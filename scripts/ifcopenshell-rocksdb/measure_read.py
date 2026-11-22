#!/usr/bin/env python3
"""Measure sampled IFC reads; validate values after the timed reads."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
import tempfile
import time
import traceback

from measure_conversion import memory, peak_rss, sha256, size

MODES = ('ifc-normal', 'ifc-lazy', 'rocksdb')
WORKLOADS = ('ids-only', 'first-attribute', 'all-attributes')


def canonical(value):
    import ifcopenshell
    if isinstance(value, ifcopenshell.entity_instance):
        if value.declaration.as_entity() is not None:
            return ['ref', value.is_a(), value.id()]
        return ['inline', value.is_a(), canonical(value[0])]
    if isinstance(value, (list, tuple)):
        return ['aggregate', [canonical(v) for v in value]]
    if value is None:
        return ['null']
    if isinstance(value, bool):
        return ['bool', value]
    if isinstance(value, int):
        return ['int', value]
    if isinstance(value, float):
        return ['float', value.hex()]
    if isinstance(value, str):
        return ['str', value]
    raise TypeError(f'Unexpected IFC value: {type(value).__name__}: {value!r}')


def entity_hash(model, entity_id, workload):
    entity = model.by_id(entity_id)
    if entity is None:
        raise ValueError(f'Missing entity #{entity_id}')
    values = [entity.id(), entity.is_a()]
    count = 0 if workload == 'ids-only' else min(len(entity), 1) if workload == 'first-attribute' else len(entity)
    for i in range(count):
        values.append(canonical(entity[i]))
    return hashlib.sha256(json.dumps(values, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def read_entity(model, entity_id, workload):
    entity = model.by_id(entity_id)
    if entity is None:
        raise ValueError(f'Missing entity #{entity_id}')
    if workload != 'ids-only':
        count = min(len(entity), 1) if workload == 'first-attribute' else len(entity)
        for i in range(count):
            entity[i]


def prepare(a):
    import ifcopenshell
    model = ifcopenshell.open(a.ifc, lazy=True)
    ids = model.entity_names()
    if not ids:
        raise ValueError('IFC contains no entities')
    sampled = random.Random(42).sample(ids, min(max(a.counts), 100000, len(ids)))
    manifest = {'entity_count': len(ids), 'ids': sampled, 'expected': {}}
    del ids
    for workload in a.workloads:
        manifest['expected'][workload] = [entity_hash(model, i, workload) for i in sampled]
    Path(a.manifest).write_text(json.dumps(manifest), encoding='utf-8')


def worker(a):
    import ifcopenshell
    manifest = json.loads(Path(a.manifest).read_text(encoding='utf-8'))
    ids, expected = manifest['ids'], manifest['expected'][a.workloads[0]]
    counts = sorted(set(min(n, len(ids)) for n in a.counts))
    snapshots = {'baseline': memory()}
    start = time.perf_counter()
    if a.mode[0] == 'rocksdb':
        model = ifcopenshell.open(a.database, readonly=True)
    else:
        model = ifcopenshell.open(a.ifc, lazy=a.mode[0] == 'ifc-lazy')
    opened = time.perf_counter()
    open_seconds = opened - start
    snapshots['after_open'] = memory()
    workload = a.workloads[0]
    stages = []
    previous, cumulative_seconds = 0, 0.0
    for count in counts:
        start = time.perf_counter()
        for index in range(previous, count):
            read_entity(model, ids[index], workload)
        elapsed = time.perf_counter() - start
        cumulative_seconds += elapsed
        name = f'after_read_{count}'
        snapshots[name] = memory()
        stages.append({'count': count, 'incremental_seconds': elapsed, 'cumulative_seconds': cumulative_seconds})
        previous = count
    start = time.perf_counter()
    for entity_id in ids[:counts[-1]]:
        read_entity(model, entity_id, workload)
    reread_seconds = time.perf_counter() - start
    snapshots['after_reread'] = memory()
    mismatches, examples = 0, []
    for index, entity_id in enumerate(ids[:counts[-1]]):
        actual = entity_hash(model, entity_id, workload)
        if actual != expected[index]:
            mismatches += 1
            if len(examples) < 10:
                examples.append({'id': entity_id, 'expected': expected[index], 'actual': actual})
    baseline = snapshots['baseline']
    previous_snapshot = baseline
    for snapshot in snapshots.values():
        for key in ('rss_bytes', 'footprint_bytes', 'compressed_or_swapped_bytes'):
            value = snapshot[key]
            snapshot[key.replace('_bytes', '_delta_baseline_bytes')] = value - baseline[key] if value is not None and baseline[key] is not None else None
            snapshot[key.replace('_bytes', '_delta_previous_bytes')] = value - previous_snapshot[key] if value is not None and previous_snapshot[key] is not None else None
        previous_snapshot = snapshot
    return {'mode': a.mode[0], 'workload': workload, 'repetition': a.repetition,
            'ifcopenshell_version': ifcopenshell.version, 'open_seconds': open_seconds,
            'stages': stages, 'reread_seconds': reread_seconds,
            'mismatched_entity_count': mismatches,
            'mismatch_examples': examples, 'valid': mismatches == 0,
            'memory': snapshots, 'peak_rss_bytes': peak_rss()}


def warm(path):
    files = [path] if path.is_file() else sorted(p for p in path.rglob('*') if p.is_file())
    for file in files:
        with file.open('rb') as f:
            while f.read(8 * 1024 * 1024):
                pass


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('ifc', type=Path)
    p.add_argument('database', type=Path)
    p.add_argument('--repeat', type=int, default=3)
    p.add_argument('--counts', nargs='+', type=int, default=[1000, 10000, 100000])
    p.add_argument('--mode', nargs='+', choices=MODES, default=list(MODES))
    p.add_argument('--workloads', nargs='+', choices=WORKLOADS, default=list(WORKLOADS))
    p.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--prepare', action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--manifest', help=argparse.SUPPRESS)
    p.add_argument('--result', help=argparse.SUPPRESS)
    p.add_argument('--repetition', type=int, help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.prepare:
        prepare(a)
        return
    if a.worker:
        try:
            data = worker(a)
        except BaseException:
            data = {'error': traceback.format_exc(), 'peak_rss_bytes': peak_rss()}
            Path(a.result).write_text(json.dumps(data), encoding='utf-8')
            raise
        Path(a.result).write_text(json.dumps(data), encoding='utf-8')
        return
    if a.repeat < 1 or any(n < 1 or n > 100000 for n in a.counts):
        p.error('repeat and counts must be positive; counts must not exceed 100000')
    if len(set(a.mode)) != len(a.mode) or len(set(a.workloads)) != len(a.workloads):
        p.error('modes and workloads must be unique')
    if not a.ifc.is_file() or not a.database.is_dir():
        p.error('IFC must be a file and database must be a directory')
    a.ifc, a.database = a.ifc.resolve(), a.database.resolve()
    data = {'ifc': str(a.ifc), 'ifc_bytes': a.ifc.stat().st_size, 'ifc_sha256': sha256(a.ifc),
            'database': str(a.database), 'database_bytes': size(a.database), 'seed': 42,
            'python_version': platform.python_version(), 'platform': platform.platform(),
            'warmup': 'sequentially read IFC and all regular database files before each worker; OS cache not controlled',
            'timing': 'by_id, len and positional attribute reads; validation runs after timed reads', 'runs': []}
    with tempfile.TemporaryDirectory(prefix='ifc-rocks-read-') as temp:
        manifest, result = Path(temp) / 'manifest.json', Path(temp) / 'result.json'
        common = [sys.executable, __file__, str(a.ifc), str(a.database), '--manifest', str(manifest), '--counts', *map(str, a.counts)]
        prep = subprocess.run(common + ['--prepare', '--workloads', *a.workloads], stdout=sys.stderr)
        data['preparation_returncode'] = prep.returncode
        if prep.returncode == 0:
            info = json.loads(manifest.read_text())
            data.update(entity_count=info['entity_count'], sample_size=len(info['ids']), actual_counts=sorted(set(min(n, len(info['ids'])) for n in a.counts)))
            del info
            for repetition in range(1, a.repeat + 1):
                shift = (repetition - 1) % len(a.mode)
                for mode in a.mode[shift:] + a.mode[:shift]:
                    for workload in a.workloads:
                        warm(a.ifc)
                        warm(a.database)
                        result.unlink(missing_ok=True)
                        cmd = common + ['--worker', '--result', str(result), '--mode', mode, '--workloads', workload, '--repetition', str(repetition)]
                        proc = subprocess.run(cmd, stdout=sys.stderr)
                        record = json.loads(result.read_text()) if result.exists() else {'error': 'worker did not write result'}
                        record.update(mode=mode, workload=workload, repetition=repetition, returncode=proc.returncode)
                        data['runs'].append(record)
    data['runtime_success'] = data['preparation_returncode'] == 0 and all(r['returncode'] == 0 for r in data['runs'])
    data['valid'] = data['runtime_success'] and bool(data['runs']) and all(r.get('valid', False) for r in data['runs'])
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if not data['runtime_success']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

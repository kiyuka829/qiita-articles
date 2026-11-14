#!/usr/bin/env python3
"""Compare RocksDB reads through the model API and Python storage API.

Attribute reads discard each returned value immediately. References are not
traversed and inline typed values are not unwrapped; this does not validate
value correctness. Timings exclude hashing, normalization, and validation.
"""
import argparse
import importlib
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
from measure_read import warm

MODES = ('model-api', 'storage')
WORKLOADS = ('ids-only', 'all-attributes')


def prepare(a):
    import ifcopenshell
    model = ifcopenshell.open(a.ifc, lazy=True)
    ids = model.entity_names()
    if not ids:
        raise ValueError('IFC contains no entities')
    sampled = random.Random(42).sample(ids, min(max(a.counts), 100000, len(ids)))
    Path(a.manifest).write_text(json.dumps({'entity_count': len(ids), 'ids': sampled}))


def worker(a):
    import ifcopenshell
    lib = importlib.import_module('ifcopenshell.file')
    manifest = json.loads(Path(a.manifest).read_text())
    ids = manifest['ids']
    if len(ids) != len(set(ids)):
        raise ValueError('Sampled IDs are not unique')
    warm(a.database)
    snapshots = {}
    def checkpoint(name):
        mem = memory()
        base = snapshots.get('baseline', {}).get('memory', mem)
        opened = snapshots.get('after_open', {}).get('memory', mem)
        for key in ('rss_bytes', 'footprint_bytes', 'compressed_or_swapped_bytes'):
            for label, ref in (('baseline', base), ('open', opened)):
                mem[key.replace('_bytes', f'_delta_{label}_bytes')] = (mem[key] - ref[key] if mem[key] is not None and ref[key] is not None else None)
        caches = {}
        for name_, fn in (('is_a', lib.rocksdb_lazy_instance.is_a), ('len', lib.rocksdb_lazy_instance.__len__), ('attribute_lookup', lib.attribute_lookup), ('entity_name_lookup', lib.entity_name_lookup)):
            caches[name_] = fn.cache_info()._asdict()
        snapshots[name] = {'memory': mem, 'caches': caches}
    checkpoint('baseline')
    start = time.perf_counter()
    model = ifcopenshell.open(a.database, readonly=True)
    open_seconds = time.perf_counter() - start
    checkpoint('after_open')
    lookup = model.by_id if a.mode[0] == 'model-api' else model.storage.by_id
    errors = {'by_id': 0, 'len': 0, 'attribute': 0}
    examples = []
    def failed(kind, entity_id, exc, index=None):
        errors[kind] += 1
        if len(examples) < 3:
            examples.append({'operation': kind, 'id': entity_id, 'index': index, 'error': str(exc)})
    def read(start_index, end_index, deadline=None):
        stats = {'entity_count': 0, 'attribute_attempts': 0, 'attribute_success': 0, 'attribute_errors': 0}
        before = errors.copy()
        start = time.perf_counter()
        for i in range(start_index, end_index):
            if deadline is not None and i % 100 == 0 and time.perf_counter() >= deadline:
                break
            entity_id = ids[i]
            stats['entity_count'] += 1
            try:
                entity = lookup(entity_id)
                if entity is None:
                    raise ValueError('Missing entity')
            except Exception as exc:
                failed('by_id', entity_id, exc)
                continue
            if a.workloads[0] == 'all-attributes':
                try:
                    length = len(entity)
                except Exception as exc:
                    failed('len', entity_id, exc)
                    continue
                for index in range(length):
                    stats['attribute_attempts'] += 1
                    try:
                        entity[index]
                        stats['attribute_success'] += 1
                    except Exception as exc:
                        failed('attribute', entity_id, exc, index)
                        stats['attribute_errors'] += 1
        stats['seconds'] = time.perf_counter() - start
        stats['errors'] = {key: errors[key] - before[key] for key in errors}
        return stats
    stages, previous, total = [], 0, 0.0
    deadline = time.perf_counter() + a.budget_seconds
    for target in sorted(set(min(n, len(ids)) for n in a.counts)):
        stage = read(previous, target, deadline)
        previous += stage['entity_count']
        total += stage['seconds']
        stage.update(target=target, completed_prefix=previous, cumulative_seconds=total)
        stages.append(stage)
        checkpoint(f'after_read_{target}')
        print(f'{a.mode[0]} {a.workloads[0]} repetition {a.repetition}: {previous}/{target}', file=sys.stderr, flush=True)
        if previous < target:
            break
    reread = read(0, previous)
    checkpoint('after_reread')
    return {'ifcopenshell_version': ifcopenshell.version, 'library_file': lib.__file__, 'library_file_sha256': sha256(Path(lib.__file__)),
            'open_seconds': open_seconds, 'stages': stages, 'reread': reread, 'errors': errors,
            'error_examples': examples, 'incomplete': previous < min(max(a.counts), len(ids)) or any(errors.values()),
            'memory_and_caches': snapshots, 'peak_rss_bytes': peak_rss()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('ifc', type=Path)
    p.add_argument('database', type=Path)
    p.add_argument('--repeat', type=int, default=3)
    p.add_argument('--counts', type=int, nargs='+', default=[1000, 10000, 100000])
    p.add_argument('--mode', choices=MODES, nargs='+', default=list(MODES))
    p.add_argument('--workloads', choices=WORKLOADS, nargs='+', default=list(WORKLOADS))
    p.add_argument('--budget-seconds', type=float, default=30)
    p.add_argument('--prepare', action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--manifest', help=argparse.SUPPRESS)
    p.add_argument('--result', help=argparse.SUPPRESS)
    p.add_argument('--repetition', type=int, help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.prepare:
        prepare(a)
        return
    if a.worker:
        try:
            result = worker(a)
        except BaseException:
            Path(a.result).write_text(json.dumps({'error': traceback.format_exc(), 'peak_rss_bytes': peak_rss()}))
            raise
        Path(a.result).write_text(json.dumps(result))
        return
    if a.repeat < 1 or any(n < 1 or n > 100000 for n in a.counts) or not 0 < a.budget_seconds < float('inf'):
        p.error('repeat and budget must be positive; counts must be between 1 and 100000')
    if len(set(a.mode)) != len(a.mode) or len(set(a.workloads)) != len(a.workloads):
        p.error('modes and workloads must be unique')
    if not a.ifc.is_file() or not a.database.is_dir():
        p.error('IFC must be a file and database must be a directory')
    a.ifc, a.database = a.ifc.resolve(), a.database.resolve()
    data = {'ifc': str(a.ifc), 'database': str(a.database), 'database_bytes': size(a.database), 'seed': 42,
            'python_version': platform.python_version(), 'platform': platform.platform(), 'no_patch': True,
            'counts': a.counts, 'repeat': a.repeat, 'budget_seconds': a.budget_seconds, 'worker_timeout_seconds': 120,
            'timing': 'by_id, len and positional attribute reads; includes counters and caught exceptions; no value validation or inline unwrapping',
            'warmup': 'each worker sequentially reads database files; OS cache is not controlled', 'runs': []}
    with tempfile.TemporaryDirectory(prefix='ifc-storage-') as tmp:
        manifest, result = Path(tmp) / 'manifest.json', Path(tmp) / 'result.json'
        common = [sys.executable, __file__, str(a.ifc), str(a.database), '--manifest', str(manifest), '--counts', *map(str, a.counts)]
        prep = subprocess.run(common + ['--prepare'], stdout=sys.stderr)
        data['preparation_returncode'] = prep.returncode
        if prep.returncode == 0:
            info = json.loads(manifest.read_text())
            data.update(entity_count=info['entity_count'], sample_size=len(info['ids']), sampled_ids_sha256=sha256(manifest))
            for repetition in range(1, a.repeat + 1):
                shift = (repetition - 1) % len(a.mode)
                for mode in a.mode[shift:] + a.mode[:shift]:
                    for workload in a.workloads:
                        result.unlink(missing_ok=True)
                        cmd = common + ['--worker', '--result', str(result), '--mode', mode, '--workloads', workload, '--repetition', str(repetition), '--budget-seconds', str(a.budget_seconds)]
                        try:
                            proc = subprocess.run(cmd, stdout=sys.stderr, timeout=120)
                            code, timed_out = proc.returncode, False
                        except subprocess.TimeoutExpired:
                            code, timed_out = None, True
                        record = json.loads(result.read_text()) if result.exists() else {'error': 'worker did not write result'}
                        record.update(mode=mode, workload=workload, repetition=repetition, returncode=code, timed_out=timed_out)
                        if code != 0:
                            record['incomplete'] = True
                        data['runs'].append(record)
    data['runtime_success'] = data['preparation_returncode'] == 0 and bool(data['runs']) and all(r['returncode'] == 0 for r in data['runs'])
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if not data['runtime_success']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

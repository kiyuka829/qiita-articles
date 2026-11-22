#!/usr/bin/env python3
"""Measure memory growth while reading sampled IFC instances in fresh processes."""
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

from measure_conversion import memory
from measure_read import read_entity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ifc', type=Path)
    parser.add_argument('database', type=Path)
    parser.add_argument('--counts', type=int, nargs='+', default=[100000, 300000, 600000, 1000000, 2000000, 3000000])
    parser.add_argument('--repeat', type=int, default=3)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--prepare', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--worker', choices=['lazy', 'rocksdb'], help=argparse.SUPPRESS)
    parser.add_argument('--manifest', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.repeat < 1 or not args.counts or min(args.counts) < 1:
        parser.error('repeat and counts must be positive')
    if not args.ifc.is_file() or not args.database.is_dir():
        parser.error('IFC must be a file and database must be a directory')

    if args.prepare:
        import ifcopenshell
        model = ifcopenshell.open(args.ifc, lazy=True)
        ids = model.entity_names()
        if not ids:
            raise ValueError('IFC contains no entities')
        sample = random.Random(args.seed).sample(ids, min(max(args.counts), len(ids)))
        args.manifest.write_text(json.dumps({'entity_count': len(ids), 'ids': sample}))
        return

    if args.worker:
        import ifcopenshell
        ids = json.loads(args.manifest.read_text())['ids']
        baseline = memory()
        model = (ifcopenshell.open(args.ifc, lazy=True) if args.worker == 'lazy'
                 else ifcopenshell.open(args.database, readonly=True))
        opened = memory()
        stages, previous = [], 0
        for count in sorted(set(min(n, len(ids)) for n in args.counts)):
            start = time.perf_counter()
            for i in range(previous, count):
                read_entity(model, ids[i], 'all-attributes')
            elapsed = time.perf_counter() - start
            snapshot = memory()
            stages.append({'count': count, 'incremental_seconds': elapsed, 'memory': snapshot,
                           'footprint_delta_open_bytes': (snapshot['footprint_bytes'] - opened['footprint_bytes']
                                                          if snapshot['footprint_bytes'] is not None else None)})
            previous = count
            print(f'{args.worker}: {count} instances', file=sys.stderr, flush=True)
        print(json.dumps({'mode': args.worker, 'ifcopenshell_version': ifcopenshell.version,
                          'baseline': baseline, 'opened': opened, 'stages': stages}))
        return

    with tempfile.TemporaryDirectory(prefix='ifc-memory-growth-') as tmp:
        manifest = Path(tmp) / 'sample.json'
        common = [sys.executable, __file__, str(args.ifc.resolve()), str(args.database.resolve()),
                  '--counts', *map(str, args.counts), '--seed', str(args.seed), '--manifest', str(manifest)]
        subprocess.run(common + ['--prepare'], check=True)
        sample = json.loads(manifest.read_text())
        count = len(sample['ids'])
        del sample
        result = {'ifc': str(args.ifc.resolve()), 'database': str(args.database.resolve()),
                  'python_version': platform.python_version(), 'platform': platform.platform(),
                  'seed': args.seed, 'sample_size': count,
                  'sample_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
                  'warmup': 'not controlled; operating system cache may be warm', 'runs': []}
        for repetition in range(1, args.repeat + 1):
            modes = ('lazy', 'rocksdb') if repetition % 2 else ('rocksdb', 'lazy')
            for mode in modes:
                proc = subprocess.run(common + ['--worker', mode], check=True, stdout=subprocess.PIPE, text=True)
                run = json.loads(proc.stdout)
                run['repetition'] = repetition
                result['runs'].append(run)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Measure streaming IFC-to-RocksDB conversion in fresh processes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import resource
import subprocess
import sys
import tempfile
import time
import traceback


def memory(pid=None):
    pid = pid or os.getpid()
    rss = int(subprocess.check_output(['ps', '-o', 'rss=', '-p', str(pid)], text=True).strip()) * 1024
    result = {'rss_bytes': rss, 'footprint_bytes': None, 'compressed_or_swapped_bytes': None}
    if sys.platform == 'darwin':
        output = subprocess.check_output(['footprint', '-f', 'bytes', '--swapped', str(pid)], text=True, stderr=subprocess.DEVNULL)
        match = re.search(r'^\s*phys_footprint:\s*(\d+) B', output, re.MULTILINE)
        total = re.search(r'^\s*(\d+) B\s+(\d+) B\s+\d+ B\s+\d+ B\s+\d+\s+TOTAL\s*$', output, re.MULTILINE)
        if not match or not total:
            raise ValueError('Could not parse footprint output')
        result['footprint_bytes'] = int(match.group(1))
        result['compressed_or_swapped_bytes'] = int(total.group(2))
    return result


def peak_rss():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == 'darwin' else value * 1024


def size(path):
    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file()) if path.is_dir() else 0


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def worker(args):
    data = {}
    try:
        import ifcopenshell
        data.update(ifcopenshell_version=ifcopenshell.version, baseline_memory=memory())
        start = time.perf_counter()
        ifcopenshell.convert_path_to_rocksdb(args.input, args.output)
        data['converter_api_seconds'] = time.perf_counter() - start
        data['after_converter_memory'] = memory()
        data['peak_rss_bytes'] = peak_rss()
    except BaseException:
        data.update(error=traceback.format_exc(), peak_rss_bytes=peak_rss())
        Path(args.result).write_text(json.dumps(data), encoding='utf-8')
        raise
    Path(args.result).write_text(json.dumps(data), encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--repeat', type=int, default=3)
    p.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--result', help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.worker:
        worker(a)
        return
    if a.repeat < 1:
        p.error('--repeat must be positive')
    if not a.input.is_file():
        p.error('input must be a file')
    if a.output.exists():
        p.error('output already exists')
    a.input, a.output = a.input.resolve(), a.output.absolute()
    result = {'input': str(a.input), 'input_bytes': a.input.stat().st_size, 'input_sha256': sha256(a.input),
              'output': str(a.output), 'python_version': platform.python_version(), 'platform': platform.platform(),
              'sampling_interval_seconds': 0.5, 'runs': []}
    with tempfile.TemporaryDirectory(prefix='ifc-rocks-convert-') as tmp:
        for repetition in range(1, a.repeat + 1):
            dest = a.output if repetition == 1 else Path(tmp) / f'db-{repetition}'
            sidecar = Path(tmp) / f'result-{repetition}.json'
            cmd = [sys.executable, __file__, str(a.input), str(dest), '--worker', '--result', str(sidecar)]
            start = time.perf_counter()
            proc = subprocess.Popen(cmd, stdout=sys.stderr)
            sampled = None
            while proc.poll() is None:
                if sys.platform == 'darwin':
                    try:
                        value = memory(proc.pid)['footprint_bytes']
                        sampled = max(sampled or 0, value)
                    except (subprocess.SubprocessError, ValueError, OSError):
                        pass
                try:
                    proc.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    pass
            elapsed = time.perf_counter() - start
            record = json.loads(sidecar.read_text()) if sidecar.exists() else {'error': 'worker did not write result'}
            record.update(repetition=repetition, returncode=proc.returncode, child_elapsed_seconds=elapsed,
                          output_bytes_after_exit=size(dest), sampled_peak_footprint_bytes=sampled)
            base = record.get('baseline_memory', {})
            observations = [v for v in (sampled, base.get('footprint_bytes'), record.get('after_converter_memory', {}).get('footprint_bytes')) if v is not None]
            observed = max(observations) if observations else None
            record['observed_peak_footprint_bytes'] = observed
            record['observed_peak_footprint_delta_baseline_bytes'] = observed - base['footprint_bytes'] if observed is not None and base.get('footprint_bytes') is not None else None
            record['peak_rss_delta_baseline_bytes'] = record['peak_rss_bytes'] - base['rss_bytes'] if record.get('peak_rss_bytes') is not None and base.get('rss_bytes') is not None else None
            result['runs'].append(record)
    result['success'] = all(r['returncode'] == 0 for r in result['runs'])
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result['success']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

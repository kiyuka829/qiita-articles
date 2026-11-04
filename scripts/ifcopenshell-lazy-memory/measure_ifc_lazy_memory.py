#!/usr/bin/env python3
"""Measure lazy-open RSS in a fresh process per IFC file; emit JSON lines.

Run with a Python environment containing IfcOpenShell 0.9.0 or later:
    python scripts/ifcopenshell-lazy-memory/measure_ifc_lazy_memory.py model.ifc [model2.ifc ...]

RSS is read using ps in KiB (macOS/Linux). On macOS, footprint also reports
physical footprint and compressed/swapped memory. Counts are collected only
after memory snapshots. The 144/12/64-byte estimate is an approximation.
"""

import argparse
import json
import mmap
import os
from pathlib import Path
import platform
import re
import resource
import subprocess
import sys


# Skip STEP strings and comments before counting reference tokens. A token
# followed by '=' declares an instance; other #number tokens are references.
TOKENS = re.compile(rb"'(?:''|[^'])*'|/\*.*?\*/|#\d+(?:\s*=)?", re.DOTALL)


def count_step_tokens(path):
    instances = references = 0
    with open(path, "rb") as file, mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as data:
        for match in TOKENS.finditer(data):
            token = match.group()
            if token.startswith(b"#"):
                if token.endswith(b"="):
                    instances += 1
                else:
                    references += 1
    return instances, references


def rss_bytes():
    rss_kib = subprocess.check_output(["ps", "-o", "rss=", "-p", str(os.getpid())], text=True)
    return int(rss_kib.strip()) * 1024


def estimate_bytes(instance_count, references, root_count, file_bytes):
    return 144 * instance_count + 12 * max(references, file_bytes // 32) + 64 * root_count


def footprint_bytes():
    output = subprocess.check_output(
        ["footprint", "-f", "bytes", "--swapped", str(os.getpid())], text=True
    )
    footprint = re.search(r"^\s*phys_footprint:\s*(\d+) B", output, re.MULTILINE)
    total = re.search(r"^\s*(\d+) B\s+(\d+) B\s+\d+ B\s+\d+ B\s+\d+\s+TOTAL\s*$", output, re.MULTILINE)
    if not footprint or not total:
        raise ValueError("Could not parse footprint output")
    return int(footprint.group(1)), int(total.group(2))


def measure(path):
    import ifcopenshell

    path = Path(path).resolve()
    before = rss_bytes()
    footprint_before = footprint_bytes() if sys.platform == "darwin" else None
    model = ifcopenshell.open(path, lazy=True)
    after = rss_bytes()
    footprint_after = footprint_bytes() if sys.platform == "darwin" else None
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024

    # These operations allocate memory, so they must follow both RSS snapshots.
    lazy_active = model.lazy_loading()
    root_count = len(model.by_type("IfcRoot"))
    instance_count = len(model.entity_names())
    source_instances, references = count_step_tokens(path)
    return {
        "file": path.name,
        "file_bytes": path.stat().st_size,
        "schema": model.schema,
        "ifcopenshell_version": ifcopenshell.version,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "lazy_active": lazy_active,
        "instance_count": instance_count,
        "source_instance_records": source_instances,
        "reference_occurrences": references,
        "ifc_root_count": root_count,
        "inverse_reserved_records": path.stat().st_size // 32,
        "estimated_bytes": estimate_bytes(instance_count, references, root_count, path.stat().st_size),
        "rss_before_bytes": before,
        "rss_after_bytes": after,
        "rss_delta_bytes": after - before,
        "peak_rss_through_open_bytes": peak,
        "footprint_before_bytes": footprint_before[0] if footprint_before else None,
        "footprint_after_bytes": footprint_after[0] if footprint_after else None,
        "compressed_or_swapped_before_bytes": footprint_before[1] if footprint_before else None,
        "compressed_or_swapped_after_bytes": footprint_after[1] if footprint_after else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="IFC STEP files to measure")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(measure(args.files[0]), ensure_ascii=False), flush=True)
    else:
        for path in args.files:
            subprocess.run([sys.executable, __file__, "--worker", path], check=True)


if __name__ == "__main__":
    main()

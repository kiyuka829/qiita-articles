#!/usr/bin/env python3
"""Measure IFC open time and memory in a fresh process; emit JSON lines."""

import argparse
import json
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time

from measure_ifc_lazy_memory import footprint_bytes, rss_bytes


def system_memory():
    if sys.platform != "darwin":
        return None
    return {
        "vm_stat": subprocess.check_output(["vm_stat"], text=True),
        "swapusage": subprocess.check_output(["sysctl", "vm.swapusage"], text=True).strip(),
    }


def measure(path, lazy):
    import ifcopenshell

    path = Path(path).resolve(strict=True)
    file_bytes = path.stat().st_size
    system_before = system_memory()
    rss_before = rss_bytes()
    footprint_before = footprint_bytes() if sys.platform == "darwin" else None

    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    model = ifcopenshell.open(path, **({} if lazy == "omit" else {"lazy": lazy == "true"}))
    cpu_seconds = time.process_time() - cpu_start
    wall_seconds = time.perf_counter() - wall_start
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024

    rss_after = rss_bytes()
    footprint_after = footprint_bytes() if sys.platform == "darwin" else None
    system_after = system_memory()
    result = {
        "file": str(path),
        "file_bytes": file_bytes,
        "ifcopenshell_version": ifcopenshell.version,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "lazy_requested": lazy,
        "lazy_active": model.lazy_loading() if hasattr(model, "lazy_loading") else None,
        "open_wall_seconds": wall_seconds,
        "open_cpu_seconds": cpu_seconds,
        "rss_before_bytes": rss_before,
        "rss_after_bytes": rss_after,
        "rss_delta_bytes": rss_after - rss_before,
        "peak_rss_through_open_bytes": peak,
        "vm_before": system_before,
        "vm_after": system_after,
    }
    for index, name in enumerate(("footprint", "compressed_or_swapped")):
        before = footprint_before[index] if footprint_before else None
        after = footprint_after[index] if footprint_after else None
        result[f"{name}_before_bytes"] = before
        result[f"{name}_after_bytes"] = after
        result[f"{name}_delta_bytes"] = after - before if before is not None else None
    return result


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def self_check():
    assert positive_int("1") == 1
    try:
        positive_int("0")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("zero repeat accepted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="IFC STEP files to measure")
    parser.add_argument("--lazy", choices=("omit", "true", "false"), default="omit")
    parser.add_argument("--repeat", type=positive_int, default=1)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if len(args.files) != 1:
            parser.error("worker requires exactly one file")
        print(json.dumps(measure(args.files[0], args.lazy), ensure_ascii=False), flush=True)
    else:
        for path in args.files:
            for _ in range(args.repeat):
                subprocess.run([sys.executable, __file__, "--worker", "--lazy", args.lazy, "--", path], check=True)


if __name__ == "__main__":
    main()

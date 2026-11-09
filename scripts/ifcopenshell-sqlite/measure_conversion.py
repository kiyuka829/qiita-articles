#!/usr/bin/env python3
"""Measure IFC-to-SQLite conversion in a fresh process per run."""

import argparse
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


def footprint(pid):
    output = subprocess.check_output(["footprint", "-f", "bytes", "--swapped", str(pid)], text=True, stderr=subprocess.DEVNULL)
    match = re.search(r"^\s*phys_footprint:\s*(\d+) B", output, re.MULTILINE)
    if not match:
        raise ValueError("Could not parse physical footprint")
    return int(match.group(1))


def peak_rss_bytes():
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss if sys.platform == "darwin" else rss * 1024


def worker(path, database, result, geometry):
    import ifcopenshell
    import ifcpatch
    from ifcpatch.recipes import Ifc2Sql

    before = footprint(os.getpid()) if sys.platform == "darwin" else None
    start = time.perf_counter()
    model = ifcopenshell.open(path, lazy=False)
    opened = time.perf_counter()
    lazy_active = model.lazy_loading()
    patcher = Ifc2Sql.Patcher(file=model, database=database, should_get_geometry=geometry)
    patcher.patch()
    end = time.perf_counter()
    data = {
        "file": str(Path(path).resolve()), "ifc_bytes": Path(path).stat().st_size,
        "geometry": geometry, "lazy_active": lazy_active, "database": database,
        "open_seconds": opened - start, "conversion_seconds": end - opened,
        "total_seconds": end - start, "database_bytes": Path(database).stat().st_size,
        "baseline_footprint_bytes": before,
        "peak_rss_bytes": peak_rss_bytes(),
        "ifcopenshell_version": ifcopenshell.version, "ifcpatch_version": ifcpatch.version,
        "python_version": platform.python_version(), "platform": platform.platform(),
    }
    Path(result).write_text(json.dumps(data), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="入力IFCファイル")
    parser.add_argument("output", type=Path, help="出力SQLiteファイル（.sqlite、.db、.ifcsqlite）")
    parser.add_argument("--no-geometry", action="store_true", help="形状データを生成しない")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--result", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args.input, str(args.output), args.result, not args.no_geometry)
        return
    if args.output.suffix.lower() not in (".sqlite", ".db", ".ifcsqlite"):
        parser.error("出力ファイルの拡張子は .sqlite、.db、.ifcsqlite のいずれかにしてください")
    if args.output.exists():
        parser.error(f"出力先が既に存在します: {args.output}")
    with tempfile.TemporaryDirectory(prefix="ifc-sql-bench-") as tmp:
        result = str(Path(tmp) / "result.json")
        command = [sys.executable, __file__, "--worker", "--result", result]
        if args.no_geometry:
            command.append("--no-geometry")
        command += ["--", str(args.input), str(args.output)]
        process = subprocess.Popen(command, stdout=sys.stderr)
        peak = None
        if sys.platform == "darwin":
            peak = 0
            while process.poll() is None:
                try:
                    peak = max(peak, footprint(process.pid))
                except subprocess.CalledProcessError:
                    if process.poll() is None:
                        raise
                time.sleep(0.5)
        else:
            process.wait()
        if process.returncode:
            print(json.dumps({"file": str(args.input.resolve()), "database": str(args.output), "geometry": not args.no_geometry, "returncode": process.returncode, "sampled_peak_footprint_bytes": peak}), flush=True)
            raise SystemExit(1)
        data = json.loads(Path(result).read_text(encoding="utf-8"))
        data["sampled_peak_footprint_bytes"] = peak
        print(json.dumps(data, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

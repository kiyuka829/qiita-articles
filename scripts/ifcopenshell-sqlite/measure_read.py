#!/usr/bin/env python3
"""Measure opening and reading the same IFC attributes in fresh processes."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import re
import resource
import sqlite3
import subprocess
import sys
import tempfile
import time

MODES = ("ifc-normal", "ifc-lazy", "sqlite-ifcopenshell", "sqlite-direct")


def quote(name):
    return '"' + name.replace('"', '""') + '"'


def connect(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)


def digest(rows):
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def sample_database(path, size, seed):
    db = connect(path)
    tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    classes = set()
    for table in tables:
        columns = {row[1] for row in db.execute(f"PRAGMA table_info({quote(table)})")}
        if {"ifc_id", "GlobalId", "Name"} <= columns:
            classes.add(table)
    rng = random.Random(seed)
    sample = []
    count = 0
    entity_count = 0
    for entity_id, cls in db.execute("SELECT ifc_id, ifc_class FROM id_map ORDER BY ifc_id"):
        entity_count += 1
        if cls not in classes:
            continue
        count += 1
        if len(sample) < size:
            sample.append((entity_id, cls))
        else:
            index = rng.randrange(count)
            if index < size:
                sample[index] = (entity_id, cls)
    sample.sort()
    rows = []
    for entity_id, cls in sample:
        row = db.execute(f"SELECT GlobalId, Name FROM {quote(cls)} WHERE ifc_id = ?", (entity_id,)).fetchone()
        if row is None:
            raise ValueError(f"Missing {cls} #{entity_id} in database")
        rows.append([entity_id, cls, *row])
    db.close()
    return rows, entity_count, count


def memory():
    rss = int(subprocess.check_output(["ps", "-o", "rss=", "-p", str(os.getpid())], text=True).strip()) * 1024
    output = subprocess.check_output(["footprint", "-f", "bytes", "--swapped", str(os.getpid())], text=True, stderr=subprocess.DEVNULL)
    match = re.search(r"^\s*phys_footprint:\s*(\d+) B", output, re.MULTILINE)
    if not match:
        raise ValueError("Could not parse physical footprint")
    return {"rss_bytes": rss, "footprint_bytes": int(match.group(1))}


def worker(args):
    if args.mode != "sqlite-direct":
        import ifcopenshell
    sample = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    expected = [[row[0], row[2], row[3]] for row in sample]
    snapshots = {"baseline": memory()}
    start = time.perf_counter()
    if args.mode == "sqlite-direct":
        model = connect(args.database)
        model.execute("SELECT preprocessor, schema, mvd FROM metadata LIMIT 1").fetchone()
    elif args.mode.startswith("ifc-"):
        model = ifcopenshell.open(args.ifc, lazy=args.mode == "ifc-lazy")
    else:
        model = ifcopenshell.open(args.database)
    opened = time.perf_counter()
    snapshots["after_open"] = memory()

    def read():
        if args.mode == "sqlite-direct":
            return [[entity_id, *model.execute(f"SELECT GlobalId, Name FROM {quote(cls)} WHERE ifc_id = ?", (entity_id,)).fetchone()] for entity_id, cls, _, _ in sample]
        rows = []
        for entity_id, _, _, _ in sample:
            entity = model.by_id(entity_id)
            rows.append([entity_id, entity.GlobalId, entity.Name])
        return rows

    start_read = time.perf_counter()
    rows = read()
    read_end = time.perf_counter()
    snapshots["after_read"] = memory()
    first_digest = digest(rows)
    del rows
    start_reread = time.perf_counter()
    rows = read()
    reread_end = time.perf_counter()
    snapshots["after_reread"] = memory()
    second_digest = digest(rows)
    valid = first_digest == second_digest == digest(expected) and rows == expected
    baseline = snapshots["baseline"]
    previous = baseline
    for name, snapshot in snapshots.items():
        for key in ("rss_bytes", "footprint_bytes"):
            snapshot[key.replace('_bytes', '_delta_baseline_bytes')] = snapshot[key] - baseline[key]
            snapshot[key.replace('_bytes', '_delta_previous_bytes')] = snapshot[key] - previous[key]
        previous = snapshot
    result = {
        "mode": args.mode, "repetition": args.repetition,
        "open_seconds": opened - start, "read_seconds": read_end - start_read,
        "reread_seconds": reread_end - start_reread, "memory": snapshots,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "ifcopenshell_version": ifcopenshell.version if args.mode != "sqlite-direct" else None,
        "lazy_requested": args.mode == "ifc-lazy" if args.mode.startswith("ifc-") else None,
        "lazy_active": model.lazy_loading() if args.mode.startswith("ifc-") else None,
        "read_digest": first_digest, "reread_digest": second_digest, "valid": valid,
    }
    print(json.dumps(result, ensure_ascii=False), flush=True)
    if not valid:
        raise SystemExit("Read values differ from the sample database")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ifc")
    parser.add_argument("database")
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", nargs="+", choices=MODES, default=list(MODES))
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--manifest", help=argparse.SUPPRESS)
    parser.add_argument("--repetition", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        args.mode = args.mode[0]
        worker(args)
        return
    if sys.platform != "darwin":
        parser.error("physical footprint measurement requires macOS")
    if args.repeat < 1 or args.sample_size < 1:
        parser.error("--repeat and --sample-size must be positive")
    if len(set(args.mode)) != len(args.mode):
        parser.error("modes must be unique")
    ifc, database = Path(args.ifc).resolve(), Path(args.database).resolve()
    sample, entity_count, root_count = sample_database(database, args.sample_size, args.seed)
    if not sample:
        parser.error("database has no entities with GlobalId and Name")
    for path in (ifc, database):
        with path.open('rb') as source:
            while source.read(8 * 1024 * 1024):
                pass
    metadata = {"ifc": str(ifc), "ifc_bytes": ifc.stat().st_size, "database": str(database),
                "database_bytes": database.stat().st_size, "entity_count": entity_count,
                "eligible_count": root_count, "sample_size": len(sample), "seed": args.seed,
                "expected_digest": digest([[r[0], r[2], r[3]] for r in sample]),
                "python_version": platform.python_version(), "platform": platform.platform(),
                "sqlite_version": sqlite3.sqlite_version, "runs": []}
    with tempfile.TemporaryDirectory(prefix="ifc-read-bench-") as temp:
        manifest = Path(temp) / "sample.json"
        manifest.write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")
        for repetition in range(1, args.repeat + 1):
            shift = (repetition - 1) % len(args.mode)
            for mode in args.mode[shift:] + args.mode[:shift]:
                command = [sys.executable, __file__, str(ifc), str(database), "--worker", "--manifest", str(manifest), "--repetition", str(repetition), "--mode", mode]
                result = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE)
                metadata["runs"].append(json.loads(result.stdout))
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

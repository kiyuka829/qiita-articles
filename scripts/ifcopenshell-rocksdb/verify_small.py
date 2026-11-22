#!/usr/bin/env python3
"""Convert in a child process, then compare IFC readers in a fresh process."""
import collections
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

import ifcopenshell
from ifcopenshell.util import selector

SOURCE = Path(os.environ.get('IFC_FIXTURE', '/Users/kiyuka/github/ifc-catalog/local/kit-ifc-examples/AC20-FZK-Haus.ifc'))


def norm(value, counts=None):
    if counts is not None:
        counts[type(value).__name__] += 1
    if isinstance(value, ifcopenshell.entity_instance):
        if SCHEMA.declaration_by_name(value.is_a()).as_entity():
            return ('ref', value.id(), value.is_a())
        return ('value', value.is_a(), norm(value.wrappedValue, counts))
    if isinstance(value, (list, tuple)):
        return [norm(v, counts) for v in value]
    return value


def ids(values):
    return sorted(x.id() for x in values)


def main(db):
    global SCHEMA
    normal = ifcopenshell.open(str(SOURCE))
    SCHEMA = ifcopenshell.ifcopenshell_wrapper.schema_by_name(normal.schema_identifier)
    lazy = ifcopenshell.open(str(SOURCE), lazy=True)
    rocks = ifcopenshell.open(db, readonly=True)
    files = {'lazy': lazy, 'rocksdb': rocks}
    errors = []
    checks = {}

    def check(name, actual, expected):
        ok = actual == expected
        checks[name] = ok
        if not ok:
            errors.append({'check': name, 'expected': repr(expected)[:350], 'actual': repr(actual)[:350]})

    base = {e.id(): e for e in normal}
    counts = collections.Counter()
    for name, f in files.items():
        entities = {e.id(): e for e in f}
        check(name + '.entity_ids', sorted(entities), sorted(base))
        mismatch_ids = []
        examples = []
        for eid in sorted(base.keys() & entities.keys()):
            expected = {k: norm(v, counts if name == 'rocksdb' else None) for k, v in base[eid].get_info().items()}
            actual = {k: norm(v) for k, v in entities[eid].get_info().items()}
            if expected != actual:
                mismatch_ids.append(eid)
                if len(examples) < 3:
                    examples.append({'id': eid, 'expected': repr(expected)[:300], 'actual': repr(actual)[:300]})
        checks[name + '.attributes_all'] = not mismatch_ids
        if mismatch_ids:
            errors.append({'check': name + '.attributes_all', 'count': len(mismatch_ids), 'ids': mismatch_ids, 'examples': examples})
        for eid in (389, 434, 436):
            check(f'{name}.by_id.{eid}', norm(f.by_id(eid)), norm(base[eid]))
            check(f'{name}.by_guid.{eid}', f.by_guid(base[eid].GlobalId).id(), eid)
            check(f'{name}.inverse.{eid}', ids(f.get_inverse(f.by_id(eid))), ids(normal.get_inverse(base[eid])))
        for typ in ('IfcProduct', 'IfcSite', 'IfcRelAggregates'):
            for subtypes in (True, False):
                check(f'{name}.by_type.{typ}.{subtypes}', ids(f.by_type(typ, include_subtypes=subtypes)), ids(normal.by_type(typ, include_subtypes=subtypes)))
        for eid, attr in ((389, 'IsDecomposedBy'), (434, 'Decomposes')):
            check(f'{name}.named_inverse.{eid}.{attr}', ids(getattr(f.by_id(eid), attr)), ids(getattr(base[eid], attr)))
        for query in ('IfcBuilding, Name="FZK-Haus"', 'IfcBuilding, Pset_BuildingCommon.BuildingID="5678"'):
            try:
                check(f'{name}.selector.{query}', ids(selector.filter_elements(f, query)), [434])
            except Exception as e:
                checks[f'{name}.selector.{query}'] = False
                errors.append({'check': f'{name}.selector.{query}', 'exception': f'{type(e).__name__}: {e}'})
    for eid, attr in ((17, 'ValueComponent'), (77, 'NominalValue'), (97, 'NominalValue')):
        check(f'rocksdb.typed_value_id.{eid}', getattr(rocks.by_id(eid), attr).id(), getattr(base[eid], attr).id())
    storage = {}
    for eid in (389, 434, 436):
        try:
            obj = rocks.storage.by_id(eid)
            storage[str(eid)] = {'python_type': type(obj).__name__, 'repr': repr(obj)[:400]}
            if eid == 389:
                check('storage.389.RefLatitude', obj.RefLatitude, base[eid].RefLatitude)
        except Exception as e:
            storage[str(eid)] = {'exception': f'{type(e).__name__}: {e}'}
    try:
        check('storage.77.NominalValue', rocks.storage.by_id(77).NominalValue[0], base[77].NominalValue.wrappedValue)
    except Exception as e:
        checks['storage.77.NominalValue'] = False
        errors.append({'check': 'storage.77.NominalValue', 'exception': f'{type(e).__name__}: {e}'})
    raw = []
    for eid in (389, 434, 436, 15067):
        for k, v in rocks.storage.prefix(f'i|{eid:016x}|').items():
            raw.append({'key': k.decode(), 'value_prefix_hex': v[:12].hex(), 'length': len(v)})
    unknown = {'source_step': next(line.strip() for line in SOURCE.read_text().splitlines() if line.startswith('#15067=')), 'normal': base[15067].IsVentilated, 'rocksdb': rocks.by_id(15067).IsVentilated, 'storage': rocks.storage.by_id(15067).IsVentilated, 'key': 'i|0000000000003adb|0000000000000002', 'value_hex': rocks.storage.read('i|0000000000003adb|0000000000000002').hex()}
    print(json.dumps({'unknown_repro': unknown, 'environment': {'python': platform.python_version(), 'platform': platform.platform(), 'ifcopenshell': ifcopenshell.version, 'fixture': str(SOURCE), 'sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest()}, 'entity_count': len(base), 'value_types': counts, 'checks': checks, 'failures': errors, 'storage_samples': storage, 'raw_first_keys': raw}, ensure_ascii=False, indent=2))
    assert not errors, f'{len(errors)} checks failed'


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'convert':
        ifcopenshell.convert_path_to_rocksdb(str(SOURCE), sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == 'check':
        main(sys.argv[2])
    else:
        with tempfile.TemporaryDirectory(prefix='ifc-rocksdb-') as tmp:
            db = os.path.join(tmp, 'db')
            subprocess.run([sys.executable, __file__, 'convert', db], check=True)
            subprocess.run([sys.executable, __file__, 'check', db], check=True)

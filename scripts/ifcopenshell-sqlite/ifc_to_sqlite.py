import argparse
from pathlib import Path

import ifcopenshell
from ifcpatch.recipes import Ifc2Sql


parser = argparse.ArgumentParser(description="IFCファイルをSQLiteに変換します。")
parser.add_argument("input", type=Path, help="入力IFCファイル")
parser.add_argument("output", type=Path, help="出力SQLiteファイル（.sqlite、.db、.ifcsqlite）")
args = parser.parse_args()

if args.output.suffix.lower() not in (".sqlite", ".db", ".ifcsqlite"):
    parser.error("出力ファイルの拡張子は .sqlite、.db、.ifcsqlite のいずれかにしてください")
if args.output.exists():
    parser.error(f"出力先が既に存在します: {args.output}")

patcher = Ifc2Sql.Patcher(file=ifcopenshell.open(args.input), database=str(args.output))
patcher.patch()
print(f"出力しました: {patcher.get_output()}")

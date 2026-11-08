# IFCからSQLiteへの変換

リポジトリのルートから、uvを使って実行します。

```sh
uv run --no-project --with 'ifcopenshell==0.9.0.post1' --with 'ifcpatch==0.9.0' \
  scripts/ifcopenshell-sqlite/ifc_to_sqlite.py /path/to/model.ifc /path/to/model.sqlite
```

# IFCからSQLiteへの変換

リポジトリのルートから、uvを使って実行します。

```sh
uv run --no-project --with 'ifcopenshell==0.9.0.post1' --with 'ifcpatch==0.9.0' \
  scripts/ifcopenshell-sqlite/ifc_to_sqlite.py /path/to/model.ifc /path/to/model.sqlite
```

## 変換の計測

macOSで、IFCファイルを通常読み込みしてSQLiteに変換し、計測結果をJSONで標準出力に出力します。2番目の引数にSQLiteの出力先を指定します。

```sh
uv run --no-project --with 'ifcopenshell==0.9.0.post1' --with 'ifcpatch==0.9.0' \
  python scripts/ifcopenshell-sqlite/measure_conversion.py \
  /path/to/model.ifc /path/to/model.sqlite > results.json
```

既定では形状を生成します。形状を生成しない場合は `--no-geometry` を指定してください。出力先がすでに存在するときは上書きせずに終了します。変換失敗時は終了コードを記録し、途中まで作成されたDBも残ります。

時間はIFCの読み込みと変換を別々に記録します。メモリはプロセス開始時から終了時までの最大RSSと、約0.5秒間隔で取得したphysical footprintの最大値です。physical footprintの最大値は標本値のため、瞬間的なピークを見逃す場合があります。`baseline_footprint_bytes` はライブラリ読み込み後、IFCを開く直前の値です。

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

## 読み込みと属性参照の計測

macOSで、同じIFCから変換したSQLiteを指定して実行します。

```sh
uv run --no-project --with 'ifcopenshell==0.9.0.post1' \
  python scripts/ifcopenshell-sqlite/measure_read.py \
  /path/to/model.ifc /path/to/model.sqlite > read-results.json
```

通常IFC、遅延IFC、IfcOpenShell経由のSQLite、直接SQLの4方式を各3回、新しいプロセスで順番を入れ替えながら計測します。`--repeat`、`--sample-size`、`--seed`、`--mode` で回数、対象数、乱数シード、対象方式を指定できます。SQLiteの `id_map` から `GlobalId` と `Name` を持つクラスを選び、固定した最大1000件の同じIDと属性値を各方式で2回読み、結果を照合します。SQLiteは指定したIFCから作成したものを使用してください。

直接SQLのオープン時間は、読み取り専用接続と `metadata` の1行取得までです。全IDの索引やIFCオブジェクトの準備を行う他の方式とは処理量が異なるため、参考値として扱います。属性参照では、同じ対象IDごとに `GlobalId` と `Name` を取得します。直接SQLの子プロセスではIfcOpenShellをインポートしません。

各プロセスはライブラリのインポート後に基準メモリを取得し、オープン、初回参照、再参照の時間と各段階後のRSS・physical footprintを記録します。差分は基準および直前の段階に対する値です。`peak_rss_bytes` はプロセス全体の最大RSSで、footprintは各段階のスナップショットです。計測前に両ファイルを順次読み、ファイルシステムキャッシュが温まった状態を目指しますが、メモリ圧迫時の常駐は保証されません。新しいプロセスでもディスクのコールドキャッシュではありません。

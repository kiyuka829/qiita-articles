# IfcOpenShell RocksDBの変換・読み込み計測

## 実行方法

リポジトリのルートからuvを使って実行します。結果はJSONで標準出力に出力します。

### IFCからRocksDBへの変換

[measure_conversion.py](measure_conversion.py) で、変換時間・DB容量・ピークメモリを計測します。

```sh
uv run --no-project --python 3.12 --with 'ifcopenshell==0.9.0.post1' \
  python scripts/ifcopenshell-rocksdb/measure_conversion.py \
  /path/to/model.ifc /path/to/model.rocksdb \
  > conversion-results.json
```

出力先のDBディレクトリが存在する場合は終了します。既定で3回、毎回別プロセスで変換し、最初のDBだけを指定先に保存します。変換には `convert_path_to_rocksdb()` を使い、通常のIFC読み込みは事前に行いません。

### 読み込みと属性参照

[measure_read.py](measure_read.py) で、通常IFC・lazy IFC・RocksDBを比較します。同じIFCから変換したDBを指定してください。

```sh
uv run --no-project --python 3.12 --with 'ifcopenshell==0.9.0.post1' \
  python scripts/ifcopenshell-rocksdb/measure_read.py \
  /path/to/model.ifc /path/to/model.rocksdb \
  > read-results.json
```

各方式で「ID取得のみ」「先頭1属性」「全属性」を別プロセスで各3回計測します。RocksDBは読み取り専用で開き、IFCを開いた場合と共通のモデルAPI（`model.by_id()` など）を使います。

全インスタンスから最大10万件を無作為抽出し（seed=42）、同じIDを1,000件・1万件・10万件と段階的に読みます。件数が少ないモデルは全件までです。最後に同じ対象をもう一度読みます。参照先の属性は再帰的にたどらず、取得結果を蓄積しません。

`--repeat` で回数、`--counts`・`--mode`・`--workloads` で読み取り条件を変更できます。実行失敗は非ゼロ終了します。値の不一致は `valid: false` として記録し、計測を継続します。

## 計測条件

Apple M5・16 GB、macOS 26.6.2、Python 3.12.13、IfcOpenShell 0.9.0.post1。
使用したIFCは [lazy読み込みの計測](../ifcopenshell-lazy-memory/README.md#使用したifcファイル) と同じ5ファイルです。

- 数値は各条件3回の中央値、メモリ・容量はMB（1 MB = 1,000,000バイト）です。
- 開く時間はimportを除いた `open()` の実時間です。`measure_read.py` の属性参照時間は値の正規化・SHA-256・照合を含みます。
- メモリはmacOSのphysical footprintを使います。基準値はimportと比較用データの読み込み後、モデルを開く前に取得します。
- 各実行前に入力IFCとDBを順次読み、OSキャッシュを温めています。コールドキャッシュの測定ではありません。

## 計測結果

### 変換時間・DB容量・ピークメモリ

変換時間は変換APIの呼び出し全体、DB容量は1回目の変換プロセス終了後の値です。観測ピーク増加量は、約0.5秒間隔の外部観測と変換前後の値の最大から基準値を引いたもので、瞬間的なピークを見逃す場合があります。

| ファイル（IFC MB） | 変換 秒 | DB MB | 観測ピーク増加 MB |
| --- | ---: | ---: | ---: |
| AC20-FZK-Haus (2.57) | 0.262 | 2.00 | 34.18 |
| kitchen (49.67) | 4.379 | 26.94 | 291.85 |
| electrical (97.06) | 8.081 | 64.31 | 463.67 |
| plumbing (222.10) | 18.653 | 129.09 | 874.63 |
| T1_UpTown_ArchiCAD (392.86) | 38.539 | 252.56 | 1,603.65 |

### 開く時間

単位は秒、括弧内は最小〜最大です。ID取得のみの条件の3回から集計し、属性参照の時間は含みません。

| ファイル | IFC 通常 | IFC lazy | RocksDB |
| --- | ---: | ---: | ---: |
| AC20-FZK-Haus | 0.024 (0.024〜0.024) | 0.009 (0.008〜0.009) | 0.002 (0.002〜0.002) |
| kitchen | 0.483 (0.479〜0.487) | 0.144 (0.144〜0.145) | 0.002 (0.002〜0.002) |
| electrical | 0.842 (0.826〜0.847) | 0.324 (0.321〜0.328) | 0.003 (0.003〜0.003) |
| plumbing | 2.006 (1.992〜2.011) | 0.701 (0.698〜0.702) | 0.003 (0.003〜0.003) |
| T1_UpTown_ArchiCAD | 3.983 (3.976〜4.128) | 1.444 (1.425〜1.484) | 0.003 (0.003〜0.003) |

### 開いた直後のメモリ増加量

モデルを開く前からのphysical footprint増加量です。単位はMB、ピーク値ではありません。上の時間と同じ実行群です。

| ファイル | IFC 通常 | IFC lazy | RocksDB |
| --- | ---: | ---: | ---: |
| AC20-FZK-Haus | 16.35 | 10.34 | 1.03 |
| kitchen | 235.70 | 143.31 | 2.36 |
| electrical | 439.78 | 234.98 | 3.98 |
| plumbing | 1,046.58 | 559.12 | 7.50 |
| T1_UpTown_ArchiCAD | 2,020.10 | 1,018.56 | 13.43 |

### 属性参照時間

選んだインスタンスの全属性を読む条件です。各セルは「初回 / 再参照」、単位は秒です。**大きい4モデルは全件ではなく10万件だけ**を読みます。

| ファイル | 参照件数 | IFC 通常 | IFC lazy | RocksDB |
| --- | ---: | ---: | ---: | ---: |
| AC20-FZK-Haus | 44,249 | 0.195 / 0.192 | 0.219 / 0.192 | 0.373 / 0.334 |
| kitchen | 100,000 | 0.443 / 0.442 | 0.879 / 0.434 | 1.020 / 0.762 |
| electrical | 100,000 | 0.534 / 0.537 | 1.015 / 0.525 | 1.468 / 1.109 |
| plumbing | 100,000 | 0.524 / 0.521 | 1.040 / 0.507 | 1.564 / 1.032 |
| T1_UpTown_ArchiCAD | 100,000 | 0.544 / 0.535 | 1.163 / 0.522 | 1.844 / 1.134 |

### 属性参照によるメモリ増加量

同じ実行内の「全属性を参照した後 − 開いた直後」を計算し、その3回の中央値を示します。単位はMB、対象件数は上の表と同じです。

| ファイル | IFC 通常 | IFC lazy | RocksDB |
| --- | ---: | ---: | ---: |
| AC20-FZK-Haus | 0.85 | 5.95 | 11.49 |
| kitchen | 0.46 | 11.16 | 115.88 |
| electrical | 1.39 | 17.45 | 205.42 |
| plumbing | 0.72 | 15.76 | 353.04 |
| T1_UpTown_ArchiCAD | 1.41 | 17.47 | 489.37 |

最大モデルでは10万件が全約540万件の約1.9%に当たります。lazyも読んだ属性を保持しており、約17.5 MB増えています。RocksDBの増加にはインスタンスの管理情報やDBのキャッシュなども含まれます。大きいモデルの全件属性参照は計測していません。

## 値の一致とメモリ指標

`measure_conversion.py` による変換15回・`measure_read.py` による読み取り135回はすべて実行に成功しました。RocksDBの全属性参照で `UNKNOWN` が `False` になる差を確認しています。AC20-FZK-Hausで4件、T1_UpTown_ArchiCADの標本で3件あり、各3回の実行で再現しました。

スクリプトはRSS、圧縮・スワップ量、段階別の結果もJSONに出力します。最大モデルの変換では圧縮・スワップが発生したため、RSSだけではなくphysical footprintで比較しています。

DB変換・取得値・保存構造の小規模検証には [verify_small.py](verify_small.py) を使います。入力の `AC20-FZK-Haus.ifc` は `IFC_FIXTURE` 環境変数で指定できます。

## storage.by_id()との比較

[measure_storage.py](measure_storage.py) で、同じRocksDBを読む `model.by_id()` と `model.storage.by_id()` を比較しました。5モデルすべてで `storage.by_id()` の方が遅く、メモリ増加量も多くなり、性能上のメリットは見られませんでした。

以下は最大モデル（T1_UpTown_ArchiCAD）の10万インスタンスから全明示属性を取得した結果で、各3回の中央値です。参照先の属性はたどらず、返り値は蓄積しません。メモリは開いた直後から初回取得後までのphysical footprint増加量です。

| 取得経路 | 初回 秒 | 再取得 秒 | メモリ増加 MB |
| --- | ---: | ---: | ---: |
| `model.by_id()` | 1.324 | 0.636 | 487.90 |
| `model.storage.by_id()` | 2.137 | 0.743 | 525.55 |

# IFCからSQLiteへの変換・読み込みの計測

## 実行方法

リポジトリのルートからuvを使って実行します。計測結果はJSONで標準出力に出力します。
physical footprintはmacOSのみで取得し、Linuxでは関連項目が `null` になります。

### 変換の計測

```sh
uv run --no-project --with 'ifcopenshell==0.9.0.post1' --with 'ifcpatch==0.9.0' \
  scripts/ifcopenshell-sqlite/measure_conversion.py \
  /path/to/model.ifc /path/to/model.sqlite > conversion-results.json
```

通常読み込み（`lazy=False`）で変換します。既定では形状を生成し、`--no-geometry` で省略できます。出力先のDBがすでにある場合は終了します。
時間はIFCの読み込みと変換を別々に記録し、メモリは最大RSSを記録します。macOSでは約0.5秒間隔で観測したphysical footprintの最大値も記録します。

計測せずに変換する場合は [ifc_to_sqlite.py](ifc_to_sqlite.py) に同じ2つのパスを渡します。

### 読み込みと属性参照の計測

```sh
uv run --no-project --with 'ifcopenshell==0.9.0.post1' \
  scripts/ifcopenshell-sqlite/measure_read.py \
  /path/to/model.ifc /path/to/model.sqlite > read-results.json
```

同じIFCから変換したSQLiteを指定します。4方式を既定で各3回、毎回別プロセスで順番を変えて計測します。同じ1,000件（seed=42）の `GlobalId` と `Name` を初回・再参照の2回読み、値を照合します。`--repeat`、`--sample-size`、`--seed`、`--mode` で条件を変更できます。

時間はimportを除いたopen・初回参照・再参照を記録します。メモリは各段階後のRSSを取得し、macOSではphysical footprintも取得します。事前に入力ファイルを読み込み、OSキャッシュが温まった状態を目指します。直接SQLはIfcOpenShellを使わず、接続と `metadata` の1行取得までをopenとするため参考値です。

## 計測結果

Apple M5・16 GB、macOS 26.6.2、Python 3.12.13、IfcOpenShell 0.9.0.post1、IfcPatch 0.9.0、SQLite 3.50.4。
使用したIFCは [lazy読み込みの計測](../ifcopenshell-lazy-memory/README.md#使用したifcファイル) と同じ5ファイルです。サイズ・メモリの単位はMB（1 MB = 1,000,000バイト）です。

### 変換

各条件の初回1回の結果です。時間は秒。最大メモリ増加量は、観測したphysical footprintの最大値からIFCを開く前の値を引いたものです。瞬間的なピークは含まれない場合があります。

| IFCファイル | IFC MB | 形状 | 読込 秒 | 変換 秒 | 合計 秒 | SQLite MB | 最大メモリ増加 MB |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| AC20-FZK-Haus | 2.57 | なし | 0.02 | 0.56 | 0.58 | 11.64 | 32.18 |
| AC20-FZK-Haus | 2.57 | あり | 0.02 | 1.27 | 1.29 | 12.55 | 276.22 |
| kitchen | 49.67 | なし | 0.49 | 10.58 | 11.07 | 105.11 | 373.31 |
| kitchen | 49.67 | あり | 0.49 | 17.82 | 18.31 | 116.01 | 917.65 |
| electrical | 97.06 | なし | 0.87 | 16.42 | 17.29 | 190.26 | 633.42 |
| electrical | 97.06 | あり | 0.88 | 25.63 | 26.51 | 236.21 | 1083.88 |
| plumbing | 222.10 | なし | 2.09 | 38.86 | 40.95 | 437.01 | 1393.53 |
| plumbing | 222.10 | あり | 2.11 | 63.19 | 65.31 | 516.28 | 2806.63 |
| T1_UpTown_ArchiCAD | 392.86 | なし | 4.02 | 73.34 | 77.36 | 812.58 | 3383.48 |

T1_UpTown_ArchiCADは形状なしのみ計測しています。

### 開く時間・メモリ使用量

形状なしのDBを使用し、各方式3回の中央値を示します。

開く時間（秒）：

| ファイル | IFC 通常 | IFC 遅延 | SQLite / IfcOpenShell | 直接SQL（参考） |
| --- | ---: | ---: | ---: | ---: |
| AC20-FZK-Haus | 0.0238 | 0.0083 | 0.0484 | 0.0020 |
| kitchen | 0.4909 | 0.1460 | 0.2978 | 0.0017 |
| electrical | 0.8713 | 0.3397 | 0.4007 | 0.0017 |
| plumbing | 2.0649 | 0.7840 | 0.9645 | 0.0017 |
| T1_UpTown_ArchiCAD | 4.0076 | 1.4057 | 1.7197 | 0.0017 |

open前後のphysical footprint増加量（MB、ピーク値ではありません）：

| ファイル | IFC 通常 | IFC 遅延 | SQLite / IfcOpenShell | 直接SQL（参考） |
| --- | ---: | ---: | ---: | ---: |
| AC20-FZK-Haus | 16.37 | 10.39 | 21.30 | 1.06 |
| kitchen | 269.17 | 172.16 | 290.80 | 0.90 |
| electrical | 474.30 | 265.52 | 363.64 | 0.92 |
| plumbing | 1,131.23 | 587.14 | 1,018.54 | 0.90 |
| T1_UpTown_ArchiCAD | 2,059.88 | 1,057.96 | 1,553.27 | 0.87 |

### 属性参照時間

各方式3回の中央値です。各セルは「初回 / 再参照」、単位はミリ秒です。

| ファイル | IFC 通常 | IFC 遅延 | SQLite / IfcOpenShell | 直接SQL（参考） |
| --- | ---: | ---: | ---: | ---: |
| AC20-FZK-Haus | 1.541 / 1.380 | 2.342 / 1.321 | 24.442 / 0.652 | 3.832 / 3.889 |
| kitchen | 1.966 / 1.686 | 4.972 / 1.549 | 35.298 / 0.691 | 4.095 / 4.164 |
| electrical | 2.405 / 1.692 | 7.126 / 1.446 | 35.974 / 0.615 | 4.669 / 4.729 |
| plumbing | 2.555 / 1.871 | 8.376 / 1.612 | 47.323 / 0.645 | 4.567 / 4.889 |
| T1_UpTown_ArchiCAD | 2.009 / 1.820 | 8.417 / 1.597 | 65.753 / 0.708 | 4.739 / 4.964 |

### 形状保存の有無によるSQLite読み込み比較

IfcOpenShell経由で開いた別の計測セットで、各条件3回の中央値です。時間は秒、メモリはopen前後のphysical footprint増加量（MB）です。メッシュ取得は含みません。

| ファイル | メッシュなし：秒 | メッシュなし：MB | メッシュあり：秒 | メッシュあり：MB |
| --- | ---: | ---: | ---: | ---: |
| AC20-FZK-Haus | 0.0485 | 21.14 | 0.0481 | 21.10 |
| kitchen | 0.2985 | 290.67 | 0.2962 | 290.90 |
| electrical | 0.3970 | 363.54 | 0.4007 | 363.66 |
| plumbing | 0.9566 | 1,018.66 | 0.9966 | 1,018.51 |

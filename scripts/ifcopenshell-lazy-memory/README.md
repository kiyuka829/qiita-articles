# IfcOpenShellの読み込み時間・メモリ計測

## 実行方法

uvを使用して、リポジトリのルートから実行します。`--with` でIfcOpenShellのバージョンを指定するため、事前のインストールは不要です。
`--no-project` は、カレントディレクトリのプロジェクト依存関係を使わないための指定です。
複数のIFCファイルを指定できます。各ファイル・各回を別プロセスで計測し、結果をJSON Lines形式で標準出力に出力します。

### 読み込み時間・メモリ使用量の比較

[measure_ifc_open.py](measure_ifc_open.py) で、`ifcopenshell.open()` の実行時間とメモリ増加量を計測します。

```sh
# IfcOpenShell 0.8.5
uv run --no-project --with 'ifcopenshell==0.8.5' \
  scripts/ifcopenshell-lazy-memory/measure_ifc_open.py \
  --repeat 3 /path/to/model.ifc

# IfcOpenShell 0.9.0（通常読み込み）
uv run --no-project --with 'ifcopenshell==0.9.0' \
  scripts/ifcopenshell-lazy-memory/measure_ifc_open.py \
  --lazy false --repeat 3 /path/to/model.ifc

# IfcOpenShell 0.9.0（lazy読み込み）
uv run --no-project --with 'ifcopenshell==0.9.0' \
  scripts/ifcopenshell-lazy-memory/measure_ifc_open.py \
  --lazy true --repeat 3 /path/to/model.ifc
```

- `--lazy`: `true` / `false` / `omit`（既定値）。`omit` は `open()` に `lazy` 引数を渡しません。
- `--repeat`: 各ファイルの計測回数（既定値: 1）。

時間はimportを除いた `open()` の実時間、メモリはimport後のopen直前と直後の差分です。属性アクセスの時間・メモリは含みません。

### lazy読み込みのメモリ概算との比較

[measure_ifc_lazy_memory.py](measure_ifc_lazy_memory.py) はIfcOpenShell 0.9.0の `lazy=True` を使用します。

```sh
uv run --no-project --with 'ifcopenshell==0.9.0' \
  scripts/ifcopenshell-lazy-memory/measure_ifc_lazy_memory.py /path/to/model.ifc
```

open前後のメモリ増加量を取得した後、インスタンス数・参照数・IfcRoot数を数え、次の概算値を出力します。

```text
概算（バイト）= 144 × インスタンス数 + 12 × max(参照数, ファイルサイズ ÷ 32) + 64 × IfcRoot数
```

ファイルサイズはバイト単位、割り算は整数除算です。

## 計測結果

計測環境: Apple M5・16 GB、macOS 26.6.2、Python 3.12.13。
メモリの単位はMB（1 MB = 1,000,000バイト）です。メモリ増加量はopen前後の差分で、ピーク値ではありません。

### 0.8.5 / 0.9.0の読み込み時間・メモリ使用量

#### 読み込み時間

単位は秒。3回の中央値、括弧内は最小〜最大です。

| ファイル（サイズ） | 0.8.5 | 0.9.0 lazy=False | 0.9.0 lazy=True |
| --- | ---: | ---: | ---: |
| AC20-FZK-Haus.ifc (2.57 MB) | 0.059 (0.059〜0.070) | 0.024 (0.024〜0.029) | 0.008 (0.008〜0.008) |
| kitchen.ifc (49.67 MB) | 1.184 (1.173〜1.206) | 0.480 (0.471〜0.913) | 0.144 (0.142〜0.145) |
| electrical.ifc (97.06 MB) | 2.673 (2.663〜2.739) | 0.842 (0.840〜0.843) | 0.328 (0.325〜0.328) |
| plumbing.ifc (222.10 MB) | 6.049 (5.782〜6.202) | 1.995 (1.960〜2.912) | 0.703 (0.702〜0.707) |
| T1_UpTown_ArchiCAD.ifc (392.86 MB) | 11.292 (11.285〜11.394) | 3.821 (3.814〜3.895) | 1.363 (1.346〜1.394) |

#### メモリ使用量

各指標の3回の中央値です。

physical footprintの増加量：

| ファイル | 0.8.5 | 0.9.0 lazy=False | 0.9.0 lazy=True |
| --- | ---: | ---: | ---: |
| AC20-FZK-Haus.ifc | 24.28 | 16.48 | 10.52 |
| kitchen.ifc | 471.12 | 269.96 | 172.28 |
| electrical.ifc | 671.63 | 475.81 | 266.27 |
| plumbing.ifc | 1,605.49 | 1,131.50 | 588.50 |
| T1_UpTown_ArchiCAD.ifc | 3,075.69 | 2,060.13 | 1,060.14 |

RSSの増加量：

| ファイル | 0.8.5 | 0.9.0 lazy=False | 0.9.0 lazy=True |
| --- | ---: | ---: | ---: |
| AC20-FZK-Haus.ifc | 25.77 | 18.45 | 12.48 |
| kitchen.ifc | 491.29 | 292.11 | 174.01 |
| electrical.ifc | 793.94 | 501.76 | 267.98 |
| plumbing.ifc | 1,548.70 | 1,161.05 | 590.04 |
| T1_UpTown_ArchiCAD.ifc | 2,517.34 | 2,128.04 | 1,061.40 |

### lazy読み込みのメモリ概算との比較

IfcOpenShell 0.9.0の `lazy=True` で、各ファイルを1回ずつ計測した結果です。

| ファイル | インスタンス数 | 参照数 | IfcRoot数 | 概算 MB | footprint増加 MB | RSS増加 MB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AC20-FZK-Haus.ifc | 44,249 | 68,264 | 1,304 | 7.42 | 10.50 | 12.48 |
| kitchen.ifc | 888,615 | 1,372,695 | 21,777 | 147.98 | 172.26 | 174.01 |
| electrical.ifc | 1,225,411 | 2,099,154 | 384,695 | 237.48 | 267.16 | 268.85 |
| plumbing.ifc | 2,965,913 | 5,019,950 | 572,677 | 547.03 | 588.46 | 590.00 |
| T1_UpTown_ArchiCAD.ifc | 5,399,942 | 8,075,801 | 1,076,305 | 993.80 | 1,060.05 | 1,061.31 |

## RSSと圧縮・スワップについて

RSSは物理メモリに常駐している量のため、圧縮・スワップされたメモリを含む使用量をRSSだけで把握することはできません。今回も大きいファイルの計測で圧縮・スワップが発生したため、macOSのphysical footprintを併記しています。

スクリプトはmacOSではRSS・physical footprint・圧縮またはスワップされた量を、LinuxではRSSを取得します。`footprint --swapped` のSwapped列は、メモリ圧縮とディスクへのスワップを区別しません。

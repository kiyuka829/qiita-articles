# IfcOpenShell 遅延読み込みのメモリ計測

`lazy=True` でIFCを開いたときのメモリ増加量を、インスタンス数などからの概算と比較するための記録です。対象ファイルごとに別プロセスで測定します。

## 再計測

IfcOpenShell 0.9.0の `lazy=True` が利用できるPython環境が必要です。macOSではRSS、physical footprint、圧縮またはスワップされた量を記録します。LinuxではRSSのみ取得します。

リポジトリのルートから、IFCファイルへのパスを指定します。複数指定すると、それぞれ別プロセスで開き、JSON Lines形式で標準出力に1行ずつ出力します。

```sh
python scripts/ifcopenshell-lazy-memory/measure_ifc_lazy_memory.py /path/to/model.ifc
```

RSSとfootprintはIfcOpenShellのimport後、openの直前・直後に取得します。件数を数える操作はその後に行います。実測値は各1回分で、プロセスやOSの状態の影響を受けます。

概算には `144 × インスタンス数 + 12 × max(参照数, ファイルサイズ ÷ 32) + 64 × IfcRoot数` を用います。ファイルサイズの割り算は整数除算、係数は仮定に基づく値です。参照数はSTEP内の文字列・コメントを除く `#ID` の出現数からインスタンス宣言数を引いて求めます。IfcOpenShell内部の逆参照索引の件数とは照合していません。

## 計測結果

Apple M5・16 GB、macOS 26.6.2、Python 3.12.13、IfcOpenShell 0.9.0で計測しました。各ファイルは別プロセスで1回ずつ開き、すべて `lazy_loading()` が `True` であることを確認しています。

| ファイル | インスタンス数 | 参照数 | IfcRoot数 | 概算 MB | footprint増加 MB | RSS増加 MB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AC20-FZK-Haus.ifc | 44,249 | 68,264 | 1,304 | 7.42 | 10.50 | 12.48 |
| kitchen.ifc | 888,615 | 1,372,695 | 21,777 | 147.98 | 172.26 | 174.01 |
| electrical.ifc | 1,225,411 | 2,099,154 | 384,695 | 237.48 | 267.16 | 268.85 |
| plumbing.ifc | 2,965,913 | 5,019,950 | 572,677 | 547.03 | 588.46 | 590.00 |
| T1_UpTown_ArchiCAD.ifc | 5,399,942 | 8,075,801 | 1,076,305 | 993.80 | 1,060.05 | 1,061.31 |

単位は10進（1 MB = 1,000,000バイト）です。各ファイルとも、open直後のプロセスの圧縮またはスワップは0 MBでした。`footprint` のSwapped列は圧縮とストレージへのスワップを区別しません。また、一時点の計測であり、open中のピークではありません。

なお、同日のUpTown単独の別計測では、open直後の圧縮またはスワップは24.10 MBでした。

## 入力データ

計測時のファイル名と入手元は次のとおりです。SHA-256は2026-11-04にローカルの入力ファイルから計算しました。サイズは10進バイトです。

| 計測時のファイル名 | 入手元 | サイズ（バイト） | SHA-256 |
| --- | --- | ---: | --- |
| `AC20-FZK-Haus.ifc` | [KIT IFC Examples](https://www.ifcwiki.org/index.php?title=KIT_IFC_Examples) | 2,570,803 | `70cc8ff245fc0894201d96496c031005a5cbd7a96b22d8a1b87c5a883fb77994` |
| `kitchen.ifc` | Sixty5設計モデルの `O-S1-BWK-BIM kitchens total - BIM keukens totaal.ifc` | 49,670,229 | `1905b992071729d1c780b18f6103e4d1d08307a4707d5f33a4413216f36776ac` |
| `electrical.ifc` | Sixty5設計モデルの `O-S1-INS-E Installatie.ifc` | 97,058,912 | `adb8d5eda2c706a1fded2a00bd38d845e35f513e2f6ba048fc6228274dfb3986` |
| `plumbing.ifc` | Sixty5設計モデルの `O-S1-INS-Plumbing - Sanitair.ifc` | 222,099,255 | `15382b06d0a63464b95ba451ce7d5fa981bf6c236ebe3f4f62bb9d2b9abfd821` |
| `T1_UpTown_ArchiCAD.ifc` | [GeoBIM Benchmark 2019 Task 1](https://zenodo.org/records/3964368) | 392,855,677 | `d96624787b62b28a7a824f9bb6611082ef9bbf15d944bccc6e0ee3850771cfca` |

Sixty5の3ファイルは [SDK - S1 の案内](https://github.com/buildingsmart-community/Community-Sample-Test-Files/tree/7ddf57a201f88a0c213d5322b02ed15e94a60a40/IFC%202.3.0.1%20%28IFC%202x3%29/SDK%20-%20S1) にある設計モデルのアーカイブから取得できます。`kitchen.ifc` などはローカルで付けた名前です。

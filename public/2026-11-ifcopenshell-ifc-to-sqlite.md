---
title: IfcOpenShellでIFCファイルをSQLiteに変換する
tags:
  - Python
  - IFC
  - IfcOpenShell
  - SQLite
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

前回は [IfcOpenShell の遅延読み込み](https://qiita.com/kiyuka/items/0d2ef739a0d34606a52f) を調べたよ！今回はIFCファイルをSQLiteに変換するぞ！

なお、この記事では IfcOpenShell 0.9.0.post1、IfcPatch 0.9.0 を使用しています。

# SQLiteへの変換方法

変換には、IfcPatchの `Ifc2Sql` というレシピを使います。Pythonから使う場合は以下のような感じです。

```py
import ifcopenshell
from ifcpatch.recipes import Ifc2Sql

model = ifcopenshell.open("model.ifc")

patcher = Ifc2Sql.Patcher(
    file=model,
    database="model.sqlite",
)
patcher.patch()

print(patcher.get_output())
```

コマンドから実行することもできます。

```sh
python -m ifcpatch -r Ifc2Sql -i /path/to/model.ifc -o /path/to/model.sqlite
```

なお、MySQLへの変換にも対応していますが、今回はSQLiteだけを扱います。

参考：[Ifc2Sqlの実装](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcpatch/ifcpatch/recipes/Ifc2Sql.py)

## 変換時のオプション

オプションで保存するデータや形式を変えられます。`Ifc2Sql.Patcher` の主なオプションは以下です。多分デフォルトから変更するとしたらメッシュがいらない場合に `should_get_geometry=False` を指定するくらいかなと思います。

| オプション | 既定値 | 内容 |
| --- | --- | --- |
| `full_schema` | `True` | IFCスキーマの全クラスのテーブルを作成する。`False` ではモデルに存在するクラスのみ |
| `is_strict` | `False` | IFCスキーマ上の必須属性に `NOT NULL` 制約を付ける |
| `should_expand` | `False` | インスタンス参照のリストを複数行に展開する |
| `should_get_inverses` | `True` | 逆参照のID一覧を `inverses` 列に保存する |
| `should_get_psets` | `True` | プロパティセットを `psets` テーブルにも保存する |
| `should_get_geometry` | `True` | メッシュを生成し、`shape`・`geometry` テーブルに保存する |
| `should_skip_geometry_data` | `False` | 元のIFCの形状表現に関するクラスの一部を保存対象から外す |

<details><summary>読まなくてもいいオプションの補足</summary>

### メッシュの保存と、元の形状表現の保存

形状に関係するオプションが2つありますが、それぞれ別の設定です。
`should_get_geometry` は、IFCからメッシュを生成して保存するかどうかです。属性だけを使いたい場合は、以下のように `False` にするとメッシュ生成を省略できます。

```py
patcher = Ifc2Sql.Patcher(
    file=model,
    database="model.sqlite",
    should_get_geometry=False,
)
patcher.patch()
```

一方、`should_skip_geometry_data` は、元のIFCにある形状表現のインスタンスをクラス別テーブルに保存するかどうかです。`True` にすると、`IfcRepresentation`・`IfcRepresentationItem` とそのサブタイプを保存対象から外します。
いまいち用途が思いつきませんが意図としては「`should_get_geometry=True`でメッシュ情報作ったら、その元となるIFCの情報なくても良いよね？」みたいなことを想定しているのかなとは思います。あんまり気にしなくて良さそうです。

### 参照リストの保存形式

`should_expand` は、インスタンス参照のリストをJSONのまま1行に保存するか、複数行に展開するかです。
たとえば、以下のように `IfcRelAggregates` の `RelatedObjects` が `#434` と `#435` を参照しているとします。

```text
#436=IFCRELAGGREGATES(..., #389, (#434, #435));
```

既定の `False` では、リストをJSONとして1行に保存します。

| ifc_id | Name | GlobalId | RelatingObject | RelatedObjects |
| --- | --- | --- | --- | --- |
| 436 | xxx | 012... | 389 | [434, 435] |

`True` では、参照先ごとに行を分けます。このとき、`Name` や `GlobalId` などの他の属性も、それぞれの行に重複して保存されます。

| ifc_id | Name | GlobalId | RelatingObject | RelatedObjects |
| --- | --- | --- | --- | --- |
| 436 | xxx | 012... | 389 | 434 |
| 436 | xxx | 012... | 389 | 435 |

参照リストだけを別テーブルに分離して正規化するのではなく、同じクラスのテーブル内で行全体を複製する形です。また、この場合は同じ `ifc_id` が複数行に現れるため、`ifc_id` が一意の主キーではなくなります。

</details>

# DBの構成と読み方

変換したDBには、IFCクラスごとのテーブルと、検索やメッシュの保存に使う補助的なテーブルが作成されます。

ここではテーブルの構成と変換したDBの読み込み方を説明していきます。

## IFCクラスごとのテーブル

IFCクラス1つにつき1テーブル、1インスタンスにつき1行という形です。IFC4であれば、IFCクラスは776種類あるので776テーブルが作られます。

たとえば `IfcWall` は以下のようなテーブルになります。これはIFC4の場合の例です。

```sql
CREATE TABLE IfcWall (
    ifc_id INTEGER PRIMARY KEY NOT NULL UNIQUE,
    GlobalId TEXT,
    OwnerHistory INTEGER,
    Name TEXT,
    Description TEXT,
    ObjectType TEXT,
    ObjectPlacement INTEGER, /* id の参照は '#123' などの文字ではなく 123 などの数値 */
    Representation INTEGER,
    Tag TEXT,
    PredefinedType TEXT,
    inverses JSON
);
```

なお、`IfcWallStandardCase` などのサブタイプのインスタンスは、それぞれのクラスのテーブルに保存されます。SQLで `IfcWall` テーブルを読む場合と、IfcOpenShellの `by_type("IfcWall")` でサブタイプも含めて取得する場合とでは取得の範囲が異なります。

## 補助的なテーブル

IFCクラスのテーブル以外にもいくつかテーブルが作られます。

| テーブル | 内容 |
| --- | --- |
| `metadata` | IFCスキーマ名（IFC4など）を含む情報（ヘッダー情報全てではない） |
| `id_map` | インスタンスIDとIFCクラス名の対応 |
| `psets` | 要素ごとのプロパティセットとプロパティを検索しやすく展開したもの |
| `shape` | 要素ごとの位置・変換行列と、対応する `geometry` のID |
| `geometry` | 頂点・辺・面・色のIDなどのメッシュデータ |

`psets` は `should_get_psets=True`、`shape`・`geometry` は `should_get_geometry=True` のときに作成されます。

### id_map テーブル

`id_map` の中身は以下のようなイメージです。IDとIFCクラスのペアのデータですね。

```text
ifc_id | ifc_class
-------|--------------------
15042  | IfcWallStandardCase
17468  | IfcDoor
19199  | IfcDoor
```

### psets テーブル

`psets` は以下の構成です。元の `IfcPropertySet` などのテーブルに加えて、検索しやすい形でも保存してくれます。

```sql
CREATE TABLE psets (
    ifc_id INTEGER NOT NULL,
    pset_name TEXT,
    name TEXT,
    value TEXT
);
```

たとえば以下のようなデータ形式で保存されます。

```md
| ifc_id | pset_name         | name                 | value           |
| ------ | ----------------- | -------------------- | --------------- |
| 15042  | AC_Pset_Name      | Name                 | Wand-Int-ERDG-4 |
| 15042  | Pset_WallCommon   | ThermalTransmittance | 1.5             |
| 17468  | Pset_DoorCommon   | ThermalTransmittance | 2.0             |
| 19199  | Pset_DoorCommon   | FireExit             | 0               |
| 19199  | Pset_DoorCommon   | ThermalTransmittance | 2.0             |
| 23024  | Pset_WindowCommon | ThermalTransmittance | 1.4             |
```

`value`は1.5などの数値でも文字列として保存されます。元の情報は以下のように `IfcPropertySingleValue` などのテーブルに保持されているので、そちらのテーブルを見ればデータ型も判別できます。
なお、`psets.ifc_id` はプロパティを持つ壁や窓などの要素のIDですが、以下の `ifc_id` はプロパティ自身のIDです。

```md
| ifc_id | Name                 | Description | NominalValue                                               | Unit | inverses  |
| ------ | -------------------- | ----------- | ---------------------------------------------------------- | ---- | --------- |
| 15086  | Name                 | NULL        | `{"type": "IfcLabel", "value": "Wand-Int-ERDG-4"}`         | NULL | `[15087]` |
| 15078  | ThermalTransmittance | NULL        | `{"type": "IfcThermalTransmittanceMeasure", "value": 1.5}` | NULL | `[15079]` |
| 17480  | ThermalTransmittance | NULL        | `{"type": "IfcThermalTransmittanceMeasure", "value": 2.0}` | NULL | `[17481]` |
| 19208  | FireExit             | NULL        | `{"type": "IfcBoolean", "value": false}`                   | NULL | `[19209]` |
| 19207  | ThermalTransmittance | NULL        | `{"type": "IfcThermalTransmittanceMeasure", "value": 2.0}` | NULL | `[19209]` |
| 23032  | ThermalTransmittance | NULL        | `{"type": "IfcThermalTransmittanceMeasure", "value": 1.4}` | NULL | `[23033]` |
```

## IfcOpenShellで開く

変換したSQLiteは、`ifcopenshell.open()` で開けます。

```py
import ifcopenshell

model = ifcopenshell.open("model.sqlite")
wall = model.by_type("IfcWall")[0]
print(wall.id(), wall.GlobalId, wall.Name)
```
<!--
拡張子は `.sqlite`・`.db`・`.ifcsqlite` が認識されます。

参考：[ファイル形式の判定（`__init__.py`）](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcopenshell-python/ifcopenshell/__init__.py#L352)
 -->
ただし、通常のIFCファイルと同じ操作がすべてできるわけではありません。`by_guid()` による取得や、`geom.create_shape()` によるメッシュ生成、IFC形式への書き出しには対応していません。
`Name` などの属性の更新はできますが、元のIFCに保存し直す使い方はできないということですね。

参考：[SQLite読み込みの実装（sql.py）](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcopenshell-python/ifcopenshell/sql.py)

## SQLで直接読む

もちろんSQLiteなので、IfcOpenShellを使わずにSQLで読むこともできます。

```py
import sqlite3

db = sqlite3.connect("model.sqlite")
try:
    for row in db.execute("SELECT ifc_id, GlobalId, Name FROM IfcWall"):
        print(row)
finally:
    db.close()
```

IfcOpenShellを使用しないため、IFCのスキーマ情報などを元に処理できませんが、その代わり必要な列だけ取り出したり、SQLで絞り込んだり集計したりできます。

# 変換と読み込みの時間とメモリ使用量

そんなわけでSQLiteに変換できたので、どれくらいの時間やメモリが必要になるのかを計測してみます。

参考：[計測スクリプト・実行環境](https://github.com/kiyuka829/qiita-articles/tree/8d93214d96b5cb369093ed701bacb34a6e8868bf/scripts/ifcopenshell-sqlite)

## SQLiteへの変換

まずは変換にかかる時間と、変換後のファイルサイズを見てみます。`should_get_geometry` だけを切り替え、それ以外は既定値で変換しています。変換では全インスタンスの属性を読むため、`lazy=False` の通常読み込みを使用しました。
変換時間は、IFCファイルの読み込みからSQLiteへの保存完了までの時間です。

| ファイルサイズ | メッシュ | 変換時間 | SQLite サイズ | メモリ |
| ---: | --- | ---: | ---: | ---: |
| 2.57 MB | なし | 0.58 秒 | 11.64 MB | 32.18 MB |
| 2.57 MB | あり | 1.29 秒 | 12.55 MB | 276.22 MB |
| 49.67 MB | なし | 11.07 秒 | 105.11 MB | 373.31 MB |
| 49.67 MB | あり | 18.31 秒 | 116.01 MB | 917.65 MB |
| 97.06 MB | なし | 17.29 秒 | 190.26 MB | 633.42 MB |
| 97.06 MB | あり | 26.51 秒 | 236.21 MB | 1083.88 MB |
| 222.10 MB | なし | 40.95 秒 | 437.01 MB | 1393.53 MB |
| 222.10 MB | あり | 65.31 秒 | 516.28 MB | 2806.63 MB |
| 392.86 MB | なし | 77.36 秒 | 812.58 MB | 3383.48 MB |

392.86 MBのIFCファイルはメッシュなしのみ計測しています。

今回のファイルでは、メッシュなしでもSQLiteのサイズは元のIFCファイルより大きくなりました。約50〜393 MBの4ファイルでは、おおよそ2倍です。
また、メッシュを保存する場合は、その生成時間とメモリも必要になります。純粋にIFCファイルをDBにしたいだけなら、メッシュ生成は省略したほうがよさそうです。

## メッシュ保存の有無による読み込み時間の違い

メッシュあり・なしのDBをIfcOpenShellで開いた場合を比較しました。各セルは「読み込み時間（秒）／メモリ増加量（MB）」です。

| ファイルサイズ | メッシュなし | メッシュあり |
| ---: | ---: | ---: |
| 2.57 MB | 0.0485 秒 / 21.14 MB | 0.0481 秒 / 21.10 MB |
| 49.67 MB | 0.2985 秒 / 290.67 MB | 0.2962 秒 / 290.90 MB |
| 97.06 MB | 0.3970 秒 / 363.54 MB | 0.4007 秒 / 363.66 MB |
| 222.10 MB | 0.9566 秒 / 1,018.66 MB | 0.9966 秒 / 1,018.51 MB |

大きな差はありません。これはファイルを開くときにメッシュの読み込みなどの処理をしていないためですね。

そういうわけなので、以降はメッシュなしで変換したDBを使って計測します。

## ファイルを開く時間とメモリ使用量

次に、元のIFCを `lazy=True` で開く場合と、変換したSQLiteをIfcOpenShellで開く場合を比較します。参考として、Pythonの `sqlite3` でSQLiteのファイルを直接開いた場合も載せています。

各セルは「読み込み時間（秒）／メモリ増加量（MB）」です。SQLite列はIfcOpenShell経由で開いた場合の結果です。

| ファイルサイズ | IFC遅延 | SQLite | 直接SQL（参考） |
| ---: | ---: | ---: | ---: |
| 2.57 MB | 0.0083 秒 / 10.39 MB | 0.0484 秒 / 21.30 MB | 0.0020 秒 / 1.06 MB |
| 49.67 MB | 0.1460 秒 / 172.16 MB | 0.2978 秒 / 290.80 MB | 0.0017 秒 / 0.90 MB |
| 97.06 MB | 0.3397 秒 / 265.52 MB | 0.4007 秒 / 363.64 MB | 0.0017 秒 / 0.92 MB |
| 222.10 MB | 0.7840 秒 / 587.14 MB | 0.9645 秒 / 1,018.54 MB | 0.0017 秒 / 0.90 MB |
| 392.86 MB | 1.4057 秒 / 1,057.96 MB | 1.7197 秒 / 1,553.27 MB | 0.0017 秒 / 0.87 MB |

DBにデータを持っているから、SQLiteの方がメモリ使用量は少ないかと思ったのですが、そんなことはありませんでした。むしろ多くなっています。開く時間も、すべてIFCの遅延読み込みの方が短くなりました。

### IfcOpenShellでSQLiteを開くとき何をしているか

IfcOpenShellでSQLiteを開くときも、検索用のデータはメモリ上に作成しています。具体的には、`id_map` テーブルを全件読み込み、Python側で以下のような辞書とリストを保持します。

```py
# インスタンスID → IFCクラス名
id_map = {
    389: "IfcSite",
    434: "IfcBuilding",
    436: "IfcRelAggregates",
}

# IFCクラス名 → インスタンスIDの一覧
class_map = {
    "IfcSite": [389],
    "IfcBuilding": [434],
    "IfcRelAggregates": [436],
}
```

さらに、クラスごとの属性やサブタイプなどのスキーマ情報も準備します。DBに全データが保存されていても、IfcOpenShellから検索・参照するための情報は別途メモリに載せるということですね。

IFCの遅延読み込みではC++側で索引を保持するのと同様に、SQLiteの場合はPythonの辞書やリストで索引を保持しています。この違いによってSQLiteの方がメモリも時間も増えてしまっているのだと思われます。

参考：[読み込み時の検索用データとスキーマ情報の準備（sql.py）](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcopenshell-python/ifcopenshell/sql.py#L129)

## 属性アクセス時間

最後に、属性を読むときの時間も確認します。

1,000件のインスタンスをIDで取得し、`GlobalId` と `Name`を読む処理を2回行うことで初回参照と再参照の時間を計測しています。各セルは「初回 / 再参照」、単位はミリ秒です。ファイルを開く時間は含みません。直接SQLの場合も同じ1,000件を対象に、IDで指定して1件ずつ `GlobalId` と `Name` を取得しています。

| ファイルサイズ | IFC 遅延 | SQLite | 直接SQL（参考） |
| ---: | ---: | ---: | ---: |
| 2.57 | 2.342 / 1.321 | 24.442 / 0.652 | 3.832 / 3.889 |
| 49.67 | 4.972 / 1.549 | 35.298 / 0.691 | 4.095 / 4.164 |
| 97.06 | 7.126 / 1.446 | 35.974 / 0.615 | 4.669 / 4.729 |
| 222.10 | 8.376 / 1.612 | 47.323 / 0.645 | 4.567 / 4.889 |
| 392.86 | 8.417 / 1.597 | 65.753 / 0.708 | 4.739 / 4.964 |

IfcOpenShell経由でSQLiteを読む場合は初回の参照に時間がかかりますが、再参照は速くなっています。これは、取得したインスタンスは `entity_cache` に、一度読んだ属性は `attribute_cache` にキャッシュしているためです。逆に言えば、使っていくうちに取得したインスタンスや属性の分だけ、メモリ上に保持する情報も増えていきます。

参考：[インスタンスのキャッシュ（sql.py）](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcopenshell-python/ifcopenshell/sql.py#L193)、[属性の取得とキャッシュ（sql.py）](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcopenshell-python/ifcopenshell/sql.py#L379)

# まとめ

そんなわけで、IfcOpenShellでIFCをSQLiteに変換して、DBの中身や読み込み時の挙動を調べてみました。

一度SQLiteに保存してしまえば、必要な情報だけDBから取ってくるから省メモリになっているのかなーとも思ったのですが、IfcOpenShell経由で読み込んだ場合は検索用のデータやキャッシュも保持するため、メモリ使用量はIFCの遅延読み込みの方が少ないという結果になりました。
読み込み時間の短縮と省メモリ化が目的なら、`lazy=True` の方がよさそうです。

ただ、SQLiteに変換すれば、IfcOpenShellを使わずにSQLで属性やプロパティを検索・集計できます。用途によっては何かうまく使える気がしますね。

# 参考資料

- [開発者による紹介：IFC stored as SQLite and MySQL](https://community.osarch.org/discussion/1535/ifc-stored-as-sqlite-and-mysql)
- [Ifc2Sqlのドキュメント](https://docs.ifcopenshell.org/autoapi/ifcpatch/recipes/Ifc2Sql/index.html)
- [ifcopenshell.sqlのドキュメント](https://docs.ifcopenshell.org/autoapi/ifcopenshell/sql/index.html)

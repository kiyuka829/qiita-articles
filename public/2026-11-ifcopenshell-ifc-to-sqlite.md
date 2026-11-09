---
title: IfcOpenShell で IFC ファイルを SQLite の形式にする（仮）
tags:
  - ''
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

開発者の
<https://community.osarch.org/discussion/1535/ifc-stored-as-sqlite-and-mysql>

レシピ側のコード
<https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcpatch/ifcpatch/recipes/Ifc2Sql.py>

IfcOpenShell側
<https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcopenshell-python/ifcopenshell/sql.py>

ドキュメント（中身はない）
<https://docs.ifcopenshell.org/autoapi/ifcpatch/recipes/Ifc2Sql/index.html>
<https://docs.ifcopenshell.org/autoapi/ifcopenshell/sql/index.html>

読み込み対応拡張子
<https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcopenshell-python/ifcopenshell/__init__.py#L352>

# 使い方

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

コマンド実行

```sh
python -m ifcpatch -r Ifc2Sql -i /path/to/model.ifc -o /path/to/model.sqlite

uv run --no-project \
  --with 'ifcopenshell==0.9.0.post1' \
  --with 'ifcpatch==0.9.0' \
  python -m ifcpatch \
  -i /path/to/model.ifc \
  -o /path/to/model.sqlite \
  -r Ifc2Sql
```

```py
class Patcher(ifcpatch.BasePatcher):
    def __init__(
        self,
        file: ifcopenshell.file,
        logger: Union[logging.Logger, None] = None,
        sql_type: SQLTypes = "SQLite",
        host: str = "localhost",
        username: str = "root",
        password: str = "pass",
        database: str = DEFAULT_DATABASE_NAME,
        full_schema: bool = True,
        is_strict: bool = False,
        should_expand: bool = False,
        should_get_inverses: bool = True,
        should_get_psets: bool = True,
        should_get_geometry: bool = True,
        should_skip_geometry_data: bool = False,
    ):
```

## オプション

この3つは、SQLiteに**どんな制約・形式・範囲でデータを保存するか**の設定です。今作成したAC20-FZK-Haus.sqliteでは、いずれも既定値の `False` になっています。

## `is_strict`

**IFCスキーマ上の必須属性に、SQLの `NOT NULL` 制約を付けるか**です。

```python
is_strict=False  # 既定値：属性の列にNOT NULL制約を付けない
is_strict=True   # IFCで必須の属性にNOT NULL制約を付ける
```

たとえば `GlobalId` が必須のクラスでは、イメージとして次の違いがあります。

```sql
-- False
GlobalId TEXT

-- True
GlobalId TEXT NOT NULL
```

## `should_expand`

**エンティティ参照のリストを、JSONのまま1行に保存するか、複数行に展開するか**です。

たとえば、`IfcRelAggregates` の `RelatedObjects` が `#434` と `#435` を参照しているとします。

```text
#436=IFCRELAGGREGATES(..., #389, (#434, #435));
```

既定の `False` では、リストをJSONとして1行に保存します。

```text
ifc_id | RelatingObject | RelatedObjects
-------|----------------|---------------
436    | 389            | [434, 435]
```

`True` では、参照先ごとに行を分けます。

```text
ifc_id | RelatingObject | RelatedObjects
-------|----------------|---------------
436    | 389            | 434
436    | 389            | 435
```

## `should_skip_geometry_data`

**元のIFCにある形状表現のエンティティの一部を、クラス別テーブルに保存せず省略するか**です。

```python
should_skip_geometry_data=False  # 既定値：省略しない
should_skip_geometry_data=True   # 対象の形状表現を省略する
```

`True` の場合、`IfcRepresentation` と `IfcRepresentationItem` について、テーブルの作成とデータの保存を飛ばします。

# DB

| テーブル | 内容 |
| --- | --- |
| `metadata` | DB形式の識別子、IFCスキーマ、MVD |
| `id_map` | インスタンスIDとIFCクラス名の対応 |
| `psets` | エンティティごとのプロパティセットとプロパティを検索しやすく展開したもの |
| `shape` | エンティティごとの位置・変換行列と、対応する `geometry` のID |
| `geometry` | 頂点・辺・面・スタイルなどの形状データ |

```sql
CREATE TABLE id_map (ifc_id integer PRIMARY KEY NOT NULL UNIQUE, ifc_class text);

CREATE TABLE geometry (
            id text NOT NULL,
            verts blob,
            edges blob,
            faces blob,
            material_ids blob,
            materials json
        );

CREATE TABLE shape (
            ifc_id integer NOT NULL,
            x real,
            y real,
            z real,
            matrix blob,
            geometry text
        );

CREATE TABLE psets (
            ifc_id integer NOT NULL,
            pset_name text,
            name text,
            value text
        );

CREATE TABLE metadata (preprocessor text, schema text, mvd text);

CREATE TABLE IfcWall (ifc_id INTEGER PRIMARY KEY NOT NULL UNIQUE, `GlobalId` TEXT, `OwnerHistory` INTEGER, `Name` TEXT, `Description` TEXT, `ObjectType` TEXT, `ObjectPlacement` INTEGER, `Representation` INTEGER, `Tag` TEXT, `PredefinedType` TEXT, inverses JSON);

```

# 計測

## 保存

すべてのインスタンスを読むので遅延読込みする意味はないのとメッシュ作成は `lazy=True` 未対応なので通常読み込み。

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

## 開く

## メッシュ有り無し比較

メッシュ有り無しのSQLiteをIfcOpenShellで開いたとき。同じ。

| ファイル | メッシュなし：秒 | メッシュなし：MB | メッシュあり：秒 | メッシュあり：MB |
| --- | ---: | ---: | ---: | ---: |
| AC20-FZK-Haus | 0.0485 | 21.14 | 0.0481 | 21.10 |
| kitchen | 0.2985 | 290.67 | 0.2962 | 290.90 |
| electrical | 0.3970 | 363.54 | 0.4007 | 363.66 |
| plumbing | 0.9566 | 1,018.66 | 0.9966 | 1,018.51 |

## lazy と SQLite の読み込み比較

lazy と SQLite の比較。速度は変わらない。
DBにデータを持つからSQLiteの方がメモリは少ないかと思ったがそんなこともなく、むしろ多い。
検索用のデータをPythonで保持しているせい。

| ファイル | IFC遅延：秒 | IFC遅延：MB | SQLite：秒 | SQLite：MB | SQLite単独（参考）：秒 | SQLite単独（参考）：MB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AC20-FZK-Haus | 0.0083 | 10.39 | 0.0484 | 21.30 | 0.0020 | 1.06 |
| kitchen | 0.1460 | 172.16 | 0.2978 | 290.80 | 0.0017 | 0.90 |
| electrical | 0.3397 | 265.52 | 0.4007 | 363.64 | 0.0017 | 0.92 |
| plumbing | 0.7840 | 587.14 | 0.9645 | 1,018.54 | 0.0017 | 0.90 |
| T1_UpTown_ArchiCAD | 1.4057 | 1,057.96 | 1.7197 | 1,553.27 | 0.0017 | 0.87 |

id_map、class_map をPython側でデータ保持している。
<https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcopenshell-python/ifcopenshell/sql.py#L129>
C++側の索引データ（byid_）の方にはデータを保持せずPython側で持つ形。その分メモリ使用量が増えている。

by_guid() はできない。
geom.create_shape() でのジオメトリ作成処理はできない。
Nameなどの属性の更新はできるが、IFCに保存し直すことはできない。

属性を読むときにキャッシュする。attribute_cache
<https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcopenshell-python/ifcopenshell/sql.py#L379>
インスタンスを取得してもキャッシュする。entity_cache
<https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcopenshell-python/ifcopenshell/sql.py#L200>

## 属性アクセス時間

1,000要素へのアクセスにかかった合計時間。各セルは「初回 / 再参照」、単位はミリ秒です。

| ファイル | IFC 遅延 | SQLite / IfcOpenShell | 直接SQL（参考） |
| --- | ---: | ---: | ---: |
| AC20-FZK-Haus | 2.342 / 1.321 | 24.442 / 0.652 | 3.832 / 3.889 |
| kitchen | 4.972 / 1.549 | 35.298 / 0.691 | 4.095 / 4.164 |
| electrical | 7.126 / 1.446 | 35.974 / 0.615 | 4.669 / 4.729 |
| plumbing | 8.376 / 1.612 | 47.323 / 0.645 | 4.567 / 4.889 |
| T1_UpTown_ArchiCAD | 8.417 / 1.597 | 65.753 / 0.708 | 4.739 / 4.964 |

SQLiteをIfcOpenShellで読んで属性を参照すると、参照のインスタンスもオブジェクトを作成する
<https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcopenshell-python/ifcopenshell/sql.py#L379>

# まとめ

一度SQLiteに保存してしまえばDBアクセスになるのでメモリ使用量の問題は起きないよね、というような。

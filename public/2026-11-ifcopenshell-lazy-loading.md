---
title: IfcOpenShell の 遅延読み込み （仮）
tags:
  - Python
  - IFC
  - IfcOpenShell
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

IfcOpenShell 0.9.0 で 遅延読み込みが実装されたので解説するよ！

# 使い方

使い方は、`open()` に `lazy=True` を渡すだけ。

```py
import ifcopenshell

# この時点ではまだ完全に読み込まずに、まずは検索に必要な情報だけを作成している
model = ifcopenshell.open("model.ifc", lazy=True)
wall = model.by_type("IfcWall")[0]

# 属性にアクセスするときに、対象の属性情報を解析する
name = wall.Name
```

# ゆるく理解するための解説

雰囲気だけ理解しようのコーナー。多分普通に使う分であればこれを読むだけで十分だよ！

でもざっくり解説だから、細かな説明は省略してるよ！

## 遅延処理って何？

遅延処理のイメージ的には、

> お母さん「夏休みの宿題やったのー！」
> 子ども「やったやった（やってない）だから遊びに行くねー」
> 子ども（提出は最初の授業のときだから、まだやんなくて大丈夫でしょ！）
>
> 夏休みが終わって授業前日
>
> 子ども「やっべ、明日提出だ。やらないと...いや、まだ行ける。授業始まる直前までに終わらせれば問題ないぜ！」

だいたいこんな感じです（？）とても効率的ですね（？？）

## ざっくり lazy 処理解説

`lazy=True` では、ファイルを開いた時点では `(...)` 内の属性情報を完全には解析しません。

イメージ的には以下のようなデータだと解釈するだけにとどめるような形です。

```ifc
#123=IFCWALL(...); // `#123=IFCWALL` の部分だけを読んで `(...)` 内は最小限しか読まない
#124=IFCSLAB(...);
```

実際に `Name` などの属性にアクセスするときになって初めて `(...)` 内の解析をします。こうすることで、ファイルを開くときに行う処理を減らせるし、使わないデータは解析せずに済みます。
必要になるまで処理を後回しにする、ということができるわけですね。

# 内部の処理

ここから真面目に解説する。図とかいっぱい入れたい。

## 読み込み時に保持するデータ

`lazy=True` では、ファイルを先頭から順に読み込み、検索などに必要なデータのみを保持する形を取ります。

ここでは、[AC20-FZK-Haus.ifc](https://www.ifcwiki.org/index.php?title=KIT_IFC_Examples) から以下の3件を抜粋して、どのようなデータが作られるかを説明します。

```text
#389= IFCSITE('0KMpiAlnb52RgQuM1CwVfd',#12,'Gelaende','Ebenes Gelaende','LandUse',#115,#383,$,.ELEMENT.,(49,6,1,566000),(8,26,11,540400),110.,$,$);
#434= IFCBUILDING('2hQBAVPOr5VxhS3Jl0O47h',#12,'FZK-Haus','FZK-Haus create by KHH / IAI / FZK','Wohnhaus',#432,$,$,.ELEMENT.,$,$,$);
#436= IFCRELAGGREGATES('0FWMHXglS7fAS5ox0icROM',#12,$,$,#389,(#434));
```

なお、以下はイメージを掴むためのPythonでの疑似的なデータ構造であり、実際のC＋＋でのデータではありません。

### インスタンスの内部オブジェクト

各インスタンスのIDと型を読み取り、対応する内部オブジェクトを作成します。属性値は、この時点では空です。

```py
inst389 = InstanceData(id=389, type="IfcSite", storage=None)
inst434 = InstanceData(id=434, type="IfcBuilding", storage=None)
inst436 = InstanceData(id=436, type="IfcRelAggregates", storage=None)
```

### 検索用のデータ

ID, Type, GlobalId でインスタンスを検索できるようにするための索引データも初期読込み時に作成して保持します。「`(...)` 内の属性情報を完全には解析しない」と記載していましたが、実際はGlobalIdと逆参照の索引データを作成するために、それらの情報だけ解析しています。

以下は保持されるデータのイメージ。

```py
# ID → インスタンス
by_id = {
    389: inst389,
    434: inst434,
    436: inst436,
}

# GlobalId → インスタンス
by_guid = {
    "0KMpiAlnb52RgQuM1CwVfd": inst389,
    "2hQBAVPOr5VxhS3Jl0O47h": inst434,
    "0FWMHXglS7fAS5ox0icROM": inst436,
}

# 型 → インスタンスの一覧
by_type = {
    "IfcSite": [inst389],
    "IfcBuilding": [inst434],
    "IfcRelAggregates": [inst436],
}

# 逆参照のソート済みのレコード一覧（二分探索で検索される）
# (参照先ID, 参照元ID, 参照元の型, 属性位置)
by_ref = [
    (12,  389, "IfcSite",          1),
    (12,  434, "IfcBuilding",      1),
    (12,  436, "IfcRelAggregates", 1),
    (115, 389, "IfcSite",          5),
    (383, 389, "IfcSite",          6),
    (389, 436, "IfcRelAggregates", 4),
    (432, 434, "IfcBuilding",      5),
    (434, 436, "IfcRelAggregates", 5),
]
```

### 属性を読むための位置情報

`(...)` 内の属性情報は初期読込み時にメモリ内部で保持していません。そのため、属性情報を読むためにファイル上のどの位置に各インスタンスの情報があるのかを保持します。位置は、型名の直後にある `(` の次のバイトです。

```py
# ID → ファイル内の属性開始位置（ファイル先頭からのバイト数）
lazy_offsets = {
    389: 10899,
    434: 11931,
    436: 12070,
}

"""
#436= IFCRELAGGREGATES('0FWMHXglS7fAS5ox0icROM',#12,$,$,#389,(#434));
                       ↑ ここがファイルの 12070 byte の位置
"""
```

たとえば `model.by_id(436).GlobalId` とアクセスすると、IFCファイルの 12070 byte の位置を読みに行って `(...)` 内の属性を解析するわけですね。

このように `lazy_offsets` によって、必要なときにファイルの指定の位置から属性を読み取りに行くことができます。

<!--
- [索引などのデータ構造（storage.h）](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/storage.h)
- [属性が空の内部オブジェクトの作成（instance_data.h）](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/instance_data.h#L539-L568)
- [初期走査と索引の構築（parse.cpp）](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/parse.cpp#L2776-L2886)
- [id, type, guid](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcparse/storage.h#L666)
- [ref](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcparse/storage.h#L150)
 -->

# メモ

以下、メモ書き。記事書き終わるまで残しておく。

---

IfcOpenShell 0.9.0 で 遅延読み込みが実装されたので内部処理を理解する。

ひとまずCodex

---

````md
はい、**`lazy=True` の場合は、おおむねその理解で合っています。** 正確には、入力も一部分ずつメモリに読み込みます。また、保持するものには索引以外もあります。

文書で参照している版では、次の流れです。

1. **64 KiBずつメモリに読み込む**
   ファイルI/Oはページ単位です。そのメモリ上のバイト列を解析します。入力ページは最大64ページ、計4 MiBをキャッシュし、古いページを入れ替えます。[入力の読み込み実装](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/file_reader.cpp)

2. **ファイル全体を走査して、検索に必要な情報を保持する**
   ID・型・属性のファイル位置・GlobalId・逆参照の索引に加え、各インスタンスの軽い内部オブジェクトも作ります。この時点では、通常の属性値をすべて数値や文字列へ変換して保持する処理は省いています。

3. **属性を要求されたら、その場所を読み直して解析する**
   入力ページがキャッシュにあれば使い、なければファイルから取得します。対象インスタンスの属性一式を解析し、その結果をメモリに保持して再利用します。[索引構築・遅延解析の実装](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/parse.cpp)

したがって、保持量のイメージはこうです。

```text
open直後：
  入力の一部分 ＋ 各種索引 ＋ 全件の軽い内部オブジェクト

属性を利用した後：
  上記 ＋ アクセスしたインスタンスの解析済み属性
```

**元ファイル全体のバイト列を保持する必要はありませんが、属性を読む対象が増えるほど、解析済みデータの保持量は増えます。**

````

---

インスタンスごとにオブジェクトを作ってそこにデータを格納していく形らしい。
パースした場合はそこにキャッシュしていくようにな仕組み。

パースしていない場合は指定のIDのデータの取得は lazy_offsets_ から2分探索でファイルのバイト位置を探してそこから読み込んでパースするような形。

````md
はい。**通常のlazy読み込みでは、ファイル内の各 `#123=…;` に対して、C++の内部オブジェクト `instance_data` を初期走査で作ります。** 属性値の解析は後回しですが、オブジェクト自体は作成します。

そのオブジェクトが持つメンバーは次のとおりです。

| メンバー | 内容 | 初期走査直後 |
|---|---|---|
| `file_` | 所属するモデルへのポインタ | 読み込んでいるモデルを指す |
| `declaration_` | スキーマの型定義へのポインタ | `IfcWall` などの型定義を指す |
| `identity_` | 内部管理用の識別番号 | 作成時にカウンタから採番。STEPのIDとは別 |
| `id_` | STEPのインスタンスID | `#123` なら `123` |
| `storage_` | 解析済み属性の格納領域 | 空。属性を要求されたときに設定 |

型定義そのものは共有され、インスタンスごとに複製されません。[`instance_data` の定義とlazy用コンストラクタ](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/instance_data.h)

**ファイルのバイト位置は、このオブジェクトには入っていません。** モデル側が持つ別の配列 `lazy_offsets_` に、`(ID, 属性開始位置)` の組として保存されています。

```text
モデル
 ├─ ID索引
 │    123 → instance_data
 │            ├─ file_ → このモデル
 │            ├─ declaration_ → IfcWallの型定義
 │            ├─ identity_ = 内部管理用の番号
 │            ├─ id_ = 123
 │            └─ storage_ = 空
 │
 └─ 位置索引 lazy_offsets_
      [(123, 1000), (124, 1150), ...]
              ↑
       ファイル先頭からのバイト位置（例）
```

属性を読むときは、オブジェクトの `file_` と `id_` を使ってモデル側の位置索引を引き、該当位置から解析して、そのオブジェクトの `storage_` に結果を格納します。[属性を読み込む処理](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/parse.cpp)
````

バイト位置は属性の開始位置

```md
#123=IFCWALL('guid',#5,'壁A',$,...);
            ↑
            lazy_offsets_ に記録する位置

lazy_offsets_：[(123, この位置), ...]
```

初期読み込みのときに、 #123, IFCWALL, GlobalId, 属性内の#5などの参照（逆参照用） はパースしている。
数値とかリストとかのパースはしないけどそれ以外はするような形。

以下を保持する。 lazy_offsets_ 以外は lazy 前からあるデータの保持情報。

| 索引 | 実装名 | 対応関係 |
| --- | --- | --- |
| ID | `byid_` | ID → 内部オブジェクト |
| 型 | `bytype_excl_` | 型 → 内部オブジェクトの一覧 |
| GlobalId | `byguid_` | GlobalId → 内部オブジェクト |
| 属性開始位置 | `lazy_offsets_` | ID → ファイル内の属性リスト開始位置 |
| 逆参照 | `byref_excl_` | 参照先ID → 参照元ID・型・属性番号 |

属性一つをアクセスすると、そのインスタンスすべての属性場パースされてキャッシュされる。

## メモリ

````md
はい、**属性が未解析でも、全インスタンスの内部オブジェクトと索引だけで相当なメモリになり得ます。** 概算すると、確認中のソースでは、**オブジェクト本体は約40バイト、主要な索引などを含めると1件あたり約144バイトになる構成例**が考えられます。

以下は64 bit環境を仮定した計算です。配布版での実測値やRSSではありません。

まず、`instance_data` 本体です。

| メンバー | 仮定するサイズ |
| --- | ---: |
| 所属モデルへのポインタ `file_` | 8バイト |
| 型定義へのポインタ `declaration_` | 8バイト |
| 内部識別番号 `identity_` | 4バイト |
| STEPのID `id_` | 4バイト |
| 属性格納領域 `storage_` | 16バイト |
| **合計** | **40バイト** |

`storage_` は、属性データへのポインタを持つ構造を `std::optional` で包んでいます。ここではポインタ8バイト＋有無の状態とパディングで16バイトと仮定しています。**空でもこの領域はオブジェクト内にありますが、属性配列自体はまだ確保しません。** [`instance_data` の定義](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/instance_data.h)、[属性格納構造の定義](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/variant_array.h)

さらに、オブジェクトを管理・検索するための領域が必要です。共有・弱参照ポインタを使う `IFOPSH_SAFE_INSTANCE` が有効な構成について、次のように仮定します。

| 1インスタンスあたりに割り当てる項目 | 計算例 |
| --- | ---: |
| 内部オブジェクト本体 | 40バイト |
| 共有ポインタの参照数などを管理する領域（固定費的なもの） | 24バイト |
| IDハッシュ表のノードとバケットの按分（IDのインデックス） | 48バイト（次ノードポインタ8 + hash値8 + ID4 + shared_ptr16） |
| 型別一覧に入る弱参照ポインタ（型のインデックス） | 16バイト （8＋8）|
| `lazy_offsets_` の `(ID, 位置)`。パディング込み | 16バイト （4＋8＋α）|
| **小計** | **144バイト／件** |

管理領域24バイト、ハッシュ表48バイトなどは、標準ライブラリの構成を仮定した値です。配列の余剰容量やメモリアロケータの丸めも、この小計には含めていません。[ポインタの構成](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/express.h)、[索引の定義](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/storage.h)

この仮定だけでも、件数を掛けると次の規模です。単位は10進です。

| インスタンス数 | 本体40バイトだけ | 上記の小計144バイト |
| --- | ---: | ---: |
| 100万件 | 40 MB | 144 MB |
| 1,000万件 | 400 MB | 1.44 GB |
| 2,000万件 | 800 MB | 2.88 GB |

**ここにGlobalId索引・逆参照索引・解析済み属性などが追加されます。**

特に逆参照は、インスタンス数ではなく参照の出現数に応じて増えます。レコードのフィールド幅の合計は1参照あたり12バイトです。また、確認ソースでは初期に「入力バイト数÷32」件分を予約するため、実際の確保容量は参照件数だけでは決まりません。[逆参照の構造](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/storage.h)、[初期容量の予約](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/parse.cpp)

なので、懸念には根拠があります。**入力ページが4 MiBに収まっても、インスタンス数が多ければオブジェクトと索引がGB単位になる構造です。** ただし、「通常openとの互換性のため、この構造にするしかなかった」という設計意図までは確認できていません。
````

はい。**144バイトには、本体・参照管理・ID索引・型索引・位置索引を含めています。** 逆参照・GlobalId索引は別です。

その2つの件数も、先ほどの実ファイルで数えました。追加分は、前と同じ64 bit環境の仮定で次のように概算できます。

| 追加項目 | 概算 |
| --- | ---: |
| 逆参照 | **1参照あたり12バイト**：参照先ID 4＋参照元ID 4＋型番号2＋属性番号2 |
| GlobalId索引 | **1件あたり約64バイト**：GUID・オブジェクト参照・ハッシュ表管理領域など |

GlobalIdの64バイトにはハッシュ表の仮定を含みます。これで全体の概算は、

```text
144 × インスタンス数
＋ 12 × 参照の出現数
＋ 64 × GlobalId索引の件数
```

となります。[保持構造の定義](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/storage.h)

---

インデックスとしては byid_、bytype_excl_、byref_excl_、byguid_ の4つを持つ。
ID、Type、逆参照、GUID。

## 編集保存処理

属性の編集自体は、 storage_ に保持したデータの書き換えになる（参照など編集したら各種インデックスなども当然編集される）。
ただ、保存時はパースしていないインスタンスもずべてパースして storage に保持してから保存する。
そのため読み込みは少なくても保存はメモリ消費が多くなる。

````md
保存処理
  → 各インスタンスの属性値を取得する
    → 未解析なら、通常の属性アクセスと同じ遅延解析が動く
      → 解析結果が storage_ に保持される
  → 属性値をSTEPテキストとして出力する
````

## ページキャッシュ

そうです。**ファイルを一定サイズに区切り、その一部分を元のバイト列のままメモリに置くキャッシュ**です。

保持しているデータ自体はシンプルで、1ページが次の構造です。

```cpp
struct file_reader_page {
    std::vector<char> data;
};
```

この `data` に、ファイルから読み込んだ `#123=IFCWALL(...);` などの生のバイト列が入ります。解析済みの属性やインスタンスのオブジェクトではありません。[ページの定義](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/file_reader.h#L60-L62)

ページの区切りは、インスタンスの区切りとは関係なく、ファイル先頭から一定間隔です。確認中のlazy実装では1ページ64 KiBなので、こうなります。

| ページ番号 | ファイル内のバイト位置 |
| --- | --- |
| 0 | 0〜65,535 |
| 1 | 65,536〜131,071 |
| 2 | 131,072〜196,607 |

一つのインスタンスがページをまたぐ場合もあります。

ページ全体の管理には、**ページ番号からデータを探すハッシュ表**と、**使った順番を管理するリスト**を組み合わせています。

```text
map_：ページ番号 → ページデータ ＋ リスト上の位置
  2 → 生のバイト列 [...]
  7 → 生のバイト列 [...]
  3 → 生のバイト列 [...]

lru_：ページの利用順
  最近使った側 → [3, 7, 2] → 長く使っていない側
```

実際の型は `std::unordered_map<size_t, entry>` と `std::list<size_t>` です。各エントリにはリスト上の位置も持たせているので、利用順の更新時にリストを探し回る必要がありません。[管理構造の定義](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/file_reader.h#L328-L369)

例えばファイルの100,000バイト目を読む場合は、

1. `100000 ÷ 65536` でページ番号 **1** を求める。
2. キャッシュにページ1があれば、それを使う。
3. なければ、ファイルの65,536バイト目から1ページ分を読み込む。
4. ページ内の `100000 % 65536 = 34464` 番目のバイトを返す。

という処理になります。キャッシュが上限に達していれば、長く使っていないページを外して入れ替えます。[バイトの取得](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/file_reader.cpp#L112-L122)、[ページの読み込み・入れ替え](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/file_reader.cpp#L166-L211)

lazy読み込みではこれを64ページ保持する設定なので、ページのデータ部分は最大4 MiBです。ここから読んだ内容を解析して `storage_` に格納する処理は、また別にあります。[lazy用の設定](https://github.com/IfcOpenShell/IfcOpenShell/blob/a298d3489419a06636c5f4b423b2fc9c1ceb7c65/src/ifcparse/parse.cpp#L2728-L2733)

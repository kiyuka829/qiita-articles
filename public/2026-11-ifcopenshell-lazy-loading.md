---
title: IfcOpenShell の遅延読み込み
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

IfcOpenShell 0.9.0 で遅延読み込みが実装されたので解説するよ！

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

ここからは、遅延読み込みがどういう処理をしているかのアルゴリズムとかデータ構造とかの話をするよ！一見さんお断りだよ！読んだらだめだよ！(ΦωΦ)

## 読み込み時に保持するデータ

`lazy=True` では、ファイルを先頭から順に読み込み、検索などに必要なデータのみを保持する形を取ります。

ここでは、[AC20-FZK-Haus.ifc](https://www.ifcwiki.org/index.php?title=KIT_IFC_Examples) から以下の3件を抜粋して、どのようなデータが作られるかを説明します。

```text
#389= IFCSITE('0KMpiAlnb52RgQuM1CwVfd',#12,'Gelaende','Ebenes Gelaende','LandUse',#115,#383,$,.ELEMENT.,(49,6,1,566000),(8,26,11,540400),110.,$,$);
#434= IFCBUILDING('2hQBAVPOr5VxhS3Jl0O47h',#12,'FZK-Haus','FZK-Haus create by KHH / IAI / FZK','Wohnhaus',#432,$,$,.ELEMENT.,$,$,$);
#436= IFCRELAGGREGATES('0FWMHXglS7fAS5ox0icROM',#12,$,$,#389,(#434));
```

なお、以降の説明はイメージを掴むためのPythonでの疑似的なデータ構造であり、実際のC++のデータ構造とは異なります。

参考：[初期走査と索引の構築（parse.cpp）](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcparse/parse.cpp#L2805-L2876)

### インスタンスの内部オブジェクト

各インスタンスのIDと型を読み取り、対応する内部オブジェクトを作成します。属性値は、この時点では空です。

```py
inst389 = InstanceData(id=389, type="IfcSite", storage=None)
inst434 = InstanceData(id=434, type="IfcBuilding", storage=None)
inst436 = InstanceData(id=436, type="IfcRelAggregates", storage=None)
```

### 検索用のデータ

ID, Type, GlobalId でインスタンスを検索できるようにするための索引データも初期読み込み時に作成して保持します。「`(...)` 内の属性情報を完全には解析しない」と記載していましたが、実際はGlobalIdと逆参照の索引データを作成するために、それらの情報だけ解析しています。

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

参考：[検索用データの定義（storage.h）](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcparse/storage.h#L666-L670)

### 属性を読むための位置情報

`(...)` 内の属性情報は初期読み込み時にメモリ内部で保持していません。そのため、後から属性情報を読むためにファイル上のどの位置に各インスタンスの情報があるのかを保持します。位置は、型名の直後にある `(` の次のバイトです。

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

## 属性の保持

属性にアクセスしたときに、その情報を実際に読み取って解析し、内部にデータを保持します。
このとき単一の属性へのアクセスだとしても対象のすべての属性を解析して保持する形を取ります。

イメージ的には、以下のように `storage` にデータが格納されるような形です。

```py
"""
#389= IFCSITE('0KMpiAlnb52RgQuM1CwVfd',#12,'Gelaende','Ebenes Gelaende','LandUse',#115,#383,$,.ELEMENT.,(49,6,1,566000),(8,26,11,540400),110.,$,$);
"""

# 読み込んだ時点のデータ
inst389 = InstanceData(id=389, type="IfcSite", storage=None)

# どれかの属性にアクセスすると以下のようなデータが作られる
inst389.storage = [
  '0KMpiAlnb52RgQuM1CwVfd',
  inst12,
  'Gelaende',
  'Ebenes Gelaende',
  'LandUse',
  inst115,
  inst383,
  None,
  "ELEMENT",
  (49,6,1,566000),
  (8,26,11,540400),
  110.,
  None,
  None
]
```

一度ファイルから読み取って解析したらメモリ上に保持することで、同じデータに対して何度も解析処理をしないようにしています。

参考：[属性の遅延読み込み（parse.cpp）](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcparse/parse.cpp#L2733-L2762)

# メモリ使用量

これまでの説明の通り、遅延読み込みをすることでファイルの情報をすべて解析することなく、必要な情報のみを保持しています。つまり、メモリ上にすべてのデータを保持しない形なので、メモリ使用量も抑えられています。

ここでは実際にどれくらいのメモリ使用量になるかの概算と実際に計測した値を確認してみます。

## 仮定に基づく概算

:::note info
概算の計算は Codex におまかせ！
:::

ここでは64 bit環境を想定し、初期読み込み時に保持する主要なデータ構造のメモリ使用量をざっくり計算してみます。各データのサイズは仮定に基づくもので、環境やビルド構成によって変わります。

実際のIfcOpenShell上の `instance_data` では以下の情報を保持しています。
参考：[instance_data の定義（instance_data.h）](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcparse/instance_data.h#L539-L568)

| メンバー | 内容 | 仮定するサイズ |
| --- | --- | --- |
| `file_` | 所属するモデルへのポインタ | 8バイト |
| `declaration_` | `IfcWall` などの型定義へのポインタ | 8バイト |
| `identity_` | 内部管理用の識別番号 | 4バイト |
| `id_` | `#1234`などのインスタンスID | 4バイト |
| `storage_` | 解析済み属性の格納領域 | 16バイト |

この仮定では、属性情報を解析していない状態でも、1インスタンスあたり合計40バイトを使用する計算です。また、検索用のデータ4種と属性遅延読み込み用のデータも読み込み時に保持します。これらのサイズも以下のように仮定します。

- `byid_`: 48バイト / 1インスタンス
- `bytype_excl_`: 16バイト / 1インスタンス
- `byguid_`: 64バイト / `IfcRoot` の件数
- `byref_excl_`: 12バイト / max(参照数, ファイルサイズ / 32)
- `lazy_offsets_`: 16バイト / 1インスタンス

これらに加えて、共有ポインタの参照数などを管理する領域を1インスタンスあたり24バイトと仮定します。また、逆参照の領域については、初期容量として「ファイルサイズ / 32」件分が予約されるため、それも考慮します。
参考：[逆参照の初期容量の予約（parse.cpp）](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcparse/parse.cpp#L2808)

以上から、初期読み込み時に保持する主要なデータ構造のメモリ使用量を、以下のように概算します。

```text
144(40+48+16+16+24) × インスタンス数
＋ 12 × max(参照数, ファイルサイズ / 32)
＋ 64 × IfcRoot の件数
```

実際にはページキャッシュやメモリ管理のための領域なども必要になるため、使用量はこれより多くなることが考えられます。

どれくらい差があるか、次に実測してみます。

## 実測

実測した結果が以下です。ファイルサイズの異なる5種類のIFCファイルで計測しました。なお、実測のメモリ使用量はファイル読み込み前後の RSS の増加量です。

| ファイルサイズ | インスタンス数 | 参照数 | IfcRoot数 | 概算 MB | 実測 MB |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2.57 MB | 44,249 | 68,264 | 1,304 | 7.42 | 12.48 |
| 49.67 MB | 888,615 | 1,372,695 | 21,777 | 147.98 | 174.01 |
| 97.06 MB | 1,225,411 | 2,099,154 | 384,695 | 237.48 | 268.85 |
| 222.10 MB | 2,965,913 | 5,019,950 | 572,677 | 547.03 | 590.00 |
| 392.86 MB | 5,399,942 | 8,075,801 | 1,076,305 | 993.80 | 1,061.31 |

概算 + α くらいのメモリ使用量になっており、おおよそ想定していた通りの結果なのかなと思います。

参考：[計測スクリプト・実行環境](https://github.com/kiyuka829/qiita-articles/blob/33c2fdda1b7a2951942af665d666754eeea6ac9e/scripts/ifcopenshell-lazy-memory/README.md)

# まとめ

そんなわけで IfcOpenShell 0.9.0 が新しく出てパフォーマンスが上がっていたので、調べてみました。
遅延読み込みではファイルのデータをすべてメモリに載せないようになったからメモリ使用量かなり減っているのでは！？とも思ったのですが、それでもファイルサイズの3倍近くは使用するようです。実際は属性を読む（何らかの処理をする）とその情報をメモリに載せるのでもっと必要になるということですね。

でも体感 0.8 系と比べればかなり良くなってるからみんな 0.9 系を使おう！

ちなみに文体が途中で変わるのは書いてる途中でテンションが変わるからだよ。
仕方ないね (´・ω・｀)

# Appendix

## ページキャッシュ

属性を読むたびに毎回ファイルへアクセスすると、比較的重い処理であるファイルI/Oが増える。そのため、一度読み込んだデータの一部をメモリ上にキャッシュしている（`storage` での属性の保持の話とは別の話）。
ファイルは64 KiBごとのページに分けて読み込み、最大64ページを保持する形。必要な位置のページがキャッシュにあればそれを使い、なければファイルから読み込む。

データ構造的には以下のようなイメージで保持している。

```py
# ページ番号 → ページのデータと、利用順リスト上の位置
pages = {
    0: {
        "data": b"ISO-10303-21;\r\nHEADER;...",
        "lru_position": ...,  # lru の中のページ0の位置
    },
    1: {
        "data": b"...",
        "lru_position": ...,  # lru の中のページ1の位置
    },
}

# ページ番号を利用順に並べたリスト
# 最近使ったページが先頭
lru = [1, 0]
```

参考：[ページキャッシュのデータ構造（file_reader.h）](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.9.0post1/src/ifcparse/file_reader.h#L328-L369)

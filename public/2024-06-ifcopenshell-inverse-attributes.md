---
title: IfcOpenShellで逆属性を取得する
tags:
  - Python
  - IFC
  - BIM
  - IfcOpenShell
private: false
updated_at: '2024-06-21T20:04:38+09:00'
id: 2b3db8147412f282806c
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

[IfcOpenShell](https://ifcopenshell.org/)はBIMの標準フォーマットであるIFCファイルを扱うライブラリだよ。
そのIfcOpenShellで逆属性を取得するよ！！

> :::note info
> 「逆属性」 = 「inverse attribute」だよ！

使用した`IfcOpenShell`はバージョンは `0.7.0`です。

# 結論

早く回答ください(・Д・)っ/凵 ⌒☆ﾁﾝ ﾁﾝ
っていう人のために結果のコードだよ！

```py
import ifcopenshell
model = ifcopenshell.open(path)
item = model.by_type('IfcWall')[0]

# これだよ！！( ﾟ∀ﾟ)o彡°
inv_keys = (
    set(dir(item))
    - set(dir(ifcopenshell.entity_instance))
    - set(item.get_info().keys())
)
inverse_attributes = { key: getattr(item, key) for key in inv_keys }
```

# そもそも逆属性って何？

IFCを構成する各要素（IfcWallとかIfcSlabとかエンティティって呼ばれている要素たち）は、それぞれ属性を持っているよ。
たとえば[IfcSlab](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcSlab.htm)だと`GlobalId`～`PredefinedType`までの9個の属性があるね。IfcOpenShellで表示してみると下記のような感じだね。
あ、データはBlenderBIMの[ドキュメントページ](https://docs.blenderbim.org/users/exploring_an_ifc_model.html)にあるIFCファイルを使用しているよ。

```py
item = model.by_type('IfcSlab')[0]
item.get_info()
# {'id': 34509,
#  'type': 'IfcSlab',
#  'GlobalId': '1pPHnf7cXCpPsNEnQf8_6B',
#  'OwnerHistory': #12=IfcOwnerHistory(#7,#11,$,.ADDED.,$,$,$,1482339244),
#  'Name': 'Bodenplatte',
#  'Description': None,
#  'ObjectType': None,
#  'ObjectPlacement': #34464=IfcLocalPlacement(#477,#34463),
#  'Representation': #34505=IfcProductDefinitionShape($,$,(#34495,#34503)),
#  'Tag': 'E4D9CD4B-CA43-4735-94-BD-1FD4376BD455',
#  'PredefinedType': 'BASESLAB'}
```

じゃあ"逆"属性は？っていうとIFCのドキュメントの[Attributes](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcSlab.htm#6.1.3.35.3-Attributes)の表を見ると上記の9個の属性以外にも`HasAssignments`とか`IsDeclaredBy`とかみたいに#列に数字のついていない属性があるよね？これを逆属性とここでは呼んでいるよ。

![逆属性.PNG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/7fa26537-5bf2-6cfa-46c5-1e65d7d3572c.png)

# え？それって`get_inverse`で取得できるよね？

IfcOpenShellに`get_inverse`って関数あるからそれ使えばいいんじゃないの？って思うよね。確かにそれで逆属性も取得できるんだよね。

```py
model.get_inverse(item)
# {#34531=IfcRelAssociatesMaterial('22HuPqu8qBpALMZnyfqhUK',#12,$,$,(#34509),#34530),
#  #14517=IfcRelContainedInSpatialStructure('13J1BKcWxmCqHLM0nJ4nFJ',#12,$,$,(#14502,#15042,#15372,#15848,#16507,#16982,#17040,#17468,#18407,#18465,#18698,#19199,#19504,#20069,#20268,#20299,#20329,#20374,#20598,#20808,#21966,#23024,#23944,#27013,#27421,#27833,#28113,#31079,#31470,#31818,#32098,#32407,#32829,#33109,#33389,#33672,#34509,#35053),#479),
#  #34613=IfcRelDefinesByProperties('0NBjOOE7bx9S$iH5ujkO2m',#12,$,$,(#34509),#34611),
#  #34602=IfcRelDefinesByProperties('0tDKLSbXIVoh$W$V5W$PwA',#12,$,$,(#34509),#34575),
#  #34539=IfcRelDefinesByProperties('1B6RMRVlt73_0vPr1dONZL',#12,$,$,(#34509),#34536),
#  #34547=IfcRelDefinesByProperties('1ce7nQALQ4Uw9kMrk75YsH',#12,$,$,(#34509),#34544),
#  #34645=IfcRelDefinesByProperties('2Gsr2AVG5$zczeHEInpXFk',#12,$,$,(#34509),#34643),
#  #34661=IfcRelDefinesByType('3jE0353rdOAedUCYpD$jiH',#12,$,$,(#34509),#34648),
#  #77456=IfcRelSpaceBoundary('0wxqSYU9XfzU3VLFEoAGQ9',#12,'2ndLevel','2a',#33774,#34509,#77455,.PHYSICAL.,.EXTERNAL.),
#  #78243=IfcRelSpaceBoundary('1Wo7jfPGGvdgmZeiVZPQDp',#12,'2ndLevel','2a',#34763,#34509,#78242,.PHYSICAL.,.EXTERNAL.),
#  #78041=IfcRelSpaceBoundary('29sJT6Ho2mKZovzttaNM5H',#12,'2ndLevel','2a',#34191,#34509,#78040,.PHYSICAL.,.EXTERNAL.),
#  #77144=IfcRelSpaceBoundary('2Sn7uAlFxA$POrax5b6wqo',#12,'2ndLevel','2a',#21640,#34509,#77143,.PHYSICAL.,.EXTERNAL.),
#  #76656=IfcRelSpaceBoundary('2daBdKK14H6N6ekhTDweXH',#12,'2ndLevel','2a',#20909,#34509,#76655,.PHYSICAL.,.EXTERNAL.),
#  #76945=IfcRelSpaceBoundary('2weIpzIiCR4kwbSmcs97PG',#12,'2ndLevel','2a',#21283,#34509,#76944,.PHYSICAL.,.EXTERNAL.)}
```

ただこれ、正確には対象のエンティティを参照している要素すべてが取得されるんだよね。どういうことかというと、ドキュメントに記載されていない属性も実は取得していたりする。

どういうことかわかりにくいので例を上げてみる。

`IfcApplication`についての`get_inverse`の結果は以下のように`IfcOwnerHistory`が取得される。でも[IFCのドキュメント](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcApplication.htm)をみると`IfcApplication`に逆属性はない。
逆に`IfcOwnerHistory`の属性を`get_info`で確認すると`IfcApplication`が存在している。
つまり`get_inverse`はドキュメント上の逆属性を取得しているのではなく、通常の属性として参照されているエンティティ全てが取得されていると思われる。

IFCファイルの中身でいえば、
`#12= IFCOWNERHISTORY(#7,#11,$,.ADDED.,$,$,$,1482339244);`
のカッコ内に`#11`が含まれているので`#12`が`get_inverse`で取得されたということになる。

```py
item = model.by_type('IfcApplication')[0]
model.get_inverse(item)
# {#12=IfcOwnerHistory(#7,#11,$,.ADDED.,$,$,$,1482339244)}

# `IfcOwnerHistory`の属性
item = model.by_id(12)
item.get_info()
# {'id': 12,
#  'type': 'IfcOwnerHistory',
#  'OwningUser': #7=IfcPersonAndOrganization(#1,#3,$),
#  'OwningApplication': #11=IfcApplication(#10,'20.0.0','ARCHICAD-64','IFC2x3 add-on version: 4009 GER FULL'),
#  'State': None,
#  'ChangeAction': 'ADDED',
#  'LastModifiedDate': None,
#  'LastModifyingUser': None,
#  'LastModifyingApplication': None,
#  'CreationDate': 1482339244}
```

## つまりどういうことだってばよ

つまりは`get_inverse`だと逆属性以外も取得してしまうんだよ。逆属性のみ取得したい場合には適さないんだよね。あと属性名が取得できないんだよね。

# ではどうやって逆属性のみを取得すればいいのか

IfcOpenShellでは逆属性のみを直接取得する関数はなさそう。
（あったら教えてください！！！！）

でもIfcOpenShellのデータ定義上では逆属性も定義されている。

```py
item = model.by_type('IfcSlab')[0]
dir(item)
# ['ConnectedFrom',
#  'ConnectedTo',
#  'ContainedInStructure',
#  'Declares',
#  'Decomposes',
#  'Description',
#  'FillsVoids',
#  'GlobalId',
#  'HasAssignments',
#  'HasAssociations',
#  'HasContext',
#  'HasCoverings',
#  'HasOpenings',
#  'HasProjections',
#  'InterferesElements',
#  'IsConnectionRealization',
#  'IsDeclaredBy',
#  'IsDecomposedBy',
#  'IsDefinedBy',
#  'IsInterferedByElements',
#  'IsNestedBy',
#  'IsTypedBy',
#  'Name',
#  'Nests',
#  'ObjectPlacement',
#  'ObjectType',
#  'OwnerHistory',
#  'PredefinedType',
#  'ProvidesBoundaries',
#  'ReferencedBy',
#  'ReferencedInStructures',
#  'Representation',
#  'Tag',
#  ...
```

そして全てのエンティティは `ifcopenshell.entity_instance` を継承している。なおかつ明示属性は`get_info`で取得できる。
そのため、逆属性を取得したいエンティティのプロパティから、継承元の共通プロパティを削除し、さらに明示属性も削除すると逆属性が残ることになる。

```py
# 逆属性の属性名を取得
inv_keys = (
    set(dir(item))
    - set(dir(ifcopenshell.entity_instance))
    - set(item.get_info().keys())
)
# {'ConnectedFrom',
#  'ConnectedTo',
#  'ContainedInStructure',
#  'Declares',
#  'Decomposes',
#  'FillsVoids',
#  'HasAssignments',
#  'HasAssociations',
#  'HasContext',
#  'HasCoverings',
#  'HasOpenings',
#  'HasProjections',
#  'InterferesElements',
#  'IsConnectionRealization',
#  'IsDeclaredBy',
#  'IsDecomposedBy',
#  'IsDefinedBy',
#  'IsInterferedByElements',
#  'IsNestedBy',
#  'IsTypedBy',
#  'Nests',
#  'ProvidesBoundaries',
#  'ReferencedBy',
#  'ReferencedInStructures'}
```

逆属性の属性名が取得できたので、あとは`getattr`で値を取得するだけ。

```py
inverse_attributes = { key: getattr(item, key) for key in inv_keys }
# {'IsDecomposedBy': (),
#  'IsDefinedBy': (#34539=IfcRelDefinesByProperties('1B6RMRVlt73_0vPr1dONZL',#12,$,$,(#34509),#34536),
#   #34547=IfcRelDefinesByProperties('1ce7nQALQ4Uw9kMrk75YsH',#12,$,$,(#34509),#34544),
#   #34602=IfcRelDefinesByProperties('0tDKLSbXIVoh$W$V5W$PwA',#12,$,$,(#34509),#34575),
#   #34613=IfcRelDefinesByProperties('0NBjOOE7bx9S$iH5ujkO2m',#12,$,$,(#34509),#34611),
#   #34645=IfcRelDefinesByProperties('2Gsr2AVG5$zczeHEInpXFk',#12,$,$,(#34509),#34643)),
#  'IsDeclaredBy': (),
#  'HasOpenings': (),
#  'IsTypedBy': (#34661=IfcRelDefinesByType('3jE0353rdOAedUCYpD$jiH',#12,$,$,(#34509),#34648),),
#  'HasAssignments': (),
#  'Decomposes': (),
#  'IsInterferedByElements': (),
#  'HasProjections': (),
#  'HasCoverings': (),
#  'ConnectedFrom': (),
#  'IsConnectionRealization': (),
#  'IsNestedBy': (),
#  'Nests': (),
# ...
#   #78041=IfcRelSpaceBoundary('29sJT6Ho2mKZovzttaNM5H',#12,'2ndLevel','2a',#34191,#34509,#78040,.PHYSICAL.,.EXTERNAL.),
#   #78243=IfcRelSpaceBoundary('1Wo7jfPGGvdgmZeiVZPQDp',#12,'2ndLevel','2a',#34763,#34509,#78242,.PHYSICAL.,.EXTERNAL.)),
#  'ConnectedTo': (),
#  'ReferencedBy': (),
#  'Declares': ()}
```

# まとめ

IfcOpenShellでの逆属性の取得方法でした。

これ需要あるの？（というか需要がないからIfcOpenShellで実装されてないんじゃ...？）と思いつつ、下記みたいなことしたくて必要だったのでまとめました。

https://twitter.com/kiyuka_study/status/1727919084367642757?s=20

そして途中で口調に飽きて普通の文章になりました。

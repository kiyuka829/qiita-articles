---
title: IFCファイルの中身を解読する
tags:
  - IFC
  - BIM
private: false
updated_at: '2022-11-27T01:57:43+09:00'
id: 00434f1b8e0b38c621fb
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

IFC形式のファイルが何かというとBIMの標準フォーマットです。ArchicadやRevitなどのBIMソフトウェア間でデータをやり取りするときの中間ファイルとしても使われます。建築分野で使用されるファイルですね。
拡張子が`.ifc`というだけのテキストデータなのでメモ帳などのテキストエディタでも開くことができ、内容の解析も可能です。可能ではありますが、ファイルのフォーマットが特殊なのでパッと見ても何がなにやらでよくわかりません。
IFCからJSONやXMLへの変換も可能なようですが、それでもそもそもIFCがどういうふうにデータを保持しているのかを知らないと中身を理解するのは難しいというのもあるのでIFCについて解読していきたいと思います。

また、今回使用したifcファイルについては[IFC.jsのGitHub](https://github.com/IFCjs/test-ifc-files)から「TESTED_Simple_project_01.ifc」をお借りしました。

# ファイルを開く

エディタは VS Code を使用していきます。拡張で`IFC Syntax`を入れるとシンタックスハイライトで色が付くので見やすいです。見てみるとこんな感じ。
![ifcfile.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/9e750f9f-5c90-5885-627b-d79743e0fc63.png)
最初の「HEADER」～「ENDSEC」はだいたいコメントなので今回は見ません。「FILE_SCHEMA」がIFC形式のバージョンなので、そこを気にするくらいでしょうか。
「DATA」以降が建物の形状や情報を記載している部分になります。今回はこの部分に触れていきます。

# データの中身を見る

さて、データの中身を見ていきます。一行目です。

```
#1= IFCORGANIZATION($,'Autodesk Revit 2021 (ESP)',$,$,$);
```

「IFCORGANIZATION」というデータ型に `$,'Autodesk Revit 2021 (ESP)',$,$,$` の5つの要素が設定されています。先頭の`#1`は番号（変数）です。
IFCORGANIZATIONが何かを[ドキュメントのIfcOrganization](http://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcOrganization.htm)を見て確認してみると、組織の情報であり、5つの要素はそれぞれ「ID, 名前, 説明, 役割, 住所」を示しているようです。`$`は未設定の項目となるので、名前に'Autodesk Revit 2021 (ESP)'が設定されているという状態です。
※ IFC2x3のドキュメントは型定義へのリンクが作れないのでIFC4x3のリンクを貼っています

こんな感じにIFCファイルの各行は `#【番号】= 【データ型】(データの属性, ...)` という形式になっています。ちなみに先頭の番号は連番というわけではなく、順序も関係ないようです。単純に変数名として番号を使っているだけと思われます。

## スラブのデータを見る

上から見ていっても楽しくないので（いや組織とかわかっても...って感じですよね）、次は試しにスラブを見てみます。

```
#22551= IFCSLAB('1s5utE$rDDfRKgzV6jUJ3d',#41,'Suelo:Por defecto - 30 cm:166729',$,'Suelo:Por defecto - 30 cm',#22529,#22549,'166729',.FLOOR.);
```

やっぱりよくわからないので[ドキュメントのIfcSlab](http://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcSlab.htm)を確認します。
Attributesの項目を見てみるとカッコ内の属性9個は「GlobalId, OwnerHistory, Name, Description, ObjectType, ObjectPlacement, Representation, Tag, PredefinedType」に対応しているようです。
この9個を順番に見ていきます。

### GlobalId

IDですね。値としては '1s5utE$rDDfRKgzV6jUJ3d' が入っています。
GlobalId はファイル内だけでなく、別のIFCファイルとも区別をつけられるように一意なIDが割り振られているようです。

### OwnerHistory

所有者の履歴だそうです。値には「#41」が入っています。これは、IFCファイル内の「#41」を参照しています、という意味です。つまり実際の内容は「#41」に格納されています。
見てみると `#41= IFCOWNERHISTORY(#38,#5,$,.NOCHANGE.,$,$,$,1606175882);` でした。この内容は詳しくは見ません（見ても面白くなさそうなので）。詳しく見たい場合はまたさらにIFCOWNERHISTORYのドキュメントを見て...としていけば確認できると思います（とてもやりたくない）。

### Name, Description, ObjectType

それぞれ「名前、説明、オブジェクトタイプ」で値に「'Suelo:Por defecto - 30 cm:166729', $, 'Suelo:Por defecto - 30 cm'」が入っています。説明（Description）は何も入ってないことを示す `$` です。
どれもスラブについてテキストでの説明している要素と思われます。この場合「厚さ30cmのスラブです」という情報が文字として入っているという感じでしょうか。

### ObjectPlacement, Representation

これらがスラブの形状を定義している要素と思われます。値としては「#22529,#22549」が設定されており、どちらも参照型です。
おそらく一番知りたい情報がここだと思われますが、これを手作業で解析するのは地獄です。ちょっと潜ってみましたが参照地獄になっていました。
ちなみにこんな感じ `#22529= IFCLOCALPLACEMENT(#136,#22528);`, `#22549= IFCPRODUCTDEFINITIONSHAPE($,$,(#22547));` で更にこの先も参照型になっています。

そのため形状情報については素直に、オープンソースの[IFC.js](https://ifcjs.github.io/info/ja/)や[IfcOpenShell](http://ifcopenshell.org/)などで解析するのが良いかなと思います。IfcOpenShellについてはQiitaでもまとめている方がいると思います。

### Tag

タグです...。今回の場合 '166729' という値が入っていますが、何かよくわかりませんでした。何かを識別するためのものっぽいです。

### PredefinedType

`.FLOOR.`という、今まで出てこなかったタイプの値が入ってますね。ドキュメント見ると [IfcSlabTypeEnum](http://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcSlabTypeEnum.htm) に定義されている中から、どれかが設定されていることがわかります。
内容としては、スラブがどういう用途で使われているかが設定される項目であり、今回の場合はFLOORが設定されているので床スラブだということがわかります。

IFCファイル内でこんな感じに `.XXX.` とドットで囲まれた値は、定義済みの列挙型から選択して値が入っているものとなります。

# まとめ

IFCファイルの中身を見て、どういうファイルフォーマットになっているか確認して解読していきました。そしてスラブだけ見て力尽きました。手作業でやるもんじゃないですね。素直に[IFC.js](https://ifcjs.github.io/info/ja/)や[IfcOpenShell](http://ifcopenshell.org/)などを使って解析するのが賢いと思います。

まあでもIFC仕様のドキュメントの見方とか参考になればいいかなって。あとIFCに関する日本語の資料がびっくりするくらい少ないので増えてくれたら嬉しいなって。~~誰か書いて~~

# 参考

- buildingSMART
    - [Industry Foundation Classes (IFC)](https://technical.buildingsmart.org/standards/ifc/)
    - [IFC Specifications Database](https://technical.buildingsmart.org/standards/ifc/ifc-schema-specifications/)
    - [IFC 4.3 documentations](http://ifc43-docs.standards.buildingsmart.org/)
- [buildingSMART Japanの講座動画](https://www.youtube.com/playlist?list=PLdIXDBW_lzCbM2yNdWfjpWKdJ82aAItWj) : IFCについての貴重な日本語の解説



---
title: web-ifcでIFCファイルを読み込む
tags:
  - JavaScript
  - Node.js
  - IFC
  - IFC.js
private: false
updated_at: '2022-12-25T10:13:06+09:00'
id: c64d777be2707665d2cc
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

[前回の記事](https://qiita.com/kiyuka/items/00434f1b8e0b38c621fb)ではIFCファイルのテキストを見て手作業で解読しました。まあなんというかとてもめんどくさい作業でした。~~もうやりたくないです。~~
そんなわけで今回はJavaScriptライブラリの [IFC.js](https://ifcjs.github.io/info/) を使って解読していきたいと思います。

# IFC.js とは

IFC.jsが何かというと、[公式ドキュメント](https://ifcjs.github.io/info/ja/docs/Introduction)より

> IFC.jsは、IFCファイルの読み書きを非常に簡単に行うことができるJavaScriptライブラリです。

とのことです。わざわざ手作業でIFCファイルを読み解く必要はないってことですね！やったー！！

# web-ifcでファイルを読み込む

IFC.jsは `web-ifc`, `web-ifc-three`, `web-ifc-viewer` の3つのレイヤーで構成されているのですが、`web-ifc-three`, `web-ifc-viewer`についてはブラウザ上でBIMの3Dモデルを表示するビューアーです。
今回はIFCファイルの読み解きをしたいのでIFCパーサーである [web-ifc](https://github.com/IFCjs/web-ifc) を使用していきます。web-ifc は`npm install web-ifc` でインストールできます。

ではさっそくIFCファイルを読んでいきます。公式サンプルの[ifc-to-json](https://github.com/IFCjs/hello-world/blob/main/examples/web-ifc/ifc-to-json/node/main.js)からファイル読み込み部分を抽出したものが以下です。

```js
const WebIFC = require('web-ifc/web-ifc-api-node');
const fs = require("fs");

async function OpenIfc(filename) {
    const ifcData = fs.readFileSync(filename);
    await ifcapi.Init();
    return ifcapi.OpenModel(ifcData);
}

async function LoadFile(filename)
{
    const modelID = await OpenIfc(filename);

    // なんやかんやここで処理する

    ifcapi.CloseModel(modelID);
}

const ifcapi = new WebIFC.IfcAPI();
LoadFile('01.ifc');
```

読み込めました！簡単！あとは情報を読み取っていくだけ！
ちなみに公式サンプルをそのまま使えばIFCファイルをJSON形式に変換できます。

# データを読む

ファイルを開いて読み込めたので、中身を読み取っていこうと思います。
また、データについては前回と同様に[IFC.jsのGitHub](https://github.com/IFCjs/test-ifc-files)から「TESTED_Simple_project_01.ifc」をお借りしました。

ちなみに、ファイルにコードを書いて `node xxx.js` の形式で実行してもいいのですが、[IJavascript](https://github.com/n-riesco/ijavascript) を使用してJupyter Notebook上で動かすほうがインタラクティブに実行できるので、いろいろ試しながらコードを書くにはおすすめです。

Jupyter Notebookで動かすとこんな感じです。（非同期処理である都合上、ファイル実行するときとは違う書き方をしています。）
処理を少しづつ実行できるので、結果を確認しながらコードを書くことができて便利です。
![ijascript.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/5ba78302-e326-c59f-a126-1e165f3d8666.png)

## 一行目を読む

前回と同じようにまずは一行目を見てみます。以下で一行目の情報を取得できます。

```js
// 全行取得
const lines = ifcapi.GetAllLines(modelID);

// 0行目のIDを取得
const itemID = lines.get(0);

// プロパティ取得
const props = ifcapi.GetLine(modelID, itemID)
```

`props` を表示してみると下記のようになっています。
IFCファイルのデータの最初の行が `#1= IFCORGANIZATION($,'Autodesk Revit 2021 (ESP)',$,$,$);` なので、確かに一行目が取得できていそうです。

```
IfcOrganization {
  expressID: 1,
  type: 4251960020,
  Identification: null,
  Name: { type: 1, value: 'Autodesk Revit 2021 (ESP)' },
  Description: null,
  Roles: null,
  Addresses: null
}
```

## スラブを読む

次にスラブのデータを取得してみましょう。特定のIFCクラスのデータを取得するには下記のように`GetLineIDsWithType` で取得します。

```js
// スラブの行を取得
const lines = ifcapi.GetLineIDsWithType(modelID, WebIFC.IFCSLAB);

// 0番目のスラブのIDを取得
const itemID = lines.get(0);

// プロパティ取得
const props = ifcapi.GetLine(modelID, itemID)
```

`props` を表示してみると下記のようになっています。
IFCファイル上でスラブは `#22551= IFCSLAB('1s5utE$rDDfRKgzV6jUJ3d',#41,'Suelo:Por defecto - 30 cm:166729',$,'Suelo:Por defecto - 30 cm',#22529,#22549,'166729',.FLOOR.);` となっているので、取得できていることがわかります。

```
IfcSlab {
  expressID: 22551,
  type: 1529196076,
  GlobalId: { type: 1, value: '1s5utE$rDDfRKgzV6jUJ3d' },
  OwnerHistory: { type: 5, value: 41 },
  Name: { type: 1, value: 'Suelo:Por defecto - 30 cm:166729' },
  Description: null,
  ObjectType: { type: 1, value: 'Suelo:Por defecto - 30 cm' },
  ObjectPlacement: { type: 5, value: 22529 },
  Representation: { type: 5, value: 22549 },
  Tag: { type: 1, value: '166729' },
  PredefinedType: { type: 3, value: 'FLOOR' }
}
```

## typeってなんだ？

スルーしましたが、表示したデータに `type` がいくつか出てきてます。
「`expressID`の下にあるtype」と「`{ type: 1, value: XX }`の形式で出てくるtype」の2種類ありますが、それぞれ別の意味です。

`expressID`の下にある `type` は、各IFCクラスに対応する定数になっています。
下記のように `WebIFC.IFCORGANIZATION`, `WebIFC.IFCORGANIZATION` を表示してみると`type`の値と一致していることがわかります。

```js
console.log(WebIFC.IFCORGANIZATION) // 4251960020
console.log(WebIFC.IFCSLAB) // 1529196076
ifcapi.properties.getIfcType(4251960020) // 'IFCORGANIZATION'
ifcapi.properties.getIfcType(1529196076) // 'IFCSLAB'
```

`{ type: 1, value: XX }`の形式になっている各項目の `type` は `value`の型を示しています。1であれば文字列、3であればIFC上で定義されている列挙型、5であれば参照型、のような感じになっています。
たとえば、`Representation: { type: 5, value: 22549 }` であれば、22549は数値ではなく`#22549`のIDを参照しているということですね。

ちなみに各数字はソースコードを見ると下記に対応しているようです。

- 0: UNKNOWN
- 1: STRING
- 2: LABEL
- 3: ENUM
- 4: REAL
- 5: REF
- 6: EMPTY
- 7: SET_BEGIN
- 8: SET_END
- 9: LINE_END

これだけ見てもなんの型なのかよくわからないものもありますが、[IFC仕様のドキュメント](http://ifc43-docs.standards.buildingsmart.org/)のクラス定義を見ながら各プロパティを確認していくとおそらくわかるのではないかなと思います。

## 参照型の先を覗く

前回「スラブのObjectPlacement, Representationが参照地獄だ！手作業じゃ無理！」という状態でした。でも web-ifc であればとっても簡単！

```js
// 第3引数を true にすると参照型を再帰的に取得できる
props = ifcapi.GetLine(modelID, itemID, true)

// すべての階層を表示するのであればJSON文字列化する
// console.log(JSON.stringify(props, null, 2))
```

取得したpropsを表示すると下記のようになります。深い階層は表示されていませんが、参照先も取得できていることがわかります。すべて表示したい場合はJSON化すると見ることができます。

```
IfcSlab {
  expressID: 22551,
  type: 1529196076,
  GlobalId: { type: 1, value: '1s5utE$rDDfRKgzV6jUJ3d' },
  OwnerHistory: IfcOwnerHistory {
    expressID: 41,
    type: 1207048766,
    OwningUser: IfcPersonAndOrganization {
      expressID: 38,
      type: 101040310,
      ThePerson: [IfcPerson],
      TheOrganization: [IfcOrganization],
      Roles: null
    },
    OwningApplication: IfcApplication {
      expressID: 5,
      type: 639542469,
      ApplicationDeveloper: [IfcOrganization],
      Version: [Object],
      ApplicationFullName: [Object],
      ApplicationIdentifier: [Object]
    },
    State: null,
    ChangeAction: { type: 3, value: 'NOCHANGE' },
    LastModifiedDate: null,
    LastModifyingUser: null,
    LastModifyingApplication: null,
    CreationDate: { type: 4, value: 1606175882 }
  },
  Name: { type: 1, value: 'Suelo:Por defecto - 30 cm:166729' },
  Description: null,
  ObjectType: { type: 1, value: 'Suelo:Por defecto - 30 cm' },
  ObjectPlacement: IfcLocalPlacement {
    expressID: 22529,
    type: 2624227202,
    PlacementRelTo: IfcLocalPlacement {
      expressID: 136,
      type: 2624227202,
      PlacementRelTo: [IfcLocalPlacement],
      RelativePlacement: [IfcAxis2Placement3D]
    },
    RelativePlacement: IfcAxis2Placement3D {
      expressID: 22528,
      type: 2740243338,
      Location: [IfcCartesianPoint],
      Axis: null,
      RefDirection: null
    }
  },
  Representation: IfcProductDefinitionShape {
    expressID: 22549,
    type: 673634403,
    Name: null,
    Description: null,
    Representations: [ [IfcShapeRepresentation] ]
  },
  Tag: { type: 1, value: '166729' },
  PredefinedType: { type: 3, value: 'FLOOR' }
}
```


# まとめ

web-ifcを使ってIFCファイルを読み込みました。前回と同様に一行目とスラブの行を読みましたが、やっぱりドキュメントを見るなりして、IFCのデータ構造をある程度理解していないと何がなにやらよくわかりませんね。
でも手作業で読み解くよりもだいぶ楽ちんになります。特に参照型の値を手作業で解析するのはかなりつらいですが、IFC.jsであれば参照先を簡単に取得できました。

今回は単純にファイルを読み込んで内部の構造を見ただけですが、建物の形状情報などもIFC.jsであれば簡単に取得することが可能です。そしてブラウザ上で3Dモデルを表示することも可能です。3Dモデルをくるくるするのも楽しいですよね。~~だからみんなIFC.jsの記事書いて~~

# 参考

- [GitHub: web-ifc](https://github.com/IFCjs/web-ifc)
- [web-ifc-API](https://ifcjs.github.io/info/ja/docs/Guide/web-ifc/web-ifc-API)

---
title: Open BIM Components(IFC.js)の最小構成
tags:
  - JavaScript
  - IFC
  - IFC.js
private: false
updated_at: '2024-06-03T01:19:50+09:00'
id: 9a529aca46afd5abbcfc
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

2023年9月[^Sep]？11月[^Nov]？くらいにIFC.jsが一新されて、[`Open BIM Components`](https://github.com/ThatOpen/engine_components) というライブラリに変わっていました。

[^Sep]: 2023年9月に`web-ifc-viewer`が[非推奨になっている](https://github.com/ThatOpen/web-ifc-viewer/commit/1f5c975ad6d019e7355c8759369f318f9fa3e339)
[^Nov]: 2023年11月に`Open BIM Components`の初板?が[リリース](https://github.com/ThatOpen/engine_components/releases)


もともと `IFC.js`は `web-ifc`, `web-ifc-three`, `web-ifc-viewer` の3つのレイヤーで構成されていました。それが、IFCのパーサーである `web-ifc` はそのままで、ブラウザ上でIFCの3Dモデルを表示するビューアーである `web-ifc-three`, `web-ifc-viewer` が廃止されて `Open BIM Components` になったようです。
また、GitHubもIFC.jsから[That Open](https://github.com/ThatOpen)に名称が変わっています。ライブラリ全体の呼び名としてはThat Openとになったということでしょうか？でもそれだとちょっとわかりにくいので、ここではIFC.jsと呼ぶことにします。


その新しくなったIFC.jsでIFCのモデルを表示する最小構成を調べました。


# engine_templates

[公式ドキュメント](https://docs.thatopen.com/intro)はあるのですが、コードが部分的にしか掲載されていないので、実際に動かそうにもどうすればいいのかわかりませんでした。

そこで、ThatOpenのリポジトリを確認してみると [ThatOpen/engine_templates](https://github.com/ThatOpen/engine_templates) に実際に動かせるコードがありました。

# 最小構成

`engine_templates` の `templates/vanilla` をもとにして、IFCを読み込んでモデルを表示する処理のみにすると以下になります。

```ts:main.ts
import * as OBC from "openbim-components"

// Three.js 準備
const viewer = new OBC.Components()

// シーン
const sceneComponent = new OBC.SimpleScene(viewer)
sceneComponent.setup()
viewer.scene = sceneComponent

// レンダラー
const viewerContainer = document.getElementById("app") as HTMLDivElement
const rendererComponent = new OBC.PostproductionRenderer(viewer, viewerContainer)
viewer.renderer = rendererComponent

// カメラ
const cameraComponent = new OBC.OrthoPerspectiveCamera(viewer)
viewer.camera = cameraComponent

await viewer.init()

// IFC読み込み準備
const ifcLoader = new OBC.FragmentIfcLoader(viewer)
await ifcLoader.setup()

// ファイル選択アイコン表示
const mainToolbar = new OBC.Toolbar(viewer)
mainToolbar.addChild(
  ifcLoader.uiElement.get("main"),
)

viewer.ui.addToolbar(mainToolbar)
```

IFCファイルを読み込んだ状態の画面はこんな感じです。

![obc-minimal.PNG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/57f5422b-309b-28f7-34a6-99cfe9a4e66b.png)

また、HTML, CSSなどの他のコードは [GitHub](https://github.com/kiyuka829/obc-minimal) に公開しているので、コード全体が見たい場合はそちらも見てもらえれば。


# 解説

簡単な解説です。

## Three.js

[Three.jsのドキュメント](https://threejs.org/docs/index.html#manual/en/introduction/Creating-a-scene)を確認すると以下のように書いてあります。

> 実際にthree.jsで何かものを表示できるようにするには、scene、camera、rendererの3つが必要です。

最初の `const viewer = new OBC.Components()` ～ `await viewer.init()` の部分は、このThree.jsでの処理に対応おり、3Dモデルを表示させるために必要な記述となります。Three.jsのセットアップ処理をOBCで行うと以下のようになるというわけですね。

```ts
const viewer = new OBC.Components()

// シーン
const sceneComponent = new OBC.SimpleScene(viewer)
sceneComponent.setup()
viewer.scene = sceneComponent

// レンダラー
const viewerContainer = document.getElementById("app") as HTMLDivElement
const rendererComponent = new OBC.PostproductionRenderer(viewer, viewerContainer)
viewer.renderer = rendererComponent

// カメラ
const cameraComponent = new OBC.OrthoPerspectiveCamera(viewer)
viewer.camera = cameraComponent

await viewer.init()
```

## IfcLoader 

次にIFCを読み込むための準備をしています。
IFCを読み込みにはパーサーである`web-ifc`を使用しており、そのためにはWASMモジュールの読み込みが必要です。以下ではそういったセットアップ処理を行っています。

```ts
const ifcLoader = new OBC.FragmentIfcLoader(viewer)
await ifcLoader.setup()
```

## Toolbar

最後にツールバーを表示させ、そこにファイル選択ボタンを設置しています。これにより選択したIFCファイルの3Dモデルを表示させることができます。

```ts
const mainToolbar = new OBC.Toolbar(viewer)
mainToolbar.addChild(
  ifcLoader.uiElement.get("main"),
)

viewer.ui.addToolbar(mainToolbar)
```

# まとめ

Open BIM Componentsの最小構成でした。

あまり調べきれていませんが、基本的なツール郡がコンポーネント化されているので、そこそこ簡単にBIMアプリケーションを作成できるらしいです。ちょこちょこ触って遊んでいきたいですね。


---
title: Babylon.jsで変身！
tags:
  - Babylon.js
private: false
updated_at: '2022-12-12T07:03:50+09:00'
id: a27bbe83566f6bf98119
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
この記事は[Babylon.js Advent Calendar 2022](https://qiita.com/advent-calendar/2022/babylonjs)の12日目の記事です。

<!--
![Dude-Dummy.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/3a1d69f1-d82e-5dec-0c8d-7b573982e8c7.png)
-->

# はじめに

変身っていいですよね。ライダーとか戦隊モノとか魔法少女モノとか。あとちょっとちがうけどアイドルの衣装チェンジとかも。普段と違う姿になって活躍するって憧れちゃうね！

そんなわけでBabylon.js界のアイドル？Dudeくんを変身させようと思います。

# 変身！！

というわけで変身しました。コードは[ここ](https://playground.babylonjs.com/#JS5PZI)に。

![Dude-transform.gif](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/0ff1e964-6ec2-5686-60a9-57782864d882.gif)

# コード解説的なもの

基本的にやっていることは `clipPlane` でメッシュが見える領域を切り替えているだけです。
`clipPlane` でどういう事ができるかについては[公式ドキュメント](https://doc.babylonjs.com/features/featuresDeepDive/scene/clipPlanes)にあるサンプルがとても分かりやすいのでそちらを見るのがおすすめです。

今回ほぼ公式のサンプルの [Clipping Planes Example](https://playground.babylonjs.com/#Y6W087) をそのまま使ってちょこちょこ変更して作りました。変更点はだいたいこんな感じ。
- メッシュを2つ読み込む
- 2つのメッシュスケールを合わせる
- sceneではなくメッシュに対してclipPlaneを設定する
    - いい感じに変身できるようにパラメータを調整する

とざっくりこれだけです。

## クリッピングプレーンの領域

今回クリッピングプレーンを使ってメッシュの表示を切り替えました。このとき平面を `scene.clipPlane
 = new BABYLON.Plane(0, 1, 0, XX)` みたく設定するわけですが、どっちがプラス方向やねん！となったので図を描きました。
青色部分がメッシュが見えなくなる領域です。

![上からclipPlane.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/e1231b04-8c4e-7da8-c4b3-237cb4ed96f5.png)

上方向を見えなく（下側が見えるように）する場合、`new BABYLON.Plane(0, 1, 0, XX)`の形式で指定します。第4引数は下向きがプラスになっています。

![下からclipPlane.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/a84cfc85-b900-7607-f47a-1138abf0fcf9.png)

逆に下方向を見えなく（上側が見えるように）する場合、`new BABYLON.Plane(0, -1, 0, XX)`の形式で指定します。第4引数は上向きがプラスになっています。

今回はY方向（高さ方向）でのクリップの例でしたが、X方向やZ方向（奥行方向）で指定するときも、Xは右がプラス、Yは上がプラス、Zは奥行きがプラス、なので...と考えて同じように指定すれば自由にクリップ領域を指定できそうですね。

# まとめ

これDodeくんが変身じゃなくてDodeくんに変身では？とか言わない。
あとはクリッピングプレーン部分にエフェクトとかかけるともっと変身っぽくなると思います。
それと本当は12月だしサンタ衣装に着せ替えしてDudeくんを可愛くしたかった。。けどサンタ衣装が用意できなかった。誰かDudeくんを可愛くしてあげてください。

# 参考

- 公式ドキュメント
    - [Using Clipping Planes](https://doc.babylonjs.com/features/featuresDeepDive/scene/clipPlanes)
    - [The Meshes Library](https://doc.babylonjs.com/toolsAndResources/assetLibraries/availableMeshes)

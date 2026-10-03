---
title: Babylon.jsのMaterialStencilStateのサンプルを解読する
tags:
  - Babylon.js
private: false
updated_at: '2023-12-15T16:28:51+09:00'
id: 1c0a9cd0545efd91c7b7
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
この記事は[Babylon.js Advent Calendar 2023](https://qiita.com/advent-calendar/2023/babylonjs)の15日目の記事です。

# はじめに

Babylon.jsの[ドキュメント](https://doc.babylonjs.com/typedoc/classes/BABYLON.MaterialStencilState)内に面白い[サンプル](https://playground.babylonjs.com/#CW5PRI#10)見つけた！どうなってるんだろう？解読しなきゃ！！

![top.JPG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/f3b407ff-9abb-faab-8b18-51938cacb2c2.jpeg)

そんなわけで、MaterialStencilStateのサンプルコードを解読していきます。


# 事前に知っておくといいもの

このサンプルコードではステンシルバッファを使用しています。先にステンシルバッファで何ができるのかをある程度把握しておいたほうがいいかもしれません。

個人的に参考になったリンクを張っておきます。

https://zenn.dev/kento_o/articles/dd99c6c9e98d4a

https://nn-hokuson.hatenablog.com/entry/2017/05/02/185320

https://wgld.org/d/webgl/w038.html

# どういう構造になっているのか

このサンプル、ぱっと見だと立方体にサイコロの穴のようなものがあるように見えます。しかしそうではなく、平面6個と穴の部分の球6個で作成されています。

```js:平面6つと球6つ
// 立方体を構成する平面
makePlane("x", 3);
makePlane("-x", 5);
makePlane("-z", 7);
makePlane("z", 9);
makePlane("y", 11);
makePlane("-y", 13);

// 表示制御用の半球
makeSphereIntersect("x", 3);
makeSphereIntersect("-x", 5);
makeSphereIntersect("-z", 7);
makeSphereIntersect("z", 9);
makeSphereIntersect("y", 11);
makeSphereIntersect("-y", 13);

// 穴として表示する半球
makeSphere("x", 3);
makeSphere("-x", 5);
makeSphere("-z", 7);
makeSphere("z", 9);
makeSphere("y", 11);
makeSphere("-y", 13);
```


一つの面を削除して色々制御をなくして表示すると、面と半球は以下のような配置になっています（平面と半球が同じテクスチャだとわかりにくいので変えています）。立方体の内側に半球が入っているような形ですね。
※ `SphereIntersect`と`Sphere` は同じ位置に重なって配置されています。
コードは[こちら](https://playground.babylonjs.com/#P0JCPI#1)

![配置.JPG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/ba5430ca-09c2-bceb-bc9b-d4db5c79e62f.jpeg)

## `makeSphereIntersect` はなにを？

平面と半球で構成されていました。では`makeSphereIntersect`ってなにをしているの？ということで、これの表示を変えてみると以下のようになります。

左が元の状態、中央が`makeSphereIntersect`をコメントアウト（削除）した状態、右が10行目を`mat0.disableColorWrite = false;`にした状態です。

![intersectの有無.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/865624f8-fc87-317b-e539-68a03a24e8ab.jpeg)

単純にコメントアウトすると若干わかりにくいので、右側はあえて表示させるパターンです。`SphereIntersect`によって半球の外側を表示しないように（平面を表示するように）制御しているようです。これによって穴としての表現をしているようです。なんだか不思議ですね？

# なぜ立方体の内側にある球が見えているのか？

立方体の内側に球が配置されているわけですが、立方体に穴が空いているから中にある半球が見えている、というわけではありません。穴が空いているわけでもないのに、元のコードでは内側にある半球が見えています。本来物体の奥側にあるものは隠れて見えないはずです。なぜ見えているのでしょうか？

これは以下の3つトリックによって実現しています。

- レンダリンググループが、`Plane`は`0`、`SphereIntersect`は`1`、`Sphere`が`2`、であること。つまりはこの順番にレンダリングされる、ということ。
- `depthFunction`の設定を変えて、`SphereIntersect`と`Sphere`については、物体の奥側にあるものほど画面上に表示されるようになっていること。
- ステンシルバッファを設定することで、特定のオブジェクトを通さないと`SphereIntersect`と`Sphere`が表示されないようにしていること。

レンダリンググループごとにどのような処理が行われているのかを順に説明していきます。

## 深度テストとステンシルテスト

画面に物体が表示されるためには「深度テスト」と「ステンシルテスト」の2つに合格する必要があります。
深度テストは、奥行き情報を使用して物体の表示を制御する、というものです。手前にある物体が見える、というものですね。ただし、今回のサンプルでは`depthFunction`の設定を変えることでその条件を変えています。
ステンシルテストは、奥行き情報以外で物体の表示非表示を設定するものです。通常、ステンシルは無効になっています。これを有効にするとステンシルバッファというものを参照して描画を制御することができます。


## レンダリンググループ0 : `plane`の描画

レンダリンググループ0から順にレンダリングされていきます。サンプルでレンダリンググループが0に属するのは平面です（レンダリンググループは特に指定していなければ0になります）。つまり最初は平面が描画されます。そして平面の描画は以下で行っています。

```js
const makePlane = (axis, stencilRef) => {
    // 平面の作成と配置場所の設定
    var mul = axis.charAt(0) == '-' ? -1 : 1;
    if (mul < 0) axis = axis.substring(1);

    var plane = BABYLON.MeshBuilder.CreatePlane("plane" + axis + (mul < 0 ? "n" : "p"), {size: 2}, scene);

    plane.material = matp.clone("matp" + axis);

    plane.position[axis] = mul;

    if (axis == 'x') plane.rotation.y = -Math.PI/2 * mul;
    if (axis == 'y') plane.rotation.x = Math.PI/2 * mul;
    if (axis == 'z' && mul > 0) plane.rotation.y = Math.PI * mul;

    // ステンシル有効化
    plane.material.stencil.enabled = true;

    // ステンシルバッファに `funcRef` で指定した値（stencilRef）を設定
    plane.material.stencil.opStencilDepthPass = BABYLON.Engine.REPLACE;

    // 今回のサンプルでは特に意味はないはず
    plane.material.stencil.mask = 0xFF;

    // 無条件にステンシルテストを合格させる
    plane.material.stencil.func = BABYLON.Engine.ALWAYS;

    // ステンシルバッファに書き込む値（とステンシルテスト合格）の基準値を設定
    plane.material.stencil.funcRef = stencilRef;
};
```

コードの上半分は平面をどの向きでどの場所に配置するかを指定しています。今回重要なのは`plane.material.stencil`を指定している部分です。何をしているかというとステンシルバッファというものに書き込みする方法の指定を行っています。以下の図は説明のために`makePlane("x", 3)`のみ表示させたものです。


![レンダリンググループ0.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/8a2bd743-b475-e1e0-db9d-8883afeadfc2.jpeg)

平面の表示については特別なことをしているわけではなく、通常通り表示させているだけです。
重要なのはステンシルバッファです。平面が表示された部分のピクセルについて、ステンシルバッファに`3`を書き込んでいます。レンダリンググループ1以降はこのステンシルバッファを参照することで表示の制御を行っています。

## レンダリンググループ1 : `sphereIntersect`の描画

次にレンダリングされるのは`sphereIntersect`（表示制御用の半球）です。描画している部分のコードは以下です。

```js
// レンダリンググループ間でステンシルバッファをクリアしない設定
scene.setRenderingAutoClearDepthStencil(1, false, false, false);

// sphereIntersect自体の表示はしない（次のsphereの表示制御に使用する）
mat0.disableColorWrite = true;

// 物体の奥にあるものほど表示されるように設定
mat0.depthFunction = BABYLON.Engine.GEQUAL;

// ...

const makeSphereIntersect = (axis, stencilRef) => {
    // 表示制御用の半球の作成と配置場所の設定
    var mul = axis.charAt(0) == '-' ? -1 : 1;
    if (mul < 0) axis = axis.substring(1);

    var sphereIntersect = BABYLON.MeshBuilder.CreateSphere("sphere" + axis + (mul < 0 ? "n" : "p"), { diameter:1, segments: 16, arc: 0.5 }, scene);

    sphereIntersect.position[axis] = mul;
    sphereIntersect.material = mat0.clone("mat0" + axis);
    sphereIntersect.renderingGroupId = 1;

    if (axis == 'x') sphereIntersect.rotation.y = Math.PI/2 * mul;
    if (axis == 'y') sphereIntersect.rotation.x = -Math.PI/2 * mul;
    if (axis == 'z' && mul < 0) sphereIntersect.rotation.y = Math.PI;
    
    // ステンシル有効化
    sphereIntersect.material.stencil.enabled = true;

    // ステンシルテストが合格したピクセルについてステンシルバッファを `funcRef -1` に置き換える
    sphereIntersect.material.stencil.opStencilDepthPass = BABYLON.Engine.DECR;

    // ステンシルバッファが  `funcRef` で指定した値（stencilRef）と同じであればステンシルテスト合格
    sphereIntersect.material.stencil.func = BABYLON.Engine.EQUAL;

    // ステンシルバッファに書き込む値とステンシルテスト合格の基準値を設定
    sphereIntersect.material.stencil.funcRef = stencilRef;
};
```

まず、`depthFunction = BABYLON.Engine.GEQUAL`の設定をすることで物体の奥側にあるものほど表示するように設定しています。また、ステンシルテストの条件により、指定した壁を通さないと`sphereIntersect`が見えないようにしています。
これにより、奥側にあるものほど表示され、指定の平面を通さないと見えない半球がレンダリングされます。ただ、`disableColorWrite = true`の設定で表示はされないようになっています。

説明用に`sphereIntersect`を表示しているものが以下です。同じ方向にある平面からしか半球は見えません。
[コード](https://playground.babylonjs.com/#P0JCPI#2)

![レンダリンググループ1_intersect.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/1b144ddb-fea3-5b85-b835-358de53f99eb.jpeg)

ステンシルバッファの値は`sphereIntersect`が描画されたピクセルについて、元の値から1ずらしています（`BABYLON.Engine.DECR`）。これは次の`sphere`を描画するときに、平面と`sphereIntersect`とを区別するためです。

![レンダリンググループ1.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/b8ee4c54-e564-8e1f-4d4b-6034fbaabac1.jpeg)

## レンダリンググループ2 : `sphere`の描画

最後に`sphere`（穴を表現するための半球）のレンダリングです。描画している部分のコードは以下です。

```js
// レンダリンググループ間でステンシルバッファをクリアしない設定
scene.setRenderingAutoClearDepthStencil(2, false, false, false);

// 物体の奥にあるものほど表示されるように設定
mat1.depthFunction = BABYLON.Engine.GEQUAL;

// ...

const makeSphere = (axis, stencilRef) => {
    // 穴の表現をする半球の作成と配置場所の設定
    var mul = axis.charAt(0) == '-' ? -1 : 1;
    if (mul < 0) axis = axis.substring(1);

    // 球の内側が見える設定 `sideOrientation: BABYLON.Mesh.BACKSIDE`
    var sphere = BABYLON.MeshBuilder.CreateSphere("sphere" + axis + (mul < 0 ? "n" : "p"), { diameter:1, segments: 16, arc: 0.5, sideOrientation: BABYLON.Mesh.BACKSIDE }, scene);
    
    sphere.position[axis] = mul;
    sphere.material = mat1.clone("mat1" + axis);
    sphere.renderingGroupId = 2;

    if (axis == 'x') sphere.rotation.y = Math.PI/2 * mul;
    if (axis == 'y') sphere.rotation.x = -Math.PI/2 * mul;
    if (axis == 'z' && mul < 0) sphere.rotation.y = Math.PI;

    // ステンシルを有効化
    sphere.material.stencil.enabled = true;

    // 今回のサンプルでは特に意味はないはず
    sphere.material.stencil.mask = 0x0;
 
    // ステンシルバッファが  `funcRef` で指定した値（stencilRef）と同じであればステンシルテスト合格
    sphere.material.stencil.func = BABYLON.Engine.EQUAL;
    
    // （ステンシルバッファに書き込む値と）ステンシルテスト合格の基準値を設定
    sphere.material.stencil.funcRef = stencilRef;
};
```

`sphereIntersect`と同様に、奥側にあるほど表示され、指定の平面を通さないと表示されないように設定されています。
`sphereIntersect`のときと異なるのは、`sphereIntersect`を表示している部分だけは、ステンシルバッファの値が異なっているということです（平面が`3`、半球の外側が`2`）。
これによって半球の外側部分が表示されなくなるため、平面に穴が空いているような表現をすることができます。

![レンダリンググループ2.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/d7403197-347b-a76a-7d61-57f8cc4917ab.jpeg)

図は一つの面だけですが、これを6面行うことで立方体に穴が空いた表現ができて、MaterialStencilStateのサンプルコードのようになります。

# まとめ

Babylon.jsのMaterialStencilStateの[サンプルコード](https://playground.babylonjs.com/#CW5PRI#10)の解読をしました。
ステンシルバッファはうまく使いこなすといろんな表現ができそうですね。

ちなみに、シェーダーの知識があるわけでもなく、ステンシルバッファのこともよくわかっていない状態で解読し始めたのもあって難しかったです。その上、このサンプルだと奥行方向の描画を制御していたりと複数の要素が絡んでいて、最初は何が何やらの状態でした。でも楽しかったです。
そんなわけなので間違っている説明はあるかも？

# 補足

なんとなく補足です。自分で解読しているときに思ったこととかを。

## 内部にある球が見えればいいのであればステンシルいらないのでは？

ステンシルがないとこうなります。

[コード](https://playground.babylonjs.com/#P0JCPI#3)
![ステンシルなし.JPG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/8b959146-87b1-6af1-ca2e-c4240736c550.jpeg)

ステンシルは、同一面からのみ半球を見えるようにするために必要なわけですね。ステンシルがないとどの面からでも見えるため、上記のようになります。

## なんで`stencilRef`を奇数に設定しているの？

下記のように`stencilRef`の値を3, 5, 7, ...としています。

```js
makePlane("x", 3);
makePlane("-x", 5);
makePlane("-z", 7);
makePlane("z", 9);
makePlane("y", 11);
makePlane("-y", 13);
```

その理由は以下です。
別々の数字にするのは面と球をペアにする必要があるからです（同一面からのみ半球を見えるようにしたいので）。
奇数にするのは`sphereIntersect`でのステンシルバッファの書き込みで値に`-1`をするためです。たとえば`makePlane("x", 3)`であれば`+x`の面については、2と3の値を使用することになります。他の面と使用する値をかぶらないようにするため、値を一つ置きにしています。


実際に3, 4, 5, ... の連番にするとこうなります。わかりにくいですが、奥の穴が微妙に見えてしまっています。

[コード](https://playground.babylonjs.com/#P0JCPI#4)
![連番.JPG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/52deb580-f749-aee3-b716-135a321e3e28.jpeg)

# 参考

本文内にも同様のリンクはありますが。一応まとめて。

https://doc.babylonjs.com/typedoc/classes/BABYLON.MaterialStencilState

https://zenn.dev/kento_o/articles/dd99c6c9e98d4a

https://nn-hokuson.hatenablog.com/entry/2017/05/02/185320

https://wgld.org/d/webgl/w038.html

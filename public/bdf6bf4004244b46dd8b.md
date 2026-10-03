---
title: Babylon.jsでシーンを上から俯瞰する
tags:
  - Babylon.js
private: false
updated_at: '2022-12-16T00:16:54+09:00'
id: bdf6bf4004244b46dd8b
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
この記事は[Babylon.js Advent Calendar 2022](https://qiita.com/advent-calendar/2022/babylonjs)の16日目の記事です。

# はじめに

3Dワールドを探索するのって楽しいですよね。広いワールド上を自由に動き回ったり、色んな場所を旅したり、素敵な世界観であれば何をするでもなく適当に歩き回るだけでも時間が無限に潰せてしまいます。
でもあんまり広いと自分がどこにいるかよくわからなくなったりします。方向音痴はつらいです。俯瞰してマップ全体を見られるといいですよね。ゲームでもよくマップ表示とかあると思います。

そんなわけでお手軽にシーンを俯瞰しようと思います。

# できたもの

俯瞰しました。コードは[こちら](https://playground.babylonjs.com/#GA4J1D#3)
![minimap.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/5f13e9fd-8860-238f-33d5-dbbe372cd9f3.png)

# 解説

今回、[公式ドキュメント](https://doc.babylonjs.com/features/featuresDeepDive/cameras/customizingCameraInputs)にあった[Walk and Look Camera Example](https://playground.babylonjs.com/#CTCSWQ#945)をベースにして作成しました。
このサンプルだと一人称視点と三人称視点の2つの視点を表示していますが、これを一人称視点と俯瞰視点にしていきます。

## ステージを作る

ステージは[Walk and Look Camera Example](https://playground.babylonjs.com/#CTCSWQ#945)をそのまま使いました。
元のサンプルはカメラ設定をいろいろやっているのでそれを除いてステージ作成のみにしたものが[こちら](https://playground.babylonjs.com/#GA4J1D)。WASDで移動できるようにしています。

## 俯瞰用のカメラを追加する

俯瞰するのに平行投影カメラを使用しました。透視投影（通常のカメラ）は遠くにあるものは小さく、近くにあるものは大きく描画します。それに対して平行投影は、遠近感をなくして物体を描画します。図面のように物体のサイズ比較をしたいときなどに使われます。

透視投影と平行投影を比較してみると下記画像のようになります。左が透視投影で右が平行投影です。透視投影だと遠くの箱が小さく見えるのに対して、平行投影だとすべて同じ大きさに描画されています。
（ちなみに下記画像のコードは[こちら](https://playground.babylonjs.com/#M5YGFQ)にあります。）

![透視投影と平行投影.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/14cc5c05-5db1-8008-099a-20a89cdb4067.png)

そして、Babylon.jsでカメラを平行投影に設定するには下記のようにカメラの `mode` を `ORTHOGRAPHIC_CAMERA` に、`orthoLeft`, `orthoRight`, `orthoTop`, `orthoBottom` のパラメータを設定して、どの領域をカメラに映すのかを指定する必要があります。
下記の例だと幅を60にして、高さはアスペクト比が合うようにカメラ領域を指定しています。

```js
const cameraOrt = new BABYLON.ArcRotateCamera("Camera", 0, 0, 100, new BABYLON.Vector3(0, 0, 0), scene);
cameraOrt.mode = BABYLON.Camera.ORTHOGRAPHIC_CAMERA;
const distance = 60;
const ratio = canvas.height / canvas.width;
cameraOrt.orthoLeft = -distance / 2;
cameraOrt.orthoRight = distance / 2;
cameraOrt.orthoTop = cameraOrt.orthoRight * ratio;
cameraOrt.orthoBottom = cameraOrt.orthoLeft * ratio;
```

この平行投影カメラを使って、俯瞰用のカメラを追加したものが[こちら](https://playground.babylonjs.com/#GA4J1D#1)です。ミニマップみたく右上に表示してみました。


## 自分の位置を表示する

自分がどこにいるのかわかるようにミニマップにコーンを表示します。自分の位置（カメラの位置）にコーンを追加したものが[こちら](https://playground.babylonjs.com/#GA4J1D#2)です。
このとき、自分より上に屋根などのものがあってもミニマップ上に表示されるように、カメラの位置その場所ではなく、カメラの上空にコーンが来るようにします。下記のようにすることで、自分（カメラ）の上にコーンが表示されます。

```js
const cone = BABYLON.MeshBuilder.CreateCylinder("dummyCamera", { diameterTop: 0.1, diameterBottom: 2, height: 2 }, scene);
const mat = new BABYLON.StandardMaterial("coneMat");
mat.diffuseColor = new BABYLON.Color3(1, 0, 0)
cone.material = mat
cone.onBeforeRenderObservable.add(() => {
    cone.position.x = camera.position.x
    cone.position.y = 50;
    cone.position.z = camera.position.z
    cone.rotation.x = camera.rotation.x + Math.PI / 2;
    cone.rotation.y = camera.rotation.y
    cone.rotation.z = camera.rotation.z
});
```

## 一人称視点でコーンを非表示にする

俯瞰視点では自分の位置がわかるようにコーンを表示したいですが、一人称視点ではコーンは表示したくありません。先程の状態だと上を見ると丸い謎物体が見えてしまう状態です。
そこで一人称視点からコーンを削除するために下記のように `layerMask` を設定します。
一人称視点からはコーン以外を表示するように、カメラとコーン以外のメッシュ（今回の場合 `box` と `ground`）に対して`layerMask = 0x10000000` を設定し、平行投影のカメラにはすべてのメッシュを表示させたいので `layerMask = 0xFFFFFFFF` を設定します。これで一人称視点からコーンが表示されなくなります。

```js
box.layerMask = 0x10000000;
ground.layerMask = 0x10000000;
camera.layerMask = 0x10000000;
cameraOrt.layerMask = 0xFFFFFFFF;
```

そうして出来上がったものが[こちら](https://playground.babylonjs.com/#GA4J1D#3)になります。

# まとめ

平行投影カメラを使用することでシーンを俯瞰できるミニマップを作成しました。これで迷子にならないね！
ちなみに今回は常時ミニマップで表示させるようにしましたが、キーボード入力などで一人称視点と俯瞰視点を切り替えたりとかもできると思います。

# 参考

- [Customizing Camera Inputs](https://doc.babylonjs.com/features/featuresDeepDive/cameras/customizingCameraInputs)
    - [Walk and Look Camera Example](https://playground.babylonjs.com/#CTCSWQ#945) : 今回の参考元
- [Top view draggable orthographic Camera](https://forum.babylonjs.com/t/top-view-draggable-orthographic-camera/4309/6)
    - [Orthographic zoom demo](https://playground.babylonjs.com/#EBPQH9#1) : 平行投影
- [MultiViews Part 2](https://doc.babylonjs.com/features/featuresDeepDive/cameras/multiViewsPart2) : カメラを複数表示する
- [Layer Masks and Multi-Cam Textures](https://doc.babylonjs.com/features/featuresDeepDive/cameras/layerMasksAndMultiCam) ：レイヤーでメッシュの表示設定する
- [Picture in Picture Visual Camera](https://playground.babylonjs.com/#L92PHY#217) ： 
    - この記事書いてる途中で見つけたもの。同じようにミニマップで上から視点を表示したりレイヤーで表示の制御をしているよう。

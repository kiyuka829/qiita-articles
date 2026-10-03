---
title: Babylon.jsで360パノラマ画像ツアー
tags:
  - JavaScript
  - Babylon.js
  - '360'
  - panorama
private: false
updated_at: '2022-08-15T02:49:41+09:00'
id: 614809be864aff20a632
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

Babylon.jsで360度パノラマ画像を表示させて、画像間を移動できるようにしました。

パノラマ画像を扱うライブラリとして、[Pannellum](https://pannellum.org/)とか[krpano](https://krpano.com/home/)とか[Panolens.js](https://pchen66.github.io/Panolens/)とかもあるので、Babylon.jsでやる意味があるかというとなんとも言えませんが、せっかく作ったのでまとめます。

作ったものは[こちら](https://playground.babylonjs.com/#IIES35#1)

# 処理

処理全体としては以下のようになっています。
ちなみにカメラの初期方向設定をカメラ作成時（`new BABYLON.ArcRotateCamera`）にやろうとすると、なぜか画像が思った方向に向きません（第二引数を「Math.PI/2」にしても「-Math.PI/2」にしても結果が変わらず、0にすると変わるけど想定とは違う結果に...）。
そのため、初期表示時に特定の方向を向かせたい場合は、360度画像設置後に実施する必要があるようです。

```js
const createScene = () => {
  const scene = new BABYLON.Scene(engine);
  
  // メインカメラ
  const camera = new BABYLON.ArcRotateCamera("Camera", Math.PI, Math.PI / 2, 250, BABYLON.Vector3.Zero(), scene);
  camera.attachControl(canvas, true);
  camera.inputs.attached.mousewheel.detachControl(canvas);
  
  // 俯瞰用のカメラ
  const camera2 = new BABYLON.ArcRotateCamera("Camera", -Math.PI / 2, Math.PI / 2, 2500, BABYLON.Vector3.Zero(0, 0, 0), scene);
  camera2.attachControl(canvas, true);

  // 360度画像設置
  const dome1 = create360photo(scene, 'pano1', "./textures/equirectangular.jpg", new BABYLON.Vector3(0, 0, -1000));
  const dome2 = create360photo(scene, 'pano2', "./textures/GatonaParkWalkway1_Panorama_4Kx2K.jpg", new BABYLON.Vector3(0, 0, 1000));

  // カメラの初期方向設定（360度画像設置に設定しないと方向がおかしい）
  camera.alpha = -Math.PI / 2;
  
  // 移動用のボタン作成
  const manager = new BABYLON.GUI.GUI3DManager(scene);
  createMoveButton(manager, `move to area2`, dome1, dome2, camera);
  createMoveButton(manager, `move to area1`, dome2, dome1, camera);

  // カメラ初期位置設定
  moveDome(camera, dome1);

  // GUI作成
  createGUI(scene, camera, camera2);

  return scene;
}
```

## 360度画像設置

[公式ドキュメント](https://doc.babylonjs.com/divingDeeper/environment/360PhotoDome)を参考にしてほとんどそのままです。設置位置を指定できるようにと、画像の向き指定をできるようにしています。

```js
const create360photo = (scene, name, textureUrlOrElement, position, rotate=0) => {
  const dome = new BABYLON.PhotoDome(
    name, textureUrlOrElement,
    {
      resolution: 32,
      size: 1000
    },
    scene
  );
  dome.position = position;
  dome.mesh.rotation.y = rotate;
  return dome;
}
```

## 移動用のボタン設置

360度画像間を移動するためのボタンを設置します。
下記では設置済みの画像の位置関係をもとに自動でボタンを配置しています。そのため、360度画像の位置と向きは移動方向との整合性が取れるように設置しておく必要があります。

```js
const createMoveButton = (manager, name, domeSrc, domeDst, camera) => {
  const button = new BABYLON.GUI.HolographicButton(name);

  // ボタンの回転設定に必要
  manager.addControl(button);

  const pos = domeDst.position.subtract(domeSrc.position);
  const theta = Math.acos(pos.y / (Math.sqrt(pos.x * pos.x + pos.y * pos.y + pos.z * pos.z)));
  const phi = Math.atan2(pos.z, pos.x)
  const degreeY = theta * 180 / Math.PI;
  const degreeX = phi * 180 / Math.PI;

  const r = 490;
  const x = r * Math.sin(theta) * Math.cos(phi);
  const z = r * Math.sin(theta) * Math.sin(phi);
  const y = r * Math.cos(theta);

  button.scaling.x = 100;
  button.scaling.y = 100;
  button.position.x = x;
  button.position.y = y;
  button.position.z = z;
  button.mesh.rotation.x = (degreeY - 90) * Math.PI / 180;
  button.mesh.rotation.y = (90 - degreeX) * Math.PI / 180;
  button.position = button.position.add(domeSrc.position);

  // テキスト設定
  const text = new BABYLON.GUI.TextBlock();
  text.text = `${name}\nx, y, z = ${x.toFixed()}, ${y.toFixed()}, ${z.toFixed()}`;
  text.color = "white";
  text.fontSize = 28;
  button.content = text;

  // ボタン押下時にカメラ移動
  button.onPointerUpObservable.add(() => moveDome(camera, domeDst));

  return button;
}

const moveDome = (camera, dome) => {
  const alpha = camera.alpha;
  const beta = camera.beta;
  const radius = camera.radius;
  camera.setTarget(dome.position);
  camera.alpha = alpha;
  camera.beta = beta;
  camera.radius = radius;
  camera.radius = 250;
}
```

## カメラ変更用ボタン設置

俯瞰で360度画像を見るとおもしろかったので、俯瞰カメラと360度画像を見る用のカメラを切り替えるボタンを作成します。

```js
const createGUI = (scene, camera, camera2) => {
  const advancedTexture = BABYLON.GUI.AdvancedDynamicTexture.CreateFullscreenUI("UI");
  const buttonExit = BABYLON.GUI.Button.CreateSimpleButton("exit", "Exit");
  buttonExit.width = "120px";
  buttonExit.height = "40px";
  buttonExit.color = "white";
  buttonExit.cornerRadius = 20;
  buttonExit.background = "green";
  buttonExit.horizontalAlignment = 0;
  buttonExit.verticalAlignment = 0;
  buttonExit.paddingTop = "10px";
  buttonExit.paddingLeft = "10px";
  buttonExit.onPointerUpObservable.add(function() {
      scene.activeCamera = camera2;
  });
  advancedTexture.addControl(buttonExit);
  const buttonEnter = BABYLON.GUI.Button.CreateSimpleButton("enter", "Enter");
  buttonEnter.width = "120px";
  buttonEnter.height = "80px";
  buttonEnter.color = "white";
  buttonEnter.cornerRadius = 20;
  buttonEnter.background = "green";
  buttonEnter.horizontalAlignment = 0;
  buttonEnter.verticalAlignment = 0;
  buttonEnter.paddingTop = "50px";
  buttonEnter.paddingLeft = "10px";
  buttonEnter.onPointerUpObservable.add(function() {
      scene.activeCamera = camera;
  });
  advancedTexture.addControl(buttonEnter);
}
```

## できあがり

こんな感じに見れます。俯瞰で見ると一般的な360度画像と違う感じで見えて楽しいですね。

https://twitter.com/kiyuka_study/status/1556646478533529601

# まとめ

Babylon.jsで360パノラマ画像ツアーをできるようにしました。

ただ今回の作ったものは最初にすべての画像を読み込もうとするので、数枚のパノラマ画像であれば問題ないのですが、画像が多くなると読み込みに時間がかかってしまいます。そのため、遅延読み込みをする必要があるかもしれません。

# 参考

- 公式ドキュメント
    - [360 Photo Domes](https://doc.babylonjs.com/divingDeeper/environment/360PhotoDome)
    - [Babylon 3D GUI](https://doc.babylonjs.com/divingDeeper/gui/gui3D)
    - [The Babylon GUI](https://doc.babylonjs.com/divingDeeper/gui/gui)
- [Babylon.jsで360度画像を回転させる方法](https://www.crossroad-tech.com/entry/babylonjs-photodome-rotate)
- [極座標への変換](https://science.shinshu-u.ac.jp/~tiiyama/?page_id=4311)

---
title: 世界を闇で塗りつぶす【Babylon.js】
tags:
  - Babylon.js
  - PLATEAU
private: false
updated_at: '2023-12-21T07:31:28+09:00'
id: d8d4503d05f73597d5fa
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
この記事は[Babylon.js Advent Calendar 2023](https://qiita.com/advent-calendar/2023/babylonjs)の21日目の記事です。

# はじめに

ああ、もう嫌だ。こんな世界、黒く、暗く、すべてを闇で塗りつぶしてしまえれば...！！

そんなふうに思うときってありますよね？左目の魔眼が疼きだしたり、右腕に封印されし邪龍が暴れ始めたり、闇の力ですべてを無に帰してしまいたい...そんなときがあると思います。そういうときはその衝動に任せて世界を闇で飲み込んでしまいましょう！！

そんなわけでBabylon.jsで世界を闇で飲み込みます。

# 闇に飲まれよ！

あははは！やった！やってやったぞ！！

https://x.com/kiyuka_study/status/1737465142332502393?s=20

<details><summary>動かしたコード（長いので折りたたみ）</summary>


```js
const createScene = () => {
  const scene = new BABYLON.Scene(engine);

  // カメラの設定
  const camera = new BABYLON.ArcRotateCamera(
    "camera",
    -2,
    0.9,
    1000,
    new BABYLON.Vector3(0, 0, 0)
  );
  camera.attachControl(canvas, true);

  // ライトの設定
  const light = new BABYLON.HemisphericLight(
    "light",
    new BABYLON.Vector3(200, 500, 100)
  );
  light.intensity = 7;
  const light2 = new BABYLON.HemisphericLight(
    "light2",
    new BABYLON.Vector3(-100, 300, -200)
  );
  light2.intensity = 7;

  // レンダリンググループの設定
  scene.setRenderingAutoClearDepthStencil(1, false);
  scene.setRenderingAutoClearDepthStencil(2, false);

  // マテリアル設定
  const holeTexture = new BABYLON.Texture("textures/dark.jpg", scene);

  const mat0 = new BABYLON.StandardMaterial("mat0", scene);
  mat0.disableColorWrite = true;
  mat0.depthFunction = BABYLON.Engine.GEQUAL;

  const mat1 = new BABYLON.StandardMaterial("mat1", scene);
  mat1.diffuseTexture = holeTexture;
  mat1.depthFunction = BABYLON.Engine.GEQUAL;
  mat1.specularColor = BABYLON.Color3.Black();

  const texture = new BABYLON.StandardMaterial("texture", scene);
  texture.diffuseTexture = holeTexture;
  texture.specularColor = BABYLON.Color3.Black();

  // 球体サイズ
  const sphereSize = 200;

  // モデル読み込み
  BABYLON.SceneLoader.ImportMeshAsync("", "", "tokyo.glb").then((result) => {
    const meshes = result.meshes;
    meshes.forEach((mesh) => {
      // ステンシル設定
      if (mesh.material) {
        mesh.material.stencil.enabled = true;
        mesh.material.stencil.opStencilDepthPass = BABYLON.Engine.REPLACE;
        mesh.material.stencil.func = BABYLON.Engine.ALWAYS;
        mesh.material.stencil.funcRef = 2;
      }

      // メッシュに対してクリックイベントを設定
      mesh.actionManager = new BABYLON.ActionManager(scene);
      mesh.actionManager.registerAction(
        new BABYLON.ExecuteCodeAction(
          BABYLON.ActionManager.OnPickTrigger,
          function (evt) {
            const pickResult = scene.pick(scene.pointerX, scene.pointerY);
            addSphere(pickResult.pickedPoint, sphereSize, mat0, mat1, texture);
          }
        )
      );
    });
  });

  return scene;
};

const addSphere = (point, sphereSize, mat0, mat1, texture) => {
  const sphereIntersect = BABYLON.MeshBuilder.CreateSphere(
    "sphere",
    { diameter: sphereSize },
    scene
  );
  sphereIntersect.position = point;
  sphereIntersect.material = mat0;
  sphereIntersect.renderingGroupId = 1;
  sphereIntersect.material.stencil.enabled = true;
  sphereIntersect.material.stencil.opStencilDepthPass = BABYLON.Engine.DECR;
  sphereIntersect.material.stencil.func = BABYLON.Engine.EQUAL;
  sphereIntersect.material.stencil.funcRef = 2;

  const sphere = BABYLON.MeshBuilder.CreateSphere(
    "sphere",
    { diameter: sphereSize, sideOrientation: BABYLON.Mesh.BACKSIDE },
    scene
  );
  sphere.position = point;
  sphere.material = mat1;
  sphere.renderingGroupId = 2;
  sphere.material.stencil.enabled = true;
  sphere.material.stencil.func = BABYLON.Engine.EQUAL;
  sphere.material.stencil.funcRef = 2;

  addRotateSphere(point, sphereSize, texture);
};

const addRotateSphere = (position, sphereSize, texture) => {
  // 球体の作成
  const sphere = BABYLON.MeshBuilder.CreateSphere(
    "sphere",
    { diameter: sphereSize },
    scene
  );
  sphere.position = position;
  sphere.renderingGroupId = 0;

  // テクスチャの適用
  sphere.material = texture;

  // アニメーションの作成
  const frameRate = 10;

  // 回転アニメーション
  const rotateAnimation = new BABYLON.Animation(
    "rotateAnimation",
    "rotation.y",
    frameRate,
    BABYLON.Animation.ANIMATIONTYPE_FLOAT,
    BABYLON.Animation.ANIMATIONLOOPMODE_CYCLE
  );
  const rotateKeys = [];
  rotateKeys.push({ frame: 0, value: 0 });
  rotateKeys.push({ frame: frameRate * 1, value: Math.PI * 4 });
  rotateAnimation.setKeys(rotateKeys);

  // スケールアニメーション（小さくなる）
  const scaleAnimation = new BABYLON.Animation(
    "scaleAnimation",
    "scaling",
    frameRate,
    BABYLON.Animation.ANIMATIONTYPE_VECTOR3,
    BABYLON.Animation.ANIMATIONLOOPMODE_CYCLE
  );
  const scaleKeys = [];
  scaleKeys.push({ frame: 0, value: new BABYLON.Vector3(1, 1, 1) });
  scaleKeys.push({
    frame: frameRate * 0.5,
    value: new BABYLON.Vector3(0, 0, 0),
  });
  scaleAnimation.setKeys(scaleKeys);

  // アニメーションを球体に適用
  sphere.animations.push(rotateAnimation);
  sphere.animations.push(scaleAnimation);

  // アニメーションの実行と完了後の処理
  scene.beginAnimation(sphere, 0, frameRate * 0.5, false, 1.0, () => {
    // アニメーションが完了したら球体を削除
    sphere.dispose();
  });
};
```

</details>


モデルや実装が若干違うけど[Playgroundで同じように動くコード](https://playground.babylonjs.com/#GSFGIM#4)。


# 簡単な解説

やったことはざっくりこんな感じ

- 街のモデルはPLATEAUを使用
- PLATEAUのデータをglb形式に変換
- Babylon.jsで読み込んで、メッシュにクリックイベント追加
- クリックした場所に球を配置して、回転しながら消えるアニメーション
- 球にステンシルバッファを使用することで穴が開いているような表現に

PLATEAUのデータ変換については以下の記事を参考にしました。

https://www.crossroad-tech.com/entry/PLATEAU-2022-Blender


そしてステンシルバッファについては、Babylon.jsのドキュメントのあった[サンプル](https://playground.babylonjs.com/#CW5PRI#10)をおおよそそのまま使っています。このサンプルが何をしているかは、[以前の記事](https://qiita.com/kiyuka/items/1c0a9cd0545efd91c7b7)に書いているので、そちらを参照してもらえれば。

# 実はハリボテ

実は角度を変えて見るとおかしいです。複数の穴が重なるような視点から見た場合、今回のステンシルバッファの設定の仕方だと、穴が見えずに建物のほうが見えてしまっています。

![ハリボテ.JPG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/b9055458-7b75-5ea0-bb12-11aed50d6a69.jpeg)


工夫してどうにかできないかと思ったのですが、今回はこれで妥協しました。

# 球を大きくすると

ステンシルで穴っぽく表現しているだけで、実際は穴が空いていわけではありません。
そのため、球のサイズを大きくしてメッシュ全体を覆うようにすることで、こういうこともできます。

https://x.com/kiyuka_study/status/1737468752864723153?s=20

これはこれで街が不思議空間になって面白いですね。

# まとめ

Babylon.jsでステンシルバッファを使用して、やみのま！しました。
3Dでの表現方法って色々あって楽しいですね。

ただ、視点を変えるとおかしくなるので、もっとうまいやり方があったのかもしれません。
しかし、我と共鳴せし堕ちた精霊が、それでもいいから記事を書けと囁くから仕方なかろう。...ごめんなさい許してくださいネタっぽい記事を書きたかったんです><


# 参考

https://www.crossroad-tech.com/entry/PLATEAU-2022-Blender

https://project-plateau.github.io/PLATEAU-SDK-for-Unity/index.html

---
title: IFC.js x Babylon.js で家を建てる
tags:
  - Babylon.js
  - IFC.js
private: false
updated_at: '2023-07-30T22:12:05+09:00'
id: 2722b524d8ee6d9b3860
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
<iframe width="560" height="315" src="https://www.youtube.com/embed/fuXY4eaQZ8c" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

# はじめに

IFC.jsは、IFCファイルを読み込んでブラウザ上でモデルを表示させることができます。
また、 以下の3つのレイヤーで構成されています。

- `web-ifc` - IFCファイルのパーサー
- `web-ifc-three` - `web-ifc`でパースした結果をThree.jsで表示させるビューア
- `web-ifc-viewer` - `web-ifc-three`に建物を操作する様々な機能が実装されているビューア

このようにレイヤーが分かれているため、とにかくさっと建物の操作をしたいのであれば`web-ifc-viewer` を、建物の操作を細かくカスタマイズしたいのであれば`web-ifc-three`を、Three.js以外の3Dライブラリを使用して表示したいのであれば`web-ifc`を、といった使い分けをすることができます。

公式ドキュメントにも

> IFC.jsが3Dシーンを生成できるのは、Three.jsやBabylon.jsなどの3Dライブラリに対応しているからです。つまり、3DのBIMツールをすぐに作ることができるのです。

とあるようにThree.js以外にもBabylon.jsでもIFCからモデルを表示することができる、との記載があります。
そんなわけで web-ifc と Babylon.js を使ってIFCのモデルを表示して、ついでに建築アニメーションっぽいことをします。

# できたもの

最終的にできたものはこんな感じです（トップの動画と同じもの）。
`web-ifc-three`などのビューアライブラリをそのまま使用すると、IFCを読み込んでメッシュにするところまでパッケージ化されているので、こういったアニメーションをさせるのは`web-ifc`を使用しての実装しないとできないのではないかなと思います。

https://youtu.be/fuXY4eaQZ8c


<details><summary>コード全文</summary>

```tsx
import React, { useState, useEffect, useRef } from 'react';
import * as BABYLON from '@babylonjs/core';
import * as WebIFC from 'web-ifc';
import './IFCViewer.css'

const IFCViewer = () => {
  const canvasRef = useRef(null);
  const [scene, setScene] = useState<BABYLON.Scene | null>(null);
  const ifcapi = new WebIFC.IfcAPI();
  ifcapi.SetWasmPath("../node_modules/web-ifc/");

  // 初期表示
  useEffect(() => {
    const canvas = canvasRef.current;
    const engine = new BABYLON.Engine(canvas, true);
    const scene = new BABYLON.Scene(engine);
    setScene(scene)

    const camera = new BABYLON.ArcRotateCamera("Camera", -Math.PI / 2, Math.PI / 2, 20, BABYLON.Vector3.Zero(), scene);
    camera.attachControl(canvas, true);
    camera.lowerRadiusLimit = 2
    const light1 = new BABYLON.HemisphericLight("light1", new BABYLON.Vector3(0, -100, 0), scene);
    light1

    // XYZ 軸
    const axisSize = 15;
    const xColor = new BABYLON.Color3(1, 0, 0);
    const yColor = new BABYLON.Color3(0, 1, 0);
    const zColor = new BABYLON.Color3(0, 0, 1);

    // X軸
    const xLine = BABYLON.MeshBuilder.CreateLines("xAxis", { points: [BABYLON.Vector3.Zero(), new BABYLON.Vector3(axisSize, 0, 0)] }, scene);
    xLine.color = xColor;

    // Y軸
    const yLine = BABYLON.MeshBuilder.CreateLines("yAxis", { points: [BABYLON.Vector3.Zero(), new BABYLON.Vector3(0, axisSize, 0)] }, scene);
    yLine.color = yColor;

    // Z軸
    const zLine = BABYLON.MeshBuilder.CreateLines("zAxis", { points: [BABYLON.Vector3.Zero(), new BABYLON.Vector3(0, 0, axisSize)] }, scene);
    zLine.color = zColor;

    engine.runRenderLoop(() => {
      scene.render();
    });

    window.addEventListener("resize", () => {
      engine.resize();
    });

    return () => {
      engine.dispose();
      scene.dispose();
    }
  }, []);

  // ファイル選択時の処理
  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = (event.target.files as FileList)[0];
    if (file) {
      loadIFCFile(file);
    }
  }

  // IFCファイルの読み込み
  function loadIFCFile(file: File) {
    const reader = new FileReader();
    reader.onload = async (event) => {
      const buffer = new Uint8Array(event.target?.result as ArrayBuffer)
      await ifcapi.Init();
      const modelID = ifcapi.OpenModel(buffer)
      // createMesh(modelID)

      // アニメーションさせる場合
      createMeshAnimation(modelID)
    };
    reader.readAsArrayBuffer(file);
  }

  // メッシュの作成
  function createMesh(modelID: number) {
    ifcapi.StreamAllMeshes(modelID, (mesh) => loadMesh(modelID, mesh))
  }

  // アニメーションをさせてメッシュを作成
  function createMeshAnimation(modelID: number) {
    if (scene === null) return

    // すべてのメッシュを同期取得
    let meshData = []
    const meshes = ifcapi.LoadAllGeometry(modelID)
    for (let i = 0; i < meshes.size(); i++) {
      const mesh = meshes.get(i)
      for(const geometry of loadGeometry(modelID, mesh)){
        meshData.push(geometry)
      }
    }

    // 表示順のソート設定
    meshData = meshData.map(v => {
      let posy = 100000
      for (let i = 0; i < v.vertexData.positions.length; i += 3) {
        posy = Math.min(posy, v.vertexData.positions[i + 2])
      }
      return { ...v, sortKey: v.flatTransformation[13] + posy }
    })
    meshData.sort((a, b) => a.sortKey - b.sortKey)

    // 10秒かけて表示されるように
    const msec = 10000 / meshData.length
    meshData.forEach((v, i) => {
      setTimeout(() => {
        ifc2babylonMesh(scene, v.vertexData, v.flatTransformation, v.color)
      }, msec * i);
    })
  }

  // IFCからメッシュの読み込み
  function loadMesh(modelID: number, mesh: WebIFC.FlatMesh) {
    if (scene === null) return;

    // IFCからBabylon.jsのメッシュを構築
    for(const geometry of loadGeometry(modelID, mesh)){
      ifc2babylonMesh(
        scene,
        geometry.vertexData,
        geometry.flatTransformation,
        geometry.color
      )
    }
  }

  // IFCからメッシュ情報を取得するジェネレータ
  function* loadGeometry(modelID: number, mesh: WebIFC.FlatMesh) {
    const placedGeometries = mesh.geometries;
    const size = placedGeometries.size();
    for (let i = 0; i < size; i++) {
      const placedGeometry = placedGeometries.get(i)
      const geometry = ifcapi.GetGeometry(modelID, placedGeometry.geometryExpressID);
      // 6つで一組のデータ： x, y, z, normalx, normaly, normalz
      const verts = ifcapi.GetVertexArray(geometry.GetVertexData(), geometry.GetVertexDataSize());
      // 3つで一組のデータ：頂点index 1, 2, 3
      const indices = ifcapi.GetIndexArray(geometry.GetIndexData(), geometry.GetIndexDataSize());

      // 頂点の座標と法線を分離
      const positions = [];
      const normals = [];
      for (let i = 0; i < verts.length; i += 6) {
        positions.push(verts[i], verts[i + 1], verts[i + 2]);
        normals.push(verts[i + 3], verts[i + 4], verts[i + 5]);
      }

      const vertexData = {
        positions: positions,
        normals: normals,
        indices: Array.from(indices),
      }

      // 頂点と変形行列と色情報を返す
      const geometoryData = {
        vertexData: vertexData,
        flatTransformation: placedGeometry.flatTransformation,
        color: placedGeometry.color,
      };

      yield geometoryData;
    }
  }

  // IFCの形状情報からBabylon.jsのメッシュを作成
  function ifc2babylonMesh(
    scene: BABYLON.Scene,
    vertexData: { positions: number[], normals: number[], indices: number[] },
    flatTransformation: number[],
    color: { x: number, y: number, z: number, w: number },
  ) {
    // メッシュ作成
    const mesh = createMeshFromData(scene, vertexData)

    // メッシュの移動・変形
    const transformationMatrix = BABYLON.Matrix.FromArray(flatTransformation);
    mesh.setPivotMatrix(transformationMatrix, false);

    // 奥行きZの左手系に
    mesh.scaling.z *= -1;

    // 面を反転
    mesh.flipFaces(true);

    // 色設定
    const { x, y, z, w } = color
    const material = new BABYLON.StandardMaterial("material", scene);
    material.diffuseColor = new BABYLON.Color3(x, y, z);
    material.alpha = w
    material.backFaceCulling = false;
    mesh.material = material;
  }

  // 頂点データ化からメッシュ作成
  function createMeshFromData(scene: BABYLON.Scene, vertexData: { positions: number[], normals: number[], indices: number[] }) {
    const mesh = new BABYLON.Mesh("mesh", scene);
    const vertexDataForBabylon = new BABYLON.VertexData();
    vertexDataForBabylon.positions = vertexData.positions;
    vertexDataForBabylon.normals = vertexData.normals;
    vertexDataForBabylon.indices = vertexData.indices;
    vertexDataForBabylon.applyToMesh(mesh);
    return mesh;
  }

  return (
    <>
      <input type="file" onChange={handleFileChange} className="fileInput" />
      <canvas className="fullScreenCanvas" ref={canvasRef} />
    </>
  )
}

export default IFCViewer;

```
</details>


# コード解説

Vite + React + TypeScript で実装しています。

## IFCを読み込む前の準備をする

IFCファイルを読み込む前にBabylon.jsのCanvasなどを準備します。やっていることは、以下です。

- Babylon.jsの準備：`useEffect` 内でCanvasの作成をしています
- wasm のパス指定：`ifcapi.SetWasmPath` には `web-ifc.wasm`の格納されているディレクトリを指定します。これによりブラウザ上で高速にIFCファイルのパースをすることができます。

HTMLにはファイル選択ダイアログとCanvasのみ作成しています。CSSは画面いっぱいに表示されるようにだけ指定しています。


```tsx
import React, { useState, useEffect, useRef } from 'react';
import * as BABYLON from '@babylonjs/core';
import * as WebIFC from 'web-ifc';
import './IFCViewer.css'

const IFCViewer = () => {
  const canvasRef = useRef(null);
  const [modelID, setModelID] = useState<number | null>(null)
  const [scene, setScene] = useState<BABYLON.Scene | null>(null);
  const ifcapi = new WebIFC.IfcAPI();
  ifcapi.SetWasmPath("../node_modules/web-ifc/");

  // 初期表示
  useEffect(() => {
    const canvas = canvasRef.current;
    const engine = new BABYLON.Engine(canvas, true);
    const scene = new BABYLON.Scene(engine);
    setScene(scene)

    const camera = new BABYLON.ArcRotateCamera("Camera", -Math.PI / 2, Math.PI / 2, 20, BABYLON.Vector3.Zero(), scene);
    camera.attachControl(canvas, true);
    camera.lowerRadiusLimit = 2
    const light1 = new BABYLON.HemisphericLight("light1", new BABYLON.Vector3(0, -100, 0), scene);

    engine.runRenderLoop(() => {
      scene.render();
    });

    window.addEventListener("resize", () => {
      engine.resize();
    });

    return () => {
      engine.dispose();
      scene.dispose();
    }
  }, []);

  // ここに読み込み処理とかいろいろ追加する

  return (
    <>
      <input type="file" onChange={handleFileChange} className="fileInput" />
      <canvas className="fullScreenCanvas" ref={canvasRef} />
    </>
  )
}

export default IFCViewer;
```

## IFCファイルを読み込む

ファイルを選択したときにIFCファイルを読み込みます。ここではファイルを開いているだけです。`createMesh`で読み込んだIFCファイルからメッシュを作成していきます。

```ts
  // ファイル選択時の処理
  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>){
    const file = (event.target.files as FileList)[0];
    if (file) {
      loadIFCFile(file);
    }
  }

  // IFCファイルの読み込み
  function loadIFCFile(file: File){
    const reader = new FileReader();
    reader.onload = async (event) => {
      const buffer = new Uint8Array(event.target?.result as ArrayBuffer)
      await ifcapi.Init();
      const modelID = ifcapi.OpenModel(buffer)
      createMesh(modelID)

      // アニメーションさせる場合
      // createMeshAnimation(modelID)
    };
    reader.readAsArrayBuffer(file);
  }
```

## 形状情報の読み取り

IFCから形状情報を読み取ります。処理は `web-ifc-three`を参考にして必要最小限だけ抜き出しています。
次はIFCの形状情報からBabylon.jsのメッシュを作成します。

```ts
  // メッシュの作成
  function createMesh(modelID : number){
    ifcapi.StreamAllMeshes(modelID, (mesh) => loadMesh(modelID, mesh))
  }

  // IFCからメッシュの読み込み
  function loadMesh(modelID: number, mesh: WebIFC.FlatMesh) {
    if (scene === null) return;

    // IFCからBabylon.jsのメッシュを構築
    for(const geometry of loadGeometry(modelID, mesh)){
      ifc2babylonMesh(
        scene,
        geometry.vertexData,
        geometry.flatTransformation,
        geometry.color
      )
    }
  }

  // IFCからメッシュ情報を取得するジェネレータ
  function* loadGeometry(modelID: number, mesh: WebIFC.FlatMesh) {
    const placedGeometries = mesh.geometries;
    const size = placedGeometries.size();
    for (let i = 0; i < size; i++) {
      const placedGeometry = placedGeometries.get(i)
      const geometry = ifcapi.GetGeometry(modelID, placedGeometry.geometryExpressID);
      // 6つで一組のデータ： x, y, z, normalx, normaly, normalz
      const verts = ifcapi.GetVertexArray(geometry.GetVertexData(), geometry.GetVertexDataSize());
      // 3つで一組のデータ：頂点index 1, 2, 3
      const indices = ifcapi.GetIndexArray(geometry.GetIndexData(), geometry.GetIndexDataSize());

      // 頂点の座標と法線を分離
      const positions = [];
      const normals = [];
      for (let i = 0; i < verts.length; i += 6) {
        positions.push(verts[i], verts[i + 1], verts[i + 2]);
        normals.push(verts[i + 3], verts[i + 4], verts[i + 5]);
      }

      const vertexData = {
        positions: positions,
        normals: normals,
        indices: Array.from(indices),
      }

      // 頂点と変形行列と色情報を返す
      const geometoryData = {
        vertexData: vertexData,
        flatTransformation: placedGeometry.flatTransformation,
        color: placedGeometry.color,
      };

      yield geometoryData;
    }
  }
```

## メッシュ作成

web-ifcより取得した形状情報からBabylon.jsのメッシュを作成します。コードをかんたんに解説すると、

- IFCの形状情報は三角形メッシュの頂点座標なので、`BABYLON.VertexData`を使用して頂点情報からメッシュを作成します。
- また、IFCでは形状情報と位置情報を別々に持っているため、変形行列を使用して正しい位置に移動させます。
- web-ifcで取得できるメッシュは右手系ですが、Babylon.jsは奥行きZの左手系なので、メッシュのZを反転させます。
- なぜかそのままだとメッシュの面が逆になる（左手系なため？）ので反転させて正しくします。
-  最後にメッシュの色を設定します

右手系・左手系の変換は、`ifcapi.SetGeometryTransformation` で事前に設定することでできると思われるのですが、何故かうまく行かなかったのでメッシュ作成後に無理やり変換しています。

```ts
  // IFCの形状情報からBabylon.jsのメッシュを作成
  function ifc2babylonMesh(
    scene: BABYLON.Scene,
    vertexData: { positions: number[], normals: number[], indices: number[] },
    flatTransformation: number[],
    color: {x: number, y: number, z: number, w: number},
  ){
    // メッシュ作成
    const mesh = createMeshFromData(scene, vertexData)

    // メッシュの移動・変形
    const transformationMatrix = BABYLON.Matrix.FromArray(flatTransformation);
    mesh.setPivotMatrix(transformationMatrix, false);

    // 奥行きZの右手系に
    mesh.scaling.z *= -1;

    // 面を反転
    mesh.flipFaces(true);

    // 色設定
    const {x, y, z, w} = color
    const material = new BABYLON.StandardMaterial("material", scene);
    material.diffuseColor = new BABYLON.Color3(x, y, z);
    material.alpha = w
    material.backFaceCulling = false;
    mesh.material = material;
  }

  // 頂点データ化からメッシュ作成
  function createMeshFromData(scene: BABYLON.Scene, vertexData: { positions: number[], normals: number[], indices: number[] }) {
    const mesh = new BABYLON.Mesh("mesh", scene);
    const vertexDataForBabylon = new BABYLON.VertexData();
    vertexDataForBabylon.positions = vertexData.positions;
    vertexDataForBabylon.normals = vertexData.normals;
    vertexDataForBabylon.indices = vertexData.indices;
    vertexDataForBabylon.applyToMesh(mesh);
    return mesh;
  }
```

ここまででIFCファイルからモデルを表示することができました。
![003_色付き_.PNG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/c1e19968-fa85-5eb4-5b2a-a9337d98cd4b.png)

## 建築っぽいアニメーションにする

最後にアニメーションをさせます。
単純にモデルを表示させたいだけなら、`ifcapi.StreamAllMeshes`を使って非同期に処理すれば可能です。しかし、アニメーションを行いたい場合は、`ifcapi.LoadAllGeometry`を使用して同期的にすべてのデータを取得し、その後に順番にメッシュを構築する必要があります。

- `ifcapi.LoadAllGeometry` でメッシュ情報をすべて取得し、Babylon.jsでメッシュ構築しやすい形式に変換
- 建築っぽく見せるため、下の方にあるメッシュから表示されるようにデータをソート
    - 実際はこのコードだとおかしいのだけれども、それっぽくなったので妥協
- アニメーションするように `setTimeout` で徐々にメッシュを構築

```ts
  // アニメーションをさせてメッシュを作成
  function createMeshAnimation(modelID: number) {
    if (scene === null) return

    // すべてのメッシュを同期取得
    let meshData = []
    const meshes = ifcapi.LoadAllGeometry(modelID)
    for (let i = 0; i < meshes.size(); i++) {
      const mesh = meshes.get(i)
      for(const geometry of loadGeometry(modelID, mesh)){
        meshData.push(geometry)
      }
    }

    // 表示順のソート設定
    meshData = meshData.map(v => {
      let posy = 100000
      for (let i = 0; i < v.vertexData.positions.length; i += 3) {
        posy = Math.min(posy, v.vertexData.positions[i + 2])
      }
      return { ...v, sortKey: v.flatTransformation[13] + posy }
    })
    meshData.sort((a, b) => a.sortKey - b.sortKey)

    // 10秒かけて表示されるように
    const msec = 10000 / meshData.length
    meshData.forEach((v, i) => {
      setTimeout(() => {
        ifc2babylonMesh(scene, v.vertexData, v.flatTransformation, v.color)
      }, msec * i);
    })
  }
```

こうすることでIFCファイルを読み込んだときに建築っぽいアニメーションが表示されます（再掲）

https://youtu.be/fuXY4eaQZ8c

# まとめ

IFCのモデルをBabylon.jsで建築アニメーションっぽく表示させました。

正直なところ公式実装の `web-ifc-three` を使うほうが賢い気もします。ただ、より細かな制御を行う場合は`web-ifc`を使用することが必要になってくると思うので、公式実装にないBabylon.jsで表示させることでその基礎部分の理解が深められたかなと思いました。

# 参考

- [IFC.js ドキュメント](https://ifcjs.github.io/info/ja/docs/Introduction/)
- [Create Custom Meshes From Scratch](https://doc.babylonjs.com/features/featuresDeepDive/mesh/creation/custom/custom)
    - Babylon.jsで頂点データからメッシュを構築する
- [web-ifc-babylon](https://www.npmjs.com/package/web-ifc-babylon)
    - 単に表示させるだけであればこのライブラリを使用するのがいいかも
- [AC20-FZK-Haus.ifc](https://www.ifcwiki.org/images/e/e3/AC20-FZK-Haus.ifc)
    - 使用したIFCファイル

---
title: 点群をBabylon.jsでボクセル表示する
tags:
  - Python
  - Babylon.js
  - PointCloud
  - 点群
private: false
updated_at: '2022-06-04T23:03:19+09:00'
id: f47f9a0e2df8225d6984
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---

![岸和田城ボクセル.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/949d0c34-833e-8806-3203-a7c14df92571.jpeg)

## はじめに

点群、最近流行ってますよね。iPhone LiDARで個人でもお手軽に取れるようになりました。
ただ、やっぱり広域スキャンされた点群は、データ量が大きいせいで見るだけでもPCスペックが求められてつらい。
ブラウザで閲覧できるとお手軽に見れていいですよね。というわけで、点群をボクセル化してブラウザで表示できたので、その手順を説明しようと思います。

点群データは「[岸和田城 3次元点群データ](https://www.geospatial.jp/ckan/dataset/kishiwada-castle) 」の「1.zip」を使わせていただきました。オープンデータありがたいですね。

## ボクセル表示するまでの流れ

実施した手順は以下となります

1. 点群データ`.las`を CloudCompare で間引いて `.csv` で出力
1. `.csv`ファイルをPythonでボクセル表示用にデータを変換し `.json`出力
1. Babylon.jsでボクセル表示

## CloudCompareで点群を間引く

まず点群をざっくり[CloudCompare](https://www.danielgm.net/cc/)で間引きました。元データの`.las`ファイルサイズが9GB、点の数が2.5億だったため、このままだと大きすぎて扱えないので密なデータを疎にします。
とにかく容量を減らせればいいのでパラメータは`Subsample > between points： 0.1` で行いました。
![subsampleパラメータ.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/8bf8429c-9879-bb72-3197-a54b4e31d400.png)


この間引いたデータを次にPythonで扱いたいので`.csv`形式で出力します。
出力時に `separator`を`comma`に、`columns title` にチェックを入れて出力しました。
![出力パラメータ.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/59778115-ea18-145f-ac91-8de85386c62b.png)


## Pythonでボクセル表示用に変換

どのくらいの間隔でボクセルを表示させたいのか、ボクセルサイズをどのくらいにするかを指定したいので、上記で出力したCSVファイルをPythonで処理します。
なるべく細かく表示させたいならボクセルサイズを小さめに、ざっくり表示でいいのであれば大きめに指定をする必要があります。

処理を行うコードが下記になります。ここではサイズ（点の間隔）を0.5にしています。

```py
import pandas as pd

# 点群ファイル読み込み。先頭行はヘッダーなのでスキップ。
path = 'pointcloud.csv'
df = pd.read_csv(path, usecols=range(6), names=list('xyzrgb'), skiprows=1)

# 点を集約する
eps = 1e-6
size = 0.5
df[['x', 'y', 'z']] = (df[['x', 'y', 'z']] / size + eps).round(0) * size

# 色は平均値を取る
df_group = df.groupby(['x', 'y', 'z']).mean().reset_index()

# Babylonで表示する都合上、点群の中央が（0,0）付近になるように変換
df_group[['x', 'y', 'z']] -= df_group[['x', 'y', 'z']].median()

# 減らした点群をjson出力
df_group.to_json('data.json', orient='records')
```

上記コードを実行すれば変換完了です...で終わらせてしまうのも寂しかったので、自分の覚書も兼ねて少しだけ解説書いておきます。

<details><summary>解説</summary>

おそらく一番分かりづらいのは、点を集約する`(df[['x', 'y', 'z']] / size + eps).round(0) * size` の部分だと思います。
やっていることはただの四捨五入ですが、スケールを変えられるようにしています。
上記の例だと `size = 0.5` なので、点の位置を0.5単位にしたいのですが、この処理で点を0.5単位にすることができます。
文章の説明よりも例を上げたほうがわかりやすいので例を挙げると 
> 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0
> ↓ 0.5で割って、四捨五入し、 0.5かける
> 1.0, 1.0, 1.0, 1.5, 1.5, 1.5, 1.5, 1.5, 2.0, 2.0, 2.0

こうすることでボクセル表示用に点を一定間隔にすることができます。
`eps`については偶数丸めを防ぐためにつけていますが、なくてもほぼ問題ありません。

</details>

## Babylon.jsでボクセル表示

ブラウザで表示するために`Babylon.js`を使用しました。
ほぼ[公式ドキュメント](https://doc.babylonjs.com/divingDeeper/mesh/copies/instances)のコピペです。表示させるデータの部分を今回ボクセル用に変換した点群を使用しただけです。

```js
const createScene = function () {
  const scene = new BABYLON.Scene(engine);
  // カメラとライトの位置はもっといい場所にしたほうがいいんだろうけど、調整していない
  const camera = new BABYLON.ArcRotateCamera("camera", -Math.PI / 2, Math.PI / 2.5, 30, new BABYLON.Vector3(0, 0, 0), scene);
  camera.attachControl(canvas, true);
  const light = new BABYLON.HemisphericLight("light", new BABYLON.Vector3(0, 50, 0), scene);

  // `points`が今回ボクセル用に変換した点群データ
  const box = BABYLON.CreateBox("box", {size: 0.45}, scene);
  const colorData = new Float32Array(4 * points.length);
  points.forEach((v, i) => {
    const instance = box.createInstance("box" + i);

    instance.position.x = v.x;
    instance.position.y = v.y;
    instance.position.z = v.z
    instance.alwaysSelectAsActiveMesh = true;

    colorData[i * 4] = v.r / 255;
    colorData[i * 4 + 1] = v.g / 255;
    colorData[i * 4 + 2] = v.b / 255;
    colorData[i * 4 + 3] = 1.0;
  });

  const buffer = new BABYLON.VertexBuffer(engine, colorData, BABYLON.VertexBuffer.ColorKind, false, false, 4, true);
  box.setVerticesBuffer(buffer);

  return scene;
};
```

ちなみに今回はとりあえずローカルで表示せるために`points`の読み込みは、`data.json`を加工して`data.js`にし、`<script src="data.js"></script>` をHTML側に差し込んで読み込みしました。
HTMLについては[チュートリアル](https://zenn.dev/chomado/books/babylonjs-tutorial-ja/viewer/1-04)のテンプレートそのままを使いました。


```js:data.json -> data.js
// ファイルの先頭に `const points = ` を追加
const points = [{"x":-29.0,"y":-10.0,"z":-2.0, ...]
```

## できあがり

できたものを実行するとローカル上で下記のようにぐりぐりできます。楽しいですね。

https://twitter.com/kiyuka_study/status/1532996683935916032


## まとめ

点群をBabylon.jsを使ってブラウザで表示させました。今回はローカル上で表示させましたが、サーバ上に上げて動かせるようすれば、ブラウザアクセスで誰でも見ることができると思います。（自分がその部分をあまり詳しくないのでそこまでたどり着けていない...）

手軽に誰でも閲覧できる、というのがブラウザの強みですよね。みんなぐるぐるして遊ぼう！！

## 参考

- [岸和田城 3次元点群データ](https://www.geospatial.jp/ckan/dataset/kishiwada-castle)
- [Babylon.js 公式入門チュートリアル ざっくり和訳](https://zenn.dev/chomado/books/babylonjs-tutorial-ja)

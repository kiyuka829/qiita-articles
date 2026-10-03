---
title: 【Babylon.js】メッシュを闇に染め上げる...！
tags:
  - Babylon.js
private: false
updated_at: '2024-12-16T07:08:01+09:00'
id: 073668f14920117ce908
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
この記事は[Babylon.js Advent Calendar 2024](https://qiita.com/advent-calendar/2024/babylonjs)の16日目の記事です。


# はじめに

ああ、こんな世界...黒く、暗く、闇に染め上げてやる...！
光など不要。すべては虚無の彼方へ沈むべきなのだ。我の手により、混沌は完成する――！

そんなわけでBabylon.jsでメッシュを闇に染め上げます。

# やみのまー

ふははは！どうだ！徐々に侵食されていくのは...！闇による真なる恐怖を知るがよい...！！

https://x.com/kiyuka_study/status/1868181020295749889


コード全体はここに。

https://playground.babylonjs.com/#WDNPYI#1

# やったこと

処理としては以下のことをやってます。

1. メッシュの頂点の非共有化
1. メッシュの三角形の隣接リスト作成
1. クリックした場所から幅優先探索を行って塗りつぶし

以下、解説していきます。

## メッシュの頂点の非共有化

今回、メッシュの色を徐々に変更するということをやりたかったので、メッシュの三角形ごとに色の変更をする必要がありました。そこで頂点カラーを指定することによって色の変更を行ったのですが、単純にやると以下のようにグラデーションになってしまいます。

![スクリーンショット 2024-12-15 085114.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/8b0e5e57-b78c-89da-33bf-85218aee86ca.png)

上の画像は、左上の三角形の頂点カラーを赤色にしたものなのですが、右下の三角形がグラデーションになっています。これは左上と右下の三角形で頂点を共有しているためです。頂点カラーを変更すると、頂点を共有している他の三角形も色が変わってしまいます。

そこで頂点を共有しないように、以下のコードで頂点の非共有化の処理を行います。
やっていることとしては、頂点インデックスごとに頂点データを作り直して、そのデータからメッシュを作成しています。

```js
/**
 * 頂点を非共有化して新しいメッシュを返す関数
 * @param {BABYLON.Mesh} inputMesh - 元のメッシュ
 * @param {BABYLON.Scene} scene - Babylon.js のシーン
 * @returns {BABYLON.Mesh} - 非共有化されたメッシュ
 */
function unshareVertices(inputMesh, scene) {
    // 元の頂点データとインデックスを取得
    const originalPositions = inputMesh.getVerticesData(BABYLON.VertexBuffer.PositionKind);
    const originalIndices = inputMesh.getIndices();

    // 新しいデータを格納する配列
    const positions = [];
    const indices = [];
    const colors = [];

    // 三角形ごとに独立した頂点を作成
    let triangleCount = 0; // 新しいインデックス用のカウンタ
    for (let i = 0; i < originalIndices.length; i += 3) {
        // 各頂点の座標を取得
        const vertices = [];
        for (let j = 0; j < 3; j++) {
            const index = originalIndices[i + j];
            const vertex = [
                originalPositions[index * 3],
                originalPositions[index * 3 + 1],
                originalPositions[index * 3 + 2],
            ];
            vertices.push(vertex);
        }

        // 頂点ごとに独立したデータを作成
        for (const vertex of vertices) {
            // 頂点位置を追加
            positions.push(vertex[0], vertex[1], vertex[2]);

            // 頂点カラー（デフォルトで白に設定）
            colors.push(1, 1, 1, 1); // RGBA
        }

        // 新しいインデックスを設定
        indices.push(triangleCount, triangleCount + 1, triangleCount + 2);
        triangleCount += 3;
    }

    // 新しいメッシュを作成
    const newMesh = new BABYLON.Mesh("unsharedMesh", scene);
    newMesh.setVerticesData(BABYLON.VertexBuffer.ColorKind, colors, true);

    const vertexData = new BABYLON.VertexData();
    vertexData.positions = positions;
    vertexData.indices = indices;
    vertexData.applyToMesh(newMesh);

    return newMesh;
}
```

## メッシュの三角形の隣接リスト作成

次に、どの三角形が隣り合っているのか、の情報を作成します。徐々に色を変更していく処理で、隣り合っている三角形から順に色を塗っていくので、それには三角形の隣接情報が必要になります。

コードとしては以下です。やっていることとしては、
- すべての三角形の組み合わせを見て、
- 頂点を2つ共有していたら隣接している、

という判断をしています。 

```js
/**
 * 隣接三角形情報を構築する関数
 * @param {BABYLON.Mesh} mesh - メッシュ
 * @returns {Object} - 隣接情報（{三角形インデックス: [隣接三角形インデックス]} の形式）
 */
function buildAdjacencyList(mesh) {
    const indices = mesh.getIndices();
    const positions = mesh.getVerticesData(BABYLON.VertexBuffer.PositionKind);
    const adjacencyList = {};

    // 頂点座標を取得
    function getVertexPosition(index) {
        return [
            positions[index * 3],
            positions[index * 3 + 1],
            positions[index * 3 + 2]
        ];
    }

    // 三角形ごとに隣接情報を計算
    for (let i = 0; i < indices.length; i += 3) {
        const triangle1 = [
            getVertexPosition(indices[i]),
            getVertexPosition(indices[i + 1]),
            getVertexPosition(indices[i + 2])
        ];

        // 隣接リストを初期化
        const triangleIndex1 = i / 3;
        if (!adjacencyList[triangleIndex1]) {
            adjacencyList[triangleIndex1] = [];
        }

        // 他の三角形と比較して隣接を確認
        for (let j = 0; j < indices.length; j += 3) {
            if (i === j) continue; // 同じ三角形はスキップ

            const triangle2 = [
                getVertexPosition(indices[j]),
                getVertexPosition(indices[j + 1]),
                getVertexPosition(indices[j + 2])
            ];

            // 共有する頂点数をカウント
            let sharedVertexCount = 0;
            for (const vertex1 of triangle1) {
                for (const vertex2 of triangle2) {
                    if(arePositionsEqual(vertex1, vertex2)){
                        sharedVertexCount++;
                    }
                }
            }

            // 隣接条件: 2つの頂点を共有している場合
            if (sharedVertexCount >= 2) {
                const triangleIndex2 = j / 3;
                if (!adjacencyList[triangleIndex1].includes(triangleIndex2)) {
                    adjacencyList[triangleIndex1].push(triangleIndex2);
                }
            }
        }
    }

    return adjacencyList;
}
```

ChatGPTに生成させてほぼいじってないので、処理効率がちょっと微妙なのですが、まあ良しとします。

## クリックした場所から幅優先探索実行

最後に徐々に色を塗っていく処理を幅優先探索によって行います。

コードは以下です。隣接リストを使用して幅優先探索の処理を行い、キューから取り出したノードの色を変えています。また、幅優先探索の深さごとに色を更新処理するようにして、侵食感？が出るようにしています。

```js
// アニメーションで隣接三角形を塗りつぶす
function animateTriangleFilling(startFaceId) {
    const visited = new Set();
    const queue = [startFaceId];

    function nextDepth() {
        if (queue.length === 0) {
            return;
        }

        for(let i = 0, size = queue.length; i < size; i++){
            const currentFaceId = queue.shift();
            if (visited.has(currentFaceId)) {
                continue;
            }

            visited.add(currentFaceId);
            
            // 現在の三角形を色変更
            const color = new BABYLON.Color3(0.06, 0.02, 0.04);
            setTriangleColor(currentFaceId, color);

            // 隣接三角形をキューに追加
            const neighbors = adjacencyList[currentFaceId];
            for (const neighbor of neighbors) {
                if (!visited.has(neighbor)) {
                    queue.push(neighbor);
                }
            }
        } 
        setTimeout(nextDepth, 50);
    }

    nextDepth();
}
```

クリック処理はこれです。

```js
// クリックした三角形の色を変更するイベント
scene.onPointerObservable.add((pointerInfo) => {
    if (pointerInfo.type === BABYLON.PointerEventTypes.POINTERPICK) {
        const pickInfo = scene.pick(scene.pointerX, scene.pointerY);
        // クリックされた三角形のインデックスを取得
        const faceId = pickInfo.faceId; // 三角形インデックス
        if (faceId !== undefined) {
            animateTriangleFilling(faceId); // アニメーション開始
        }
    }
});
```

# まとめ

頂点カラーの変更 + 幅優先探索 でメッシュの色塗りをしました。

今回、コードはほぼChatGPTに生成させてちょこちょこ修正する感じで作ってます。アイデアがあれば簡単なコードはさくさくかけるので、いい時代になったなーと思ったり。

---

ちなみに冒頭のは...なんでかこうなりました。「色づく世界の明日から」っていうアニメからネタを思いついたのになんででしょうね？というか去年も冒頭のノリで記事書いてたような...？この時期になると中二病が発症する...！？

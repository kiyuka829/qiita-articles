---
title: IFCのモデルをplotlyで表示する
tags:
  - Python
  - plotly
  - IfcOpenShell
private: false
updated_at: '2024-02-13T19:06:10+09:00'
id: ef4b197fa28d3a96d068
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
![plotly_axis.JPG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/93b7a741-876a-7503-90af-130fbf5af643.jpeg)

# はじめに

IFCファイルを読み込む手段の一つに`IfcOpenShell`があります。形状情報も取得することができるのですが、取得してもPythonでは表示する方法がありません。いえ、[`pythonocc`を使用すれば表示できる](https://qiita.com/Takashi_Kasuya/items/dced9fc3d8869e88ce6c)そうなのですが、[`pythonocc`](https://github.com/tpaviot/pythonocc-core)を使用するには`conda`を使用するか、ソースコードからビルドする必要があるようです。宗教上の理由で（？）`conda`が使えない人もいると思いますし、ビルドは難易度が高いです。

そんなわけでもっと手軽にIFCのモデルを表示したいので、[`IfcOpenShell`](https://ifcopenshell.org/)で読み込んだ形状情報を[`plotly`](https://plotly.com/python/)で表示します。

# できました

これで表示できるよ！やったね！！

```py
import plotly.graph_objects as go
import numpy as np
import ifcopenshell.geom

# 世界座標系で取得する設定
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)

# IFCファイル読み込み
model = ifcopenshell.open(path)

# すべての形状情報を取得する
meshes = []
for element in model.by_type("IfcProduct"):
    # 部屋の情報などや壁の開口部などは除く
    if  element.is_a('IfcOpeningElement') or element.is_a('IfcSpace'):
        continue

    try:
        # 形状の取得
        shape = ifcopenshell.geom.create_shape(settings, element)
    except:
        continue

    # 頂点と面の情報を取得
    verts = shape.geometry.verts
    faces = shape.geometry.faces
    verts = np.array(verts).reshape(-1, 3)
    faces = np.array(faces).reshape(-1, 3)

    # 色情報の取得
    materials = shape.geometry.materials
    material_ids = shape.geometry.material_ids
    if len(materials) == 0:
        facecolors = ['lightgray'] * len(faces)
    else:
        colors = [np.array(material.diffuse) for material in materials]
        transparencies = [1 - material.transparency for material in materials]
        colors = np.hstack([np.array(colors), np.array(transparencies).reshape(-1, 1)])
        facecolors = [colors[material_id] for material_id in material_ids]

    # plotlyのメッシュを作成
    mesh = go.Mesh3d(
        x=verts[:, 0],
        y=verts[:, 1],
        z=verts[:, 2],
        i=faces[:, 0],
        j=faces[:, 1],
        k=faces[:, 2],
        facecolor=facecolors,
        flatshading=True,
        lighting=dict(
            ambient=1,
            diffuse=0,
        ),
    )
    meshes.append(mesh)

# plotlyで表示
fig = go.Figure(data=meshes)

# 軸を表示しない設定
noaxis = dict(
    showbackground=False,
    showgrid=False,
    showline=False,
    showticklabels=False,
    ticks="",
    title="",
    zeroline=False,
)

# レイアウト設定
fig.update_layout(
    scene=dict(
        xaxis = noaxis,
        yaxis = noaxis,
        zaxis = noaxis,
    ),
    scene_aspectmode='data',
)

# HTMLファイルに保存
fig.write_html(
    "file.html",
    include_plotlyjs='cdn',
    full_html=True,
)
```

# 解説

コードの解説します。

## 世界座標系の設定

まず最初の設定の部分。

```py
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)
```

IFCのデータは形状の情報（`Representation`）と位置情報（`ObjectPlacement`）が別れています（[`IfcProduct`のドキュメント参照](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcProduct.htm#5.1.3.10.3-Attributes)）。そのため、特に設定を行わずに形状情報を取得すると、位置情報がないので以下のように原点付近にメッシュが表示されます。

![plotly_local.JPG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/99feed55-c95e-e89a-da47-4c122685038e.jpeg)

そのため、正しい位置を取得するには、世界座標系で形状を取得するように設定するか、別途位置情報を取得して変換をかける必要があります。
今回は、[こちらの記事](https://qiita.com/yabakunaiyo1/items/3fb43fa49fa8036fae23)を参考にして世界座標系で取得しました。

## 形状を持つデータの取得

すべての形状データの取得を行います。

```py
for element in model.by_type("IfcProduct"):
    # 部屋の情報などや壁の開口部などは除く
    if  element.is_a('IfcOpeningElement') or element.is_a('IfcSpace'):
        continue

    try:
        # 形状の取得
        shape = ifcopenshell.geom.create_shape(settings, element)
    except:
        continue
```

IFCで形状情報を持つのは`IfcProduct`（を継承しているエンティティ）です。そのため `IfcProduct` を取得すればすべての形状を持つデータを取得できるのですが、`IfcSpace`（部屋の情報など）や `IfcOpeningElement`（壁の開口部など）も含まれてしまいます。そのため、それらのエンティティは除いて取得する必要があります。

ちなみに除かないで取得すると以下のようになります（わかりやすくするために色を変えています）。

![plotly_opening.JPG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/86c79766-3a84-1133-d178-64dc4896ff91.jpeg)

また、`IfcProduct`のドキュメントを見てみるとわかるのですが、形状情報はオプションです。つまり形状のないデータもあります。さらには形状情報があっても`IfcAnnotation`のように`IfcOpenShell`が形状取得に対応していないものもあります。そのため、形状取得するときにエラーが発生しても例外処理で無視するようにしています。

## 頂点と面と色の取得

メッシュを作成するための、頂点、面、色の情報を取得します。

```py
    # 頂点と面の情報を取得
    verts = shape.geometry.verts
    faces = shape.geometry.faces
    verts = np.array(verts).reshape(-1, 3)
    faces = np.array(faces).reshape(-1, 3)

    # 色情報の取得
    materials = shape.geometry.materials
    material_ids = shape.geometry.material_ids
    if len(materials) == 0:
        facecolors = ['lightgray'] * len(faces)
    else:
        colors = [np.array(material.diffuse) for material in materials]
        transparencies = [1 - material.transparency for material in materials]
        colors = np.hstack([np.array(colors), np.array(transparencies).reshape(-1, 1)])
        facecolors = [colors[material_id] for material_id in material_ids]
```

頂点と面は[公式ドキュメント](https://blenderbim.org/docs-python/ifcopenshell-python/geometry_processing.html)のコードそのままです（numpyを使ってはいますが）。

色情報については`plotly`で処理するために RGBA の形式にしています。このとき`material.transparency`が透明度なのですが、IFCでは 1=透明, 0=不透明 のなので逆転させています。また、色情報がないデータもあるので、その場合はlightgrayとしました。

## plotlyのメッシュ作成

 plotlyでの3Dメッシュを作成します。

```py
    mesh = go.Mesh3d(
        x=verts[:, 0],
        y=verts[:, 1],
        z=verts[:, 2],
        i=faces[:, 0],
        j=faces[:, 1],
        k=faces[:, 2],
        facecolor=facecolors,
        flatshading=True,
        lighting=dict(
            ambient=1,
            diffuse=0,
        ),
    )
```

メッシュ作成時は`flatshading`と`lighting`を指定して光による表現を消して、単純に色を表示するようにします。この設定がないと以下のように変な影が表示されます。

![plotly_model.JPG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/1f5efa84-861d-2e25-ffb1-8e657010c15a.jpeg)

なぜこうなるのかはわかりません。ただ、そもそも`plotly`はグラフを描画するライブラリであって、3Dモデルを表示するものではない（可能ではあるけれども）ので、光の処理はそこまで得意ではないのかもしれません。

## メッシュの表示

作成したメッシュをplotlyで表示します。

```py
fig = go.Figure(data=meshes)

# 軸を表示しない設定
noaxis = dict(
    showbackground=False,
    showgrid=False,
    showline=False,
    showticklabels=False,
    ticks="",
    title="",
    zeroline=False,
)

# レイアウト設定
fig.update_layout(
    scene=dict(
        xaxis = noaxis,
        yaxis = noaxis,
        zaxis = noaxis,
    ),
    scene_aspectmode='data',
)
```

レイアウトの設定での`scene_aspectmode='data'`の指定はアスペクト比の設定です。これがないと見た目が歪みます。また、`noaxis`の指定をすることで、軸の表示を消してモデルのみ表示させることができます。

## できあがり

最終的に表示されたものが以下です。

![plotly_flatshading.JPG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/88069468-4660-2a96-bb70-979485b5722c.jpeg)

# まとめ

IFCのモデルを`IfcOpenShell`で読み込んで`plotly`で表示しました。`plotly`だとHTMLファイルに出力することもできるので、出力したHTMLをブラウザで開くだけで手軽にモデルを表示することができます。
ただ、かなり表示が重いです。数十MB程度のIFCファイルから作成したHTMLでも開くのに数分かかりました。大きめのモデルは素直にIFCを表示するソフトウェアやIFC.jsなどを使用しましょう。


# 参考

今回使用したモデル

https://blenderbim.org/docs-python/ifcopenshell-python/hello_world.html

`IfcOpenShell`でのジオメトリ取得方法

https://blenderbim.org/docs-python/ifcopenshell-python/geometry_processing.html

https://qiita.com/yabakunaiyo1/items/3fb43fa49fa8036fae23

plotlyで3Dメッシュの表示

https://plotly.com/python/3d-mesh/

https://qiita.com/tmiyama/items/bba94d4125d9b67edf84

`web-ifc`での開口部などを除く処理のソースコード

https://github.com/IFCjs/web-ifc/blob/6e21423d0e15a37a12986290c412bae5b788937c/src/cpp/web-ifc-wasm.cpp#L250


pythonoccを使用しての描画

https://qiita.com/Takashi_Kasuya/items/dced9fc3d8869e88ce6c

https://github.com/tpaviot/pythonocc-core

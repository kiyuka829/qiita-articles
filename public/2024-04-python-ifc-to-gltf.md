---
title: PythonでIFCのモデルをglTFに変換する
tags:
  - Python
  - glTF
  - IFC
  - IfcOpenShell
private: false
updated_at: '2024-04-28T17:10:28+09:00'
id: e80976285d912bf9ff6b
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

IFCファイルのモデルを表示して閲覧するのって、ちょっと手間ですよね？
表示するには、[Open IFC Viewer](https://openifcviewer.com/) や [BIMvision](https://bimvision.eu/) のような専用のソフトウェアをPCにインストールする必要があります。

他の人にIFCのモデルだけ見せたいんだけど...というときにわざわざソフトウェアをインストールしてもらうのもちょっとためらいますよね。
IFCのモデルを特に環境を設定しないでも閲覧できる形式に変換したいときがあると思います。

そこでIFCのモデルをPythonを使って、3Dモデルのファイル形式の一つである`glTF`に変換したいと思います。

## glTFに変換できました

できたよ！やったね？

[GitHub Gist: ifc2gltf.py](https://gist.github.com/kiyuka829/32c0f65d9ecf95eff57802e370e15e6e)

[Babylon.js Sandbox](https://sandbox.babylonjs.com/) で表示させれば、treeも表示できるよ！

![ifc2gltf_tree.JPG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/82a9a7cc-6893-3acc-3be1-80c0583b3f1d.jpeg)

選択して非表示にしたり、移動したりもできるよ！（Xの投稿は階層構造ついてない）

https://x.com/kiyuka_study/status/1772612770770440508

## 経緯

最初は `IfcOpenShell` を使えば直接変換できるのではないかと思って調べたのですが、[公式ドキュメント](https://docs.ifcopenshell.org/ifcconvert.html)を見ると `BlenderBIM Add-on` を使う必要があり、直接変換することはできないようでした。

そういうわけで、[`IfcOpenShell`](https://ifcopenshell.org/)と[`pygltflib`](https://pypi.org/project/pygltflib/)を使用して、自力で実装しています。

## まとめ

IFCのモデルを階層構造付きでglTFに変換しました。
glTF形式にしておけば、Windowsのデフォルトでインストールされている3Dビューアーなどでも表示することができるので、ちょっとモデルを見るだけの用途であれば便利です。

え？解説？ほとんどglTFのフォーマットの話になってしまうので、ここではしません。
もしかしたら、別記事でPythonによるglTF出力方法の解説を書くかも？

## 参考

- glTF 

https://pypi.org/project/pygltflib

https://qiita.com/nokonoko_1203/items/827c4afc3ae88666126b

https://qiita.com/cx20/items/2b86cb5052cd7c36038a

https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#glb-file-format-specification

https://github.com/KhronosGroup/glTF-Sample-Models/tree/main/2.0/AlphaBlendModeTest

- Web glTF ビューアー

`Babylon.js Sandbox` が一番使い勝手が良かった。`Three.js`実装の`gltf-viewer` はglTFファイルのフォーマットが誤ってるとどこがエラーか表示してくれるのでglTFフォーマットの確認に便利。

https://sandbox.babylonjs.com/

https://gltf-viewer.donmccurdy.com/

https://playcanvas.com/viewer

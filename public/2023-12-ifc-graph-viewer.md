---
title: IFCのデータ構造を可視化する「IFC graph viewer」を作ったよ
tags:
  - Python
  - JavaScript
  - IFC
  - BIM
  - IfcOpenShell
private: false
updated_at: '2023-12-24T10:46:13+09:00'
id: 116f29df6a4e91d062ae
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
![viewer.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/f67312a9-6453-a9c9-d8ae-19cd7c7d7ad5.jpeg)

# はじめに

BIM（Building Information Modeling）は建物の3Dモデル（Modeling）にデータ（Information）が付与されています。そのため、単純な見た目の情報だけではなく、データベースとしての使い方もできるため、様々な活用方法が考えられます。
しかし、ArchicadやRevitなどのネイティブのソフトウェアによって作成されたBIMファイルは、そのソフトを介さないと使用できません。ソフトウェアにAPIが整備されていて自由にデータのやり取りができるのであればいいですが、多くのソフトウェアではAPIは整備されていないと思われます。

そのため、データを解析しようとか、必要なデータを抽出して何かしらのアプリケーションに活用しようとか、そういったBIMのInfomation要素を活用して何かをしようとなるとBIMの標準フォーマットであるIFCファイルを使用する必要があります。

ただ、IFCファイルを使用するにもファイルの構造を理解している必要があります。`IfcOpenShell`や`IFC.js`のようなIFCを解析するライブラリも存在しますが、それらを使用するにしても中身をある程度理解していないと、サンプルコードを動かすだけで終わってしまうでしょう。

以前に[IFCファイルの中身を解読する](https://qiita.com/kiyuka/items/00434f1b8e0b38c621fb)という記事を書きましたが、このときはファイルを手作業で一行ずつ見て解析するという苦行をやりました。ぶっちゃけめんどくさいですもうやりたくないです。

だったらIFCファイルのデータ構造を可視化するツールを作ってしまえ！！というわけで作りました。

https://github.com/kiyuka829/ifc-graph-viewer

# できること

こんな感じのことができます。

https://x.com/kiyuka_study/status/1738442004043084204?s=20

使い方やインストールについてはGitHubに書いているのでそちらを見てもらえれば。
~~本当は実行ファイルにしてリリースしようかと思ったのですが、ウイルス判定されてしまったので諦めました。~~

ビルドした実行ファイルも上げています。

https://github.com/kiyuka829/ifc-graph-viewer/releases


# 構成とか技術選定とか

興味ある人いるのか知らないけど構成を書く。

## 構成

バックエンド、フロントエンドの考え方で、表示はブラウザ（HTML, CSS, JavaScript）、IFCの解析処理はPythonを使用しました。

- フロントエンド（可視化） : Vite, Vue, TypeScript
- バックエンド（解析）: Python, Flask, IfcOpenShell


### 可視化処理

[IFCのドキュメント](https://ifc43-docs.standards.buildingsmart.org/)とかを見つつ、IFCファイルのデータ構造を分析していたらグラフ構造っぽいことがわかりました。グラフ構造を可視化する方法を調べると[ネットワークグラフ描画ライブラリ7個まとめ](https://qiita.com/SuyamaDaichi/items/c47dc74cfefd92516e28)などのようにJavaScriptを使用してブラウザで可視化する方法が多く出てきます。
普段使用している言語がPythonかJavaScriptだったこともあり、JavaScriptを使用することにしました。ただし、表示処理は描画ライブラリを使用せずに`Vue + TypeScript`で書きました。理由はライブラリの学習コストの問題と、後で拡張するときにライブラリが対応していなくてできない、ということを避けたかったというのがあります。それに今ではChatGPTがいるので自力でもそれなりに書けてしまうというのもあります。

そして可視化の処理はユーザが指定した部分を表示するような形にしました（IFCのグラフ構造すべて表示させるのはデータ量の関係で無理なので）。そのため、作成時にイメージしたのはグラフネットワークというよりも、インタラクティブに編集のできるBabylon.jsの[Node Material Editor](https://nodematerial-editor.babylonjs.com/)やUnreal Engineの[ブループリント](https://docs.unrealengine.com/4.27/ja/ProgrammingAndScripting/Blueprints/GettingStarted/)のなどようなノードエディタでした。
そのため見た目的にノードエディタっぽくなっています。でもデータをノード間で流しているわけでも、ノードで処理をしているわけでもなく、グラフ構造を表示しているだけです。

### IFC解析処理

IFCのライブラリはIFCエンティティの継承構造や逆属性を扱う必要があったためPythonの`IfcOpenShell`を使用しました。（調べた限り`IFC.js`ではできなさそうでした。）

そしてサーバー起動は楽ちんなのでFlaskを使用しました。

## デスクトップアプリ化 ~~（したかった）~~

最終的に[pywebview](https://pywebview.flowrl.com/)と[PyInstaller](https://pyinstaller.org/en/stable/)を使用して、デスクトップアプリ化するつもりだったのですが、Microsoft Difenderにウイルス判定されて削除されてしまったので断念しました。しょんぼりです(´・ω・｀)

2023-12-24 追記
→ Pyinstallerではなく[Nuitka](https://nuitka.net/index.html)を使用したら問題なさそうだったのでGitHubに上げています。多分大丈夫だと思いたい...。

# まとめ

IFCファイルのグラフ構造を可視化するツール「**IFC graph viewer**」を作りました。

正直なところこのツールがなにかに直接的に役立つかというとなんとも言えません。これを使ってなにかする、というよりも「IFCのデータ構造特殊でよくわかんないからデータいじって解析するにしてもハードル高すぎない！？」という問題の手助けができたらいいなーというモチベで作りました。あと自分でノードエディタっぽいものを作りたかった。

まだ機能としては最小限しか作っていないですが「最小限出来てるんだからとりあえず公開してしまえ！」と思って公開した感じです。そのためモチベが続く限りまだ色々更新するつもりです。


# 参考

この記事を書くのに参考にしたものではなくて、記事を書いている途中で見つけたもの。IFCをグラフデータベースにしてあれこれしているっぽい。ちゃんと読んでないからこの記事で書いているIFCのグラフとは違うものを表現して使っているかも。

https://ifcwebserver.org/

https://www.researchgate.net/publication/325078444_Building_Knowledge_Extraction_from_BIMIFC_Data_for_Analysis_in_Graph_Databases

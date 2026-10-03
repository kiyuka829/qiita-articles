---
title: Vite+Flask+pywebviewでデスクトップアプリを作成する
tags:
  - Python
  - Flask
  - pywebview
  - vite
private: false
updated_at: '2023-12-26T00:20:25+09:00'
id: 0aa0f907e9c898ee2ede
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

こんな人向けの記事だよ

- Pythonでデスクトップアプリを作りたいよ
    - numpyとかpandasとかPyhonのライブラリを使いたいからね
- 画面の部分はVueとかReactとかを使って書きたいよ
    - 見た目はHTML, CSSでリッチな感じにしたいよね
- 最終的な実行ファイルはPython側にまとめたいよ
    - Node.jsとPythonの2つもあるとごちゃごちゃして迷子になっちゃう(´・ω・｀)


# Pythonでアプリを作成する方法について

pywebviewを選択する理由の説明なので「結論ちょーだい(ΦωΦ)」って人はここはスキップするのだ！！

## Pythonのみでシンプルに作成する

Pythonでアプリを作成する方法は色々あります。シンプルに作れるのは[PySimpleGUI](https://www.pysimplegui.org/en/latest/)や[Streamlit](https://streamlit.io/)、[Flet](https://flet.dev/)などでしょうか。これらのフレームワークはかなり簡単にかけるので、ユーザのアクションが「ファイルの選択」「ボタンを押す」「設定などを選択・入力する」などであればこれらを使用するのが良いでしょう（たとえば、CSVファイルからデータを加工・抽出して出力する、など）。

ただ、シンプルが故に機能が限られているため、それ以上に複雑な操作をユーザに求めるアプリを作りたいとなると難しくなります。
たとえば、お絵かきソフト的なものを作りたいとか、可視化したデータをマウス処理で自由に操作したいとか、[Rate.js](https://retejs.org/)みたいなノードエディタっぽいものを作りたいとか。そういうことを実現したいとなると、これらのフレームワークでは難しくなります。

## フロントエンドとバックエンドで作成

そういった複雑なGUIが必要である場合の選択肢として、VueやReactなどのフロントエンドフレームワークを使用して操作画面を作成し、バックエンドはPythonでFlaskやDjangoなど使用して処理を行う、という方法が考えられます。

この方法のメリットととしては、以下のようなことが挙げられるかと思います。

- 画面のデザインを好きにカスタマイズできること
- 画面がブラウザベースなので、ブラウザの機能をそのまま使えること
- Webアプリとデスクトップアプリの両方に対応できること

今回はこの方法についての説明になります。

## Electron

Web技術でデスクトップアプリを作成する方法として[Electron](https://www.electronjs.org/ja/docs/latest)があります。
そしてElectronで画面を、Pythonで処理を、という方法も可能です。

https://qiita.com/BUU-SAN/items/af3ae2c9835cd06dddc4

そのためElectronを使用することで、先ほど説明したフロントエンド・バックエンドのアプリを作成することも可能です。

ただ、この方法で作成したものをデスクトップアプリとして配布する場合、ElectronとPythonとの両方を実行ファイルにする必要があります。ビルドするだけではあるのですが、どうしても環境依存の問題で別環境では動かないという問題が発生するケースがあります。
そうなるとElectronとPythonのどちらに問題があったかの切り分けが必要になってきます。実行環境が自分の環境であれば色々検証するなりで試せるのですが、配布先の環境だとそれも難しいです。

そのため、実行ファイルを手軽に配布するならPython側だけで作成したいです。

## webview

そこで [pywebview](https://pywebview.flowrl.com/) を使用します。pywebviewはHTMLコンテンツをPythonのGUI上に表示することができます。つまり、VueやReactなどで作成したHTMLファイルをそのままデスクトップアプリの画面として使用できるわけです。


# 実装

実装方法です。気をつけることは以下です。

フロントエンド側

- APIエンドポイントは環境変数から読み込むようにする（推奨）
- 環境変数ファイルは開発用とビルド用で分けておく（推奨）

Python側

- FlaskはViteビルドのHTMLファイルを読み込むための設定をする（必須）
- CORS設定をしておくと便利（推奨）
- pywebviewはFlaskサーバを指定する（必須）

（推奨）と書いている部分は開発用便利枠です。設定しておかないと開発時も毎回Viteのビルドが必要になります。


## フロントエンド（画面）

フロントエンド側は好きに書けばOKです。下記の例はVueで書いていますがReactでも問題なしです。また、Python側との連携もここでは`axios`を使用していますがそれもお好みでOK。
ただ、APIエンドポイントの指定だけは環境変数から読み込むようにしておきます。

```vue:App.vue
<script setup lang="ts">
import axios from "axios";
import { ref } from "vue";

const endpoint = import.meta.env.VITE_API_ENDPOINT as string;

const message = ref<string>("Push the button!");

const handleClick = () => {
  const config = {
    method: "post",
    url: endpoint + "/message",
  };
  
  // Python側に処理をリクエストする
  axios(config)
    .then((response) => {
      console.log(response);
      response.data.message && (message.value = response.data.message);
    })
    .catch((error) => {
      console.log(error);
    });
};
</script>

<template>
  <div>
    <button type="button" @click="handleClick">{{ message }}</button>
  </div>
</template>
```

このとき環境変数ファイルを開発用とビルド用で分けておきます。
`.env.development`は`npm run dev`実行時に使用されるファイルで、`.env.production`は`npm run build`でビルドするときに使用されるファイルです。

```.env.development
VITE_API_ENDPOINT=http://localhost:5000
```

```.env.production
VITE_API_ENDPOINT=
```

## バックエンド（Flask）

バックエンド側はFlaskを使用していきます。このときViteビルドのHTMLファイルを読み込む工夫が必要です。また、開発用に`CORS`設定をしておくと便利です。それ以外の処理の部分は通常通り書いて問題ありません。

```py:server.py
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# ビルドされたHTMLファイルを読み込むための設定
app = Flask(__name__, static_folder="dist", static_url_path="")

# 開発時はあると便利。ビルドしたHTMLを使用するときには不要。
CORS(app)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# あとはフロント側からリクエストされる処理を好きに書く
@app.route("/message", methods=["POST"])
def get_message():
    message = random.choice(["Apple", "Banana", "Cherry"])
    return jsonify({"message": message})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
```

## pywebview

pywebviewは単純にFlaskのサーバを指定するだけ。とても簡単。全画面表示とかもろもろの設定をしたい場合は[公式ドキュメント](https://pywebview.flowrl.com/guide/api.html)を確認してもらえれば。

```py:app.py
import webview

from server import app as server

if __name__ == "__main__":
    webview.create_window("title",  server)
    webview.start(debug=False)
```

# 実行・確認方法

## 開発時の実行方法

開発時は以下のように実行してテストします。

- `npm run dev`で フロントエンド実行
- `python server.py` でバックエンド実行 
- `http://127.0.0.1:5173/`（フロントエンド側）にアクセス

こうすることでフロント・バックエンドの両方ともにコード修正がすぐに反映されるため、開発しやすいです。これのための`.env.development`や`CORS`の設定でした。

## Viteビルドしての実行・確認方法

コードができあがったらビルドして確認します。ViteビルドのHTMLファイルをFlaskで読み込む方法については、[別記事](https://qiita.com/kiyuka/items/6b7b70b4265728b1a6c3)にも書いているのでそちらも参考にしてもらえれば。

- `npm run build`でビルド
-  Flaskで読み込むように`dist`フォルダを移動
- `python server.py`で起動
- `http://127.0.0.1:5000` （Flaskサーバー）にアクセス


これでビルドしたHTMLファイルがFlaskから読み込めているかの確認をします。ビルドやFlaskの設定が正しくできていれば正常に起動するはずです。

## pywebviewアプリ確認

そして最後に`python app.py`でpywebviewを起動して確認します。これまではブラウザでの確認でしたが、最後はアプリの画面での確認になります。HTMLをそのまま表示していると言っても環境が異なるため、ブラウザと見た目が変わるケースがあります。


## 実行ファイルの作成

想定通りに問題なく動くことを確認したら、あとは[PyInstaller](https://pyinstaller.org/en/stable/)や[Nuitlka](https://nuitka.net/)で実行ファイルにしてできあがりです。

以下はWindowsでのコマンド実行例です。出力ディレクトリ名は指定しておくと安心です（`dist`でかぶっているので）。また、ビルドしたHTMLファイルを含む必要があるので、その指定だけは忘れずに。

```sh
# pyinstaller
pyinstaller app.py --distpath ../dist --clean --add-data "dist;dist" -n appname

# nuitka
nuitka --standalone --follow-imports app.py --output-dir=../dist --include-data-dir=dist=dist --output-filename=appname
```

# まとめ

Vite+Flask+pywebviewでデスクトップアプリを作成する方法でした。

pywebviewはWebアプリを作ればそのままデスクトップアプリにできるのでとても便利ですね。


# 参考

Viteの環境変数ファイル

https://ja.vitejs.dev/guide/env-and-mode.html

https://zenn.dev/longbridge/articles/575190b038f805

pywebview

https://pywebview.flowrl.com

Python実行ファイル化

https://pyinstaller.org/en/stable/

https://nuitka.net/


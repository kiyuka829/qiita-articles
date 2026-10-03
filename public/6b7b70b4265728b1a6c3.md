---
title: ViteビルドのHTMLファイルをFlaskで読み込む
tags:
  - Python
  - Flask
  - vite
private: false
updated_at: '2023-12-24T15:38:29+09:00'
id: 6b7b70b4265728b1a6c3
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

FlaskでWebアプリケーションを作成するとき「HTMLファイルはVueやReactなどのフレームワークを使用したいし、TypeScriptで書きたい」と思うことがあります。そうするとViteなどでビルドすることになるのですが、ビルドしたファイルをFlaskで読み込もうとしたら、ちょっと手こずりました。

そんなわけで、ビルドしたHTMLファイルをFlaskで読み込む方法です。

# 結論

`npm run build`でビルドすると出力される`dist`フォルダをpythonのファイルの場所に移動する

```:ディレクトリ構成
├─dist/
│  ├─assets/
│  │  ├─index.js
│  │  └─index.css
│  └─index.html
└─server.py
```

Flaskの静的ファイルの読み込み設定を以下のようにする。

```py:server.py
from flask import Flask, send_from_directory
app = Flask(__name__, static_folder="dist", static_url_path="")

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# MIME type of "text/plain" のエラーが出るなら以下も追加する
import mimetypes
mimetypes.add_type("application/javascript", ".js")

@app.route("/<path:path>")
def send_js(path):
    return send_from_directory(app.static_folder, path)

# 起動
if __name__ == "__main__":
    app.run(debug=True)
```

# なぜ読み込めなかったのか

FlaskはデフォルトのルートディレクトリはFlaskを起動したファイルの場所になります。しかし、ビルドしたHTMLファイルは`index.html`をルートディレクトリとしてjsやcssを読み込もうとします。そのため、設定を何もしないと`index.html`からjsやcssが読み込めません。

```html:index.html
<!-- `index.html` の場所を基準に読み込むようにビルドされている -->
<script type="module" crossorigin src="/assets/index.js"></script>
<link rel="stylesheet" href="/assets/index.css">
```

そこで、以下のように設定を変えます。これで`index.html`のある場所を基準にして、jsやcssなどを読み込むことができます。

```py
# static_folder と static_url_pathの指定で、読み込み設定を変更
app = Flask(__name__, static_folder="dist", static_url_path="")

@app.route("/")
def index():
    # ビルドした静的ファイルを読み込むので 
    # `render_template` ではなく `send_from_directory`を使用する
    return send_from_directory(app.static_folder, "index.html")
```

# まとめ

ViteビルドのHTMLファイルをFlaskで読み込む方法でした。

Vite側とFlask側のそれぞれをサーバ起動する、ということやっている記事は見つけられたのですが、HTMLをビルドして起動をFlaskのみにする方法については、探しても見つけられなかったので記事にしました。


# 参考

https://flask.palletsprojects.com/en/2.3.x/api/

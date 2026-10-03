---
title: Pythonのdict（っぽいもの）にドットでアクセスするいろんな方法
tags:
  - Python
private: false
updated_at: '2024-04-28T22:40:09+09:00'
id: 56ba34d4a1c20b3e199f
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

Pythonの辞書型を使っていて「JavaScriptのオブジェクトみたいにドット`.`でアクセスしたい！」と思うことってありませんか？
`data['key']` のように文字列で書くのって地味にめんどくさいと思うんです。

なにか方法ないのかなと思って、調べてみるといくつか方法があるようだったのでまとめてみました。

## クラス：辞書を継承する

調べるとクラスを継承する形のものがいくつか見つかりました。
（調べて見つかったものを改変しています。）

```py
class DotDict1(dict):
    def __getattr__(self, item):
        return self[item]

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, item):
        del self[item]
```

```py
class DotDict2(dict):
  def __getattr__(self, key):
    return self.__getitem__(key)
  
  def __setattr__(self, key, value):
    self.__setitem__(key, value)

  def __delattr__(self, key):
    self.__delitem__(key)
```

```py
class DotDict3(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
```

```py
class DotDict4(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self
```

この中で `DotDict1`, `DotDict2`, `DotDict3` は同じです。 どれもドットでアクセス（属性にアクセス）したとき、`['key']` でのアクセス（辞書へのアクセス）と同じ処理をする、という実装をしています。それぞれ書き方が異なっているだけで機能的には同じになります。

しかし、`DotDict4` だけは若干異なり、ちょっと扱いを気をつける必要があります。具体的には、以下のように`keys`, `values` などといった辞書にもとからあるメソッドへのアクセスに注意が必要です。

```py
d = DotDict4()
d.keys = 1
print(d.keys) # 1
print(d['keys']) # 1
d.keys() # TypeError: 'int' object is not callable
```

何が起きているかというと、辞書の属性値として`keys` を設定したつもりが、辞書の`keys`メソッドを上書きしており、`keys`メソッドが使用できなくなっています。このように既存のメソッドに誤って値を設定できてしまうので、注意が必要です。

他の `DotDict1`, `DotDict2`, `DotDict3` であれば以下のように上書きせずに設定ができます。
ただ、`keys`などはメソッドと名称が重複してしまっているので、ドットでのアクセスはできません。

```py
d = DotDict1()
d.keys = 1
print(d.keys) # <built-in method keys of DotDict1 object>
print(d['keys']) # 1
print(d.keys()) # dict_keys(['keys'])
```

## SimpleNamespace

`types` の `SimpleNamespace` を使う方法です。
もとの辞書方式でのアクセスはできませんが、ドットでアクセスすることができます。またこの方法の場合、VSCode上で設定した値の補完機能が働きます。
通常の`dict`とほとんど変わらずシンプルに書けますし、お手軽なのではないかと思います。

ただ、変数名として許可されていないもの（数字始まりや`+`等の記号など）は使えないため、そこだけは注意が必要でしょうか。

```py
from types import SimpleNamespace

d = {'name': 'Alice', 'age': 30}
ns = SimpleNamespace(**d)
# ns = SimpleNamespace(name='Alice', age=30) # 同じ

# 追加や削除も可能
ns.abc = 123
del ns.abc

# 辞書でのアクセスはできない
# ns['name'] # error
```

## namedtuple

`collections` の `namedtuple` を使う方法です。この方法でもドットでアクセスが可能です。
ただ、最初に定義した変数しか設定できませんし、インスタンスを作成したあとに変更もできません。
逆に言えば変更することができないので、動的に変更することがないとわかっており、定義を明確にして誤って変更してしまうことを防ぎたいのであれば、`namedtuple` がいいのではないかと思います。

また、VSCodeで補完機能が働くことや、変数名として許可されているもののみが使用できることは`SimpleNamespace`と同様になります。

```py
from collections import namedtuple

# namedtuple を定義
Person = namedtuple('Person', 'name age')

# インスタンスを作成
person = Person(name='Bob', age=25)

# タプルなので変更不可
person.name = 'Alice' # AttributeError: can't set attribute
person.abc = 123 # AttributeError: 'Person' object has no attribute 'abc'
```

## まとめ

辞書っぽいものにドットでアクセスするいくつかの方法でした。
個人的には、`SimpleNamespace` がお手軽で使いやすいのではないかなと思います。

## 参考

クラス

https://zenn.dev/kazuhito/articles/dbe6bbf8ce3ef2

https://qiita.com/utkamioka/items/d2c31dff5dfafbb5f12b

https://ugcj.com/python%E3%81%AEdict%E5%9E%8B%E3%81%AB%E3%83%89%E3%83%83%E3%83%88%E3%82%A2%E3%82%AF%E3%82%BB%E3%82%B9%E3%82%92%E8%BF%BD%E5%8A%A0%E3%81%99%E3%82%8B%E6%96%B9%E6%B3%95/

https://chat.openai.com/c/74717a4b-3e97-4516-931a-25a13d05a616


SimpleNamespace

https://techblg.app/articles/how-to-make-dot-access-with-python-dictionary/

https://qiita.com/fgshun/items/63fe396f043fb7553330


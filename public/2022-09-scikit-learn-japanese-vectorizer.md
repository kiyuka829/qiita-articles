---
title: scikit-learnのCountVectorizerやTfidfVectorizerの日本語での使い方について
tags:
  - Python
  - 自然言語処理
  - scikit-learn
private: false
updated_at: '2022-09-23T22:59:36+09:00'
id: 3de09e313a75248ca029
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

テキストデータを処理するには、文字列のままだと扱うのが難しいのでベクトル化ということを行います。テキストのベクトル化の有名な手法として、Bag of WordsやTF-IDFと言った手法があります。
それらの手法は機械学習ライブラリのscikit-learnでも実装されているのですが、日本語のテキストに対して使用するのに結構つまづきました。
この記事は、そのときの覚え書きになります。

# 日本語での使い方：結論

事前に文章を単語で区切ってリスト化しておき、`analyzer=lambda x: x` をパラメータに指定して、ベクトル化を行う。
（`CountVectorizer`を例にしているが `TfidfVectorizer` でも同様。）

```py
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

corpus = [
    ['これ', 'は', '最初', 'の', 'ドキュメント', 'です', '。'],
    ['この', 'ドキュメント', 'は', '2', '番目', 'の', 'ドキュメント', 'です', '。'],
    ['そして', '、', 'これ', 'は', '3', '番目', 'の', 'もの', 'です', '。'],
    ['これ', 'は', '最初', 'の', 'ドキュメント', 'です', 'か', '?']
]
vectorizer = CountVectorizer(analyzer=lambda x: x)

vec = vectorizer.fit_transform(corpus)
feature_names = vectorizer.get_feature_names_out()
df = pd.DataFrame(vec.toarray(), columns=feature_names)
```

結果
![CountVectorizer.PNG](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/8ad5b8d1-1765-0b4e-11be-826a42d876dd.png)

## 結論にたどり着くまで

使い方については上記ですが、そこそこで沼っていたので、以下はたどり着くまでの記録です。

### 公式ドキュメントのサンプルを確認する

ベクトル化について調べていたところ、scikit-learnの[CountVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.CountVectorizer.html)を使用すればできそうだということがわかったので、まず公式のドキュメントを見ました。まあ当然ですが英語です。

```py:ドキュメントのExamples
corpus = [
    'This is the first document.',
    'This document is the second document.',
    'And this is the third one.',
    'Is this the first document?',
]
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(corpus)
```

### ケース1：そのまま日本語を入力する

試しにそのまま日本語を入れてみました。一文字ずつ区切られてしまっていますね...

```py
corpus = [
    'これは最初のドキュメントです。',
    'このドキュメントは2番目のドキュメントです。',
    'そして、これは3番目のものです。',
    'これは最初のドキュメントですか?',
]
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(corpus)
X.get_feature_names_out()

# 出力
# array(['2', '3', '?', '、', '。', 'か', 'こ', 'し', 'す', 'そ', 'て', 'で', 'の',
#        'は', 'も', 'れ', 'キ', 'ト', 'ド', 'メ', 'ュ', 'ン', '初', '最', '番', '目'],
#       dtype=object)
```

### ケース2：日本をスペースで区切る


英語の文章は単語がスペースで区切られています。同じように日本語も区切ってみます。

一見良さそうに見えますが、「は」「の」などの一文字の語が消えています。英語であれば一文字の単語は「a」「I」などであり、分析する場合に不要なため自動で削除しているようです。日本語の場合は「机」「雨」など一文字の単語は多数あるため、これでは困ります。

```py: スペース区切りで処理
corpus = [
    'これ は 最初 の ドキュメント です 。',
    'この ドキュメント は 2 番目 の ドキュメント です 。',
    'そして 、 これ は 3 番目 の もの です 。',
    'これ は 最初 の ドキュメント です か ?',
]
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(corpus)
vectorizer.get_feature_names_out()

# 出力
# array(['この', 'これ', 'そして', 'です', 'もの', 'ドキュメント', '最初', '番目'], dtype=object)
```

### ケース3：token_pattern を指定する

一文字が消える問題について調べていたところ、いくつかの記事で `token_pattern='(?u)\\b\\w+\\b'` をパラメータに指定しているものを見つけました。試してみます。

一文字の語も拾っているようですね。でも「、」「。」などの記号は消えているようです。分析するときには不要なので困りませんが、どういう基準で消えているのかわからないのでちょっと もやっとしますね。

```py: token_patternを指定
corpus = [
    'これ は 最初 の ドキュメント です 。',
    'この ドキュメント は 2 番目 の ドキュメント です 。',
    'そして 、 これ は 3 番目 の もの です 。',
    'これ は 最初 の ドキュメント です か ?',
]
vectorizer = CountVectorizer(token_pattern='(?u)\\b\\w+\\b')
X = vectorizer.fit_transform(corpus)
vectorizer.get_feature_names_out()

# 出力
# array(['2', '3', 'か', 'この', 'これ', 'そして', 'です', 'の', 'は', 'もの', 'ドキュメント',
#        '最初', '番目'], dtype=object)
```

### そもそもなんでスペース区切りにする必要が？

もやっとしてしまったので、ちょっと最初に戻りましょう。
そもそも `CountVectorizer` は英語用です。英語の文章を単語区切りにした後にベクトル化を行っています。単語で区切るのはシンプルなものだと以下のように `str` -> `list` に変換しているわけですね。

`'This is the first document'` -> `['This', 'is', 'the', 'first', 'document']`

英語の場合こんな感じに、簡単なケースであればスペースで区切るだけでもに単語区切りになります。雑に言ってしまうと英語はスペースで分割するだけで単語区切りになるため、その処理が `CountVectorizer` に組み込まれています。

しかし、日本語の文章を単語で区切るのはそんなに簡単ではないため、[MeCab](https://taku910.github.io/mecab/)、[Janome](https://mocobeta.github.io/janome/)、[GiNZA](https://megagonlabs.github.io/ginza/)といった形態素解析器を使用する必要があります。省略していましたが、単語をスペース区切りにするのは下記の処理を行っていました。
つまり文章を単語区切りのリストにした後に、スペース区切りで文字列結合していたんですよ...！！なんて意味のない...

```py
from janome.tokenizer import Tokenizer
t = Tokenizer()
corpus = [
    'これは最初のドキュメントです。',
    'このドキュメントは2番目のドキュメントです。',
    'そして、これは3番目のものです。',
    'これは最初のドキュメントですか?',
]
for s in corpus:
    print(' '.join([token.surface for token in t.tokenize(s)]))

# # 出力
# 'これ は 最初 の ドキュメント です 。',
# 'この ドキュメント は 2 番目 の ドキュメント です 。',
# 'そして 、 これ は 3 番目 の もの です 。',
# 'これ は 最初 の ドキュメント です か ?',
```

### ケース4：analyzer を指定する

さて、やりたいのはベクトル化処理です。日本語の文章を単語区切りにするのは英語と比べて難しいので `scikit-learn` ではなく `Janome` などの形態素解析器に任せましょう。そうすると `CountVectorizer` 上で行っている単語区切り処理が邪魔です。そこで、その処理をしないように `analyzer=lambda x: x` を指定します（結論と同じ内容です）。こうすると区切り処理なしでそのままベクトル化してくれます。

想定通りの結果になっていますね。

```py: analyzer=lambda x: x を指定
corpus = [
    ['これ', 'は', '最初', 'の', 'ドキュメント', 'です', '。'],
    ['この', 'ドキュメント', 'は', '2', '番目', 'の', 'ドキュメント', 'です', '。'],
    ['そして', '、', 'これ', 'は', '3', '番目', 'の', 'もの', 'です', '。'],
    ['これ', 'は', '最初', 'の', 'ドキュメント', 'です', 'か', '?']
]
vectorizer = CountVectorizer(analyzer=lambda x: x)
X = vectorizer.fit_transform(corpus)
vectorizer.get_feature_names_out()

# 出力
# array(['2', '3', '?', '、', '。', 'か', 'この', 'これ', 'そして', 'です', 'の', 'は',
#        'もの', 'ドキュメント', '最初', '番目'], dtype=object)
```

# まとめ

日本語をscikit-learnのCountVectorizerやTfidfVectorizerでベクトル化するときは`alalyzer`を指定しましょうという話でした。

ちなみに `alalyzer` に`Janome`などの形態素解析処理を組み込むこともできます。ただ、形態素解析ってそこそこ時間がかかるんですよね。そのため事前に文章を形態素解析しておいて、DBなどに保存して使用する、なんてことをすることもあると思います。そういった理由もあって形態素解析は外出ししておく形で記事内では記載しています。

# 蛇足

メインの内容とは外れるので蛇足としてまとめの後に。

## Appendix1：入力は比較可能なリストであればOK

単語には同じ単語でも複数の品詞（名詞、動詞など）を持つものがあります。分析するときに別の単語として区別したいときもあると思います。`CountVectorizer`に品詞を加えてしまっても問題ありません。なんの問題もなく処理できます。

```py
# 単語はてきとーです
corpus = [
    [('雨', '名詞'), ('晴れ', '動詞'), ('曇り', '名詞'), ('雨', '名詞'), ('曇り', '動詞')],
    [('雨', '名詞'), ('晴れ', '名詞'), ('曇り', '名詞'), ('曇り', '名詞')],
]

vectorizer = TfidfVectorizer(analyzer=lambda x: x)
X = vectorizer.fit_transform(corpus)
vectorizer.get_feature_names_out()

# 出力：品詞が違えば別のもととして処理されている
# array([['晴れ', '動詞'], ['晴れ', '名詞'], ['曇り', '動詞'], ['曇り', '名詞'],
#        ['雨', '名詞']], dtype=object)
```

なんなら要素同士が比較可能であれば何でもOKです（使い道はわかりませんが...）。

```py
corpus = [
    [(1, 3), (3, 4), (5, 1), (2, 4), (5, 1)],
    [(1, 3), (3, 4), (4, 1), (1, 3)],
]
X = vectorizer.fit_transform(corpus)
vectorizer.get_feature_names_out()
# array([[1, 3], [2, 4], [3, 4], [4, 1], [5, 1]], dtype=object)


corpus = [
    [('雨', 3), ('晴れ', 4), ('曇り', 1), ('雷', 4), ('曇り', 1)],
    [('雨', 3), ('晴れ', 4), ('霰', 1), ('雨', 3)],
]
X = vectorizer.fit_transform(corpus)
vectorizer.get_feature_names_out()
# array([['晴れ', 4], ['曇り', 1], ['雨', 1], ['雨', 3], ['雨', 4]], dtype=object)
```

## Appendix2：analyzerで形態素解析もする

`analyzer` で形態素解析を行う例です。

```py
from janome.tokenizer import Tokenizer
t = Tokenizer()
def analyzer(x):
    return [token.surface for token in t.tokenize(x)]

corpus = [
    'これは最初のドキュメントです。',
    'このドキュメントは2番目のドキュメントです。',
    'そして、これは3番目のものです。',
    'これは最初のドキュメントですか?',
]

vectorizer = CountVectorizer(analyzer=analyzer)
```

# 参考

- scikit-learnのドキュメント：[CountVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.CountVectorizer.html), [TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- [【python】sklearnのCountVectorizerの使い方](https://www.haya-programming.com/entry/2018/02/25/044525)
    - この記事書いてる途中で同じこと記事にしている方がいるのを見つけてしまった...



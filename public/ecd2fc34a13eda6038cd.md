---
title: Pythonで共起ネットワークを描く（未完成）
tags:
  - Python
  - NLP
  - KHCoder
private: false
updated_at: '2022-07-25T23:07:41+09:00'
id: ecd2fc34a13eda6038cd
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

経緯

- [KH Coder](https://khcoder.net/) を使って共起ネットワークを作ってた
- 自動で処理したい...Perlでできるらしいけど、Perlわかんにゃい (・へ・)
- Pythonでできたらなー...自分で作るか！

そんなわけでPythonで共起ネットワーク作りたいと思います。
KH Coderの共起ネットワークの見た目ってすごい綺麗なんですよね（下図）。なのでKH Coderの出力とおおよそ似たような形になるように目指していきたいと思います...
が、結論を言うとグラフ描画がうまく行っていません。そのうち再度挑戦します。

![KH.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/2bd4bba5-5986-83e1-b4bd-a5c797d3f89f.png)

# 処理内容

実施した処理手順としては以下です。

1. janomeで形態素解析
1. 描画に使用する語を抽出
1. 共起ネットワークの作成
1. 共起ネットワークの描画

今回、データはKH Coderにサンプルとしてある「kokoro.xls」を使用しました。

## import 

```py
import numpy as np
import pandas as pd
import janome
from janome.tokenizer import Tokenizer
from tqdm.auto import tqdm
import unicodedata
import itertools
import re
import string
from sklearn.feature_extraction.text import CountVectorizer

import networkx as nx
import networkx.algorithms.community as nx_comm
from matplotlib import pyplot as plt
import seaborn as sns
import japanize_matplotlib
sns.set(font="IPAexGothic")
```

## janomeで形態素解析

まず文を単語に区切るために形態素解析を行います。形態素解析はMeCabなどが有名だと思いますが、Windowsだとインストールが手間なので、今回はjanomeを使用しました。

```py
def get_tokens(texts, normalize=False):
    # 形態素解析
    t = Tokenizer()
    tokens_list = []
    for text in tqdm(texts):
        tokens = []
        if normalize:
            text = unicodedata.normalize('NFKC', text)

        # 後で使用するので品詞も格納する
        for token in t.tokenize(text):
            tokens.append(tuple([token.surface, *token.part_of_speech.split(','), token.base_form]))
        tokens_list.append(tokens)
        
    return tokens_list
```

## 描画に使用する語を抽出

形態素解析をした状態だと共起ネットワークを作成する上で不要な語（助詞など）が含まれているため、必要な語のみを抽出します。

```py
def word_extract(tokens_list):
    # 単語フィルター
    # ※ 全角記号などが残ってしまうので、要改善
    
    pat = re.compile(r'^[あ-ん]+$')
    pat_symbol = re.compile(fr'^[{string.punctuation}]+$')

    def cond(token):
        # 記号のみの語は削除
        # ひらがなのみ の語（「こと」「ため」など）は削除
        return ( not pat.match(token[-1]) and not pat_symbol.match(token[-1]) and
            (
                (token[1] == '名詞' and (token[2] not in ('非自立', '代名詞',  '数', '接尾', '接続詞的') ))
            or (token[1] == '動詞') and (token[2] not in ('非自立', ) )
            or (token[1] == '形容詞') and (token[2] not in ('非自立', ) )
            or (token[1] == '副詞') and (token[2] not in ('非自立', ) )
            )
        )  

    # 原型が同じでも品詞が異なる場合があるので（原型, 品詞）の形で格納
    tokens_filter = []
    for tt in tokens_list:
        tokens_filter.append([(token[-1], token[1]) for token in tt if cond(token)])
        
    return tokens_filter
```

不要な語を除いたので、ここから共起ネットワークに描画する語を絞り込みます。
KH Coderのマニュアルを見ると

> 出力される語の数が 75 前後になるような，きりのよい数値（5 の倍数）が「最小出現数」として自動的に入力されている。

とのことなのでだいたい同じようにします。

```py
def get_use_words(tokens_filter):
    # 使用語の一覧作成
    uniq = np.unique(sum(tokens_filter, []), axis=0, return_counts=True)
    wc = sorted(list(zip(*uniq)), key=lambda x:x[-1])[::-1]    
    cnt = np.array([c[-1] for c in wc])

    # ざっくり雑に75になるようなしきい値
    if cnt[75] % 5 == 0:
        th = cnt[75]
    else:
        th = cnt[75] // 5 * 5 + 5

    use_words = [tuple(x[0]) for x in wc[:len(cnt[cnt >= th])]]
    return use_words

def get_use_token(tokens_filter, use_words):
    # 使用する語のみにする
    use_tokens = []
    for line in tokens_filter:
        ww = [w for w in line if w in use_words]
        use_tokens.append(ww)
    return use_tokens
```

## 共起ネットワークの作成

次に、絞り込んだ単語から共起ネットワークを作成するのですが、ここからは「[はじめての自然言語処理](https://www.ogis-ri.co.jp/otc/hiroba/technical/similar-document-search/part6.html)」のページをかなり参考にしています（関数化したりDataFrameを使用したりしただけ）。
解説等も詳しく書かれているのでこちらのページを参照したほうがいいかも知れません。共起ネットワーク以外も自然言語処理についてまとめられているので、おすすめです。

### jaccard係数計算

共起ネットワークを作成するためのjaccard係数を計算します。
jaccard係数は単語間の繋がり度合い？のようなものです。

```py
def compute_bow(use_tokens):
    # BoW
    cv = CountVectorizer(analyzer=lambda x:x, min_df=1)
    bows = cv.fit_transform(use_tokens).toarray()
    names = [w[0][0] for w in sorted(cv.vocabulary_ .items(), key=lambda x: x[1])]
    
    return pd.DataFrame(bows, columns=names)

def calc_cooccurrence(bow):
    length = bow.shape[0]
    clear_diag = np.ones(length, dtype=np.int64) - np.eye(length, dtype=np.int64)
    array = np.minimum.outer(bow, bow) * clear_diag
    return (array > 0).astype(np.int64)

def compute_jaccard(df_bows):
    # jaccard係数計算
    vocab_size = len(df_bows.columns)
    bows = df_bows.values
    intersection = np.zeros([vocab_size, vocab_size]).astype(np.int64)
    for bow in tqdm(bows):
        intersection += calc_cooccurrence(bow)

    sum_occurrences = np.sum((bows > 0).astype(np.int64), axis=0)
    union = np.add.outer(sum_occurrences, sum_occurrences) - intersection
    union[np.where(union==0)[0]] = 1 # to avoid division by zero.
    jaccards = intersection / union

    df_jaccards = pd.DataFrame(jaccards, columns=df_bows.columns, index=df_bows.columns)
    return df_jaccards
```

### グラフの作成

jaccard係数をもとにグラフを作成します。

```py
def create_graph(df_jaccards, topk=60):
    # グラフ作成
    G = nx.Graph()
    G.add_nodes_from([w for w in df_jaccards.columns])

    scores = df_jaccards.values
    flatten_scores = scores.reshape([-1])
    # "*2" は scores は同じ値が対角線両側の二回ずつ入る為
    thresh = np.sort(flatten_scores)[::-1][topk*2] 

    # Top K 以上の score(Jaccard係数) の単語ペアにエッジを張る
    for (i,j) in itertools.combinations(range(scores.shape[0]), 2):
        weight = scores[i][j]
        if weight > thresh:
            G.add_edge(df_jaccards.columns[i], df_jaccards.columns[j], weight=weight)

    # エッジが張られていない頂点を削除
    isolated = [n for n in G.nodes if len([i for i in nx.all_neighbors(G, n)]) == 0]
    for n in isolated:
        G.remove_node(n)
    return G
```

## 共起ネットワークの描画

共起ネットワークを描画します。

```py
def plot_network(G, freqs, k=None, iterations=50, fontsize=12, node_size_factor=30000, edge_width_factor=20):
    plt.figure(figsize=(12, 12))

    # ノード配置
    layout = nx.fruchterman_reingold_layout(G, k=k, seed=42, iterations=iterations)
    
    # ノードの大きさ（単語の頻度）
    pr_values = np.array([freqs[node] for node in G.nodes()])

    # 連結ノードを同じ色にする
    comms = nx.connected_components(G)
    connecteds = []
    colors = []
    for i, c in enumerate(comms):
        connecteds.append(c)
        colors.append(1/12 * i)

    node_colors = []
    for node in G.nodes():
        for i, c in enumerate(connecteds):
            if node in c:
                node_colors.append(colors[i])
                break
    
    # ノードの描画
    nx.draw_networkx_nodes(G, layout, node_color=node_colors, cmap=plt.cm.get_cmap('Set3'), 
        alpha=0.5, node_size=pr_values * node_size_factor)

    # ラベルの描画
    labels = nx.draw_networkx_labels(G, layout)
    for t in labels.values():
        t.set_fontproperties("IPAexGothic")
    
    # エッジの描画
    nx.draw_networkx_edges(G, layout, alpha=0.8, edge_color="darkgrey", style='-', width=2)
    plt.axis('off')
```

## 結果

関数定義が上記で完了したので、あとは実行します。

```py
# テキスト読み込み
path = r'C:\khcoder3\tutorial_jp\kokoro.xls'
df = pd.read_excel(path)
texts = df['テキスト'].tolist()

# 形態素解析
tokens_list = get_tokens(texts)

# 使用する語を抽出
tokens_filter = word_extract(tokens_list)
use_words = get_use_words(tokens_filter)
use_tokens = get_use_token(tokens_filter, use_words)

# 共起ネットワーク作成
df_bows = compute_bow(use_tokens)
df_jaccards = compute_jaccard(df_bows)
G = create_graph(df_jaccards, topk=60)

# グラフの描画
freqs = df_bows.sum().to_dict()
cmax = df_bows.sum().max()
freqs = {k:v/cmax for k, v in freqs.items()}
plot_network(G, freqs, node_size_factor=5000)
```

出力された画像が以下です。うーん。。。

![python共起ネットワーク.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/c8abc023-ef8f-d4f5-eb98-5664a7b2d120.png)

# まとめ

Pythonで共起ネットワークを描画しました。が、KH Coderのようにきれいには描画できませんでした。
あとはノードの配置さえうまくできればいいと思うのですが、そこが一番難しいようです。
レイアウトも`fruchterman_reingold_layout` とか `kamada_kawai_layout` とか `spring_layout` とかを試したのですが、なかなかきれいになりませんでした。
また、KH Coderのノードの色分けは `modularity` というものを使用しているようでしたが、その辺もうまくいかず...

KH Coderのグラフ描画はRを使用しているようなので、そのあたりを調べてまたどこかで挑戦しようと思います。~~というか誰かやっていないだろうか...~~

# 参考

- [KH Coder](https://khcoder.net/)
- [はじめての自然言語処理](https://www.ogis-ri.co.jp/otc/hiroba/technical/similar-document-search/part6.html)
    - 共起ネットワーク以外も勉強になります

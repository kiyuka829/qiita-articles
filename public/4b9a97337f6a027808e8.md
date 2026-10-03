---
title: NumPyで線分の交差判定がしたい！
tags:
  - Python
  - numpy
private: false
updated_at: '2023-11-30T00:29:59+09:00'
id: 4b9a97337f6a027808e8
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

たくさんいる線分ちゃんたちがXXXしているのか知りたいんです！！！

...そんなわけで線分の交差判定をやります。

# 結論

できた！！！

```py
import numpy as np
def is_line_intersection(lines1, lines2):
    a, b = lines1[:, 0, :], lines1[:, 1, :]
    c, d = lines2[:, 0, :], lines2[:, 1, :]

    a = a[:, None, :]
    b = b[:, None, :]
    c = c[None, :, :]
    d = d[None, :, :]

    return (
        (np.cross(a - b, a - c) * np.cross(a - b, a - d) < 0)
        & (np.cross(c - d, c - a) * np.cross(c - d, c - b) < 0)
    )
```

さすがChatGPT先生！！

# 経緯

線分の交差判定の方法を調べていたのですが、1対1での判定はあっても、N対Nでの判定が見つからず、不思議に思ってこの記事を作成しました。

# 計算速度

交差判定についてはいろんなところで解説があるのでここでは解説しません。そのため結論のコードで終わりではあるのですが、これで終わるのも寂しいので計算速度の話を。

Pythonのループ処理は遅いです。そのため、計算速度を気にする場合は可能な限りPython上でのループ処理を減らして、numpyなどのようなCやC++で書かれた高速なライブラリで処理を行うことにより計算を速くすることができます。
今回はnumpyの行列演算を使用することでN対Nの計算を一度に行っています。これをPythonで書くとN x Nの2重ループになるため、かなり遅くなります。

## 実験

試しに計算速度を以下の3パターンで検証してみます。
- N:Nの計算を一度行う方法
- 1:Nの計算をN回繰り返す方法
- 1:1の計算を N x N 回繰り返す方法

```py:交差判定時間計測
# N:N
def is_line_intersection1(lines1, lines2):
    a, b = lines1[:, 0, :], lines1[:, 1, :]
    c, d = lines2[:, 0, :], lines2[:, 1, :]

    a = a[:, None, :]
    b = b[:, None, :]
    c = c[None, :, :]
    d = d[None, :, :]

    return (
        (np.cross(a - b, a - c) * np.cross(a - b, a - d) < 0)
        & (np.cross(c - d, c - a) * np.cross(c - d, c - b) < 0)
    )

# 1:N
def is_line_intersection2_(line, lines):
    a, b = line.astype(np.float64)
    c, d = lines[:, 0, :], lines[:, 1, :]

    return (
        (np.cross(a - b, a - c) * np.cross(a - b, a - d) < 0)
        & (np.cross(c - d, c - a) * np.cross(c - d, c - b) < 0)
    )

def is_line_intersection2(lines1, lines2):
    return np.array([is_line_intersection2_(line, lines2) for line in lines1])

# 1:1
def is_line_intersection3_(a, b, c, d):
    ax, ay, bx, by, cx, cy, dx, dy = *a, *b, *c, *d
    dax, day = ax - bx, ay - by
    dcx, dcy = cx - dx, cy - dy
    ta = dcx * (ay - cy) + dcy * (cx - ax)
    tb = dcx * (by - cy) + dcy * (cx - bx)
    tc = dax * (cy - ay) + day * (ax - cx)
    td = dax * (dy - ay) + day * (ax - dx)
    return tc * td < 0 and ta * tb < 0

def is_line_intersection3(lines1, lines2):
    return np.array([[is_line_intersection3_(*line1, *line2) for line2 in lines2]  for line1 in lines1])

# 線分ランダム生成
def generate_random_lines(num_lines, x_range, y_range):
    points = np.random.uniform([x_range[0], y_range[0]], [x_range[1], y_range[1]], (num_lines, 2, 2))
    return points


num_lines = 1000
x_range = (0, 10)
y_range = (0, 10)

lines1 = generate_random_lines(num_lines, x_range, y_range)
lines2 = generate_random_lines(num_lines, x_range, y_range)

%time is_line_intersection1(lines1, lines2)
%time is_line_intersection2(lines1, lines2)
%time is_line_intersection3(lines1, lines2)
```

## 結果

Nを100,1000,10000で試した結果が以下です。Google Colaboratory上で実行しています。
予想通り、N:Nが一番速く、1:1が一番遅いという結果になりました。

| N | N:N | 1:N | 1:1 |
|:-:|:-:|:-:|:-:|
| 100 | 3.14 ms  |  20.9 ms | 110 ms  |
| 1000  | 102 ms  | 261 ms  | 10.4 s  |
|  10000 | 8.53 s  | 13 s  | 時間がかかりすぎたので省略 |


しかし、N数が増加するにつれて、N:Nと1:Nの計算時間の差が縮小しており、桁がさらに増えると計算時間が逆転しそうです。これは、一度に計算する→大きな配列を確保する→メモリ使用量（メモリを確保する時間？）が増えた、ということが原因と考えられます。そのため、多数のデータを同時に処理するときには、メモリの使用量についても考慮する必要があるということがわかります。

...という結果ではありますが、そもそも大量にある線分の交差判定をすべて真面目に計算するのが間違っている気もします。もっと効率的なアルゴリズムがありそうです。こういった計算幾何学の問題についてのアルゴリズムは色々研究されているので調べてみると面白いかもしれませんね。

# まとめ

NumPyを使って線分の交差判定を行いました。

...適当にネタっぽく記事を書こうと思っての冒頭の始まりだったんですが、なんだか普通に書いてしまった！！おかしいね？

# 参考

衝突判定の方法はこちらを参考に（というかほぼそのまま使用）しました。

https://ikatakos.com/pot/programming_algorithm/geometry/collision_judgement

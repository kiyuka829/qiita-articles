---
title: マインクラフトで点群データから建築する
tags:
  - Python
  - minecraft
  - PointCloud
  - 点群
private: false
updated_at: '2022-06-19T16:30:30+09:00'
id: faf563f6fd6cbb1b264e
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
![岸和田城マインクラフト.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/2c7d2e79-bbd7-44fc-8a4b-6d94a254e6fb.jpeg)

# はじめに

- [以前の記事](https://qiita.com/kiyuka/items/f47f9a0e2df8225d6984)で点群をBabylon.jsで表示する
- せっかくだからくるくるするだけじゃなくて、キャラクターを歩かせたいなー
- ...むずくね？というか点数が多くなると重いよー動かないよー
- [点群をマイクラ化](https://www.youtube.com/channel/UCKpiQ9PwUZnrfGhD1T_8Lmg)してる人いる！！！まねっこしよう

ということで、点群データをマインクラフトにしようと思います。
二番煎じでも気にしない

# 点群データを準備する

点群データは[前回の記事](https://qiita.com/kiyuka/items/f47f9a0e2df8225d6984)と同じく「[岸和田城 3次元点群データ](https://www.geospatial.jp/ckan/dataset/kishiwada-castle)」の「1.zip」を使わせていただきました。間引き処理なども前回と同じです。なのでやり方についてはそちらを参照。
一応データ量の多いままでもマイクラ側で表示をアレコレしてくれるので激重になったりはしないと思います。


# マインクラフトを準備する

Pythonでマイクラを操作する方法は[こちら](https://www.youtube.com/watch?v=iK3V8q2EiI8)を参考にさせていただきました。めっちゃわかりやすいのでおすすめです。

# Pythonで建築する

準備ができたので実際に建築していきます。
Babylon.jsで行ったときは点群の色をそのまま使えたのですが、マインクラフトではゲーム内で用意されたブロックを使用する必要があるので、点群の色をブロックに変換する必要があります。

...ブロックの色定義どうすんのこれ？手作業でやるしかない？めんどくさい、と思っていたら、[Blenderの3DデータをMinecraftに送りこむ](https://www.kabuku.co.jp/developers/blender2minecraft-by-python)という記事を見つけ、GitHub上でソースコードを公開してくださっている方が！！
少し加工してありがたく使わせていただくことにしました。ありがとうございます。

```py
# 使用するブロックの定義
BLOCK_LIST = (
    ("White Wool", (0.95, 0.95, 0.95), (35, 0)),
    ("Orange Wool", (0.92, 0.53, 0.25), (35, 1)),
    ("Magenta Wool", (0.73, 0.31, 0.77), (35, 2)),
    ("Light Blue Wool", (0.43, 0.55, 0.81), (35, 3)),
    ("Yellow Wool", (0.77, 0.71, 0.11), (35, 4)),
    ("Lime Wool", (0.23, 0.75, 0.18), (35, 5)),
    ("Pink Wool", (0.84, 0.54, 0.62), (35, 6)),
    ("Grey Wool", (0.26, 0.26, 0.26), (35, 7)),
    ("Light Grey Wool", (0.62, 0.65, 0.65), (35, 8)),
    ("Cyan Wool", (0.15, 0.46, 0.59), (35, 9)),
    ("Purple Wool", (0.53, 0.23, 0.80), (35, 10)),
    ("Blue Wool", (0.15, 0.20, 0.60), (35, 11)),
    ("Brown Wool", (0.22, 0.30, 0.09), (35, 12)),
    ("Green Wool", (0.22, 0.30, 0.09), (35, 13)),
    ("Red Wool", (0.65, 0.17, 0.16), (35, 14)),
    ("Black Wool", (0, 0, 0), (35, 15)),
    ("White Stained Clay", (0.77, 0.65, 0.60), (159, 0)),
    ("Orange Stained Clay", (0.60, 0.31, 0.14), (159, 1)),
    ("Magenta Stained Clay", (0.56, 0.33, 0.40), (159, 2)),
    ("Light Blue Stained Clay", (0.44, 0.42, 0.54), (159, 3)),
    ("Yellow Stained Clay", (0.69, 0.49, 0.13), (159, 4)),
    ("Lime Stained Clay", (0.38, 0.44, 0.20), (159, 5)),
    ("Pink Stained Clay", (0.63, 0.30, 0.31), (159, 6)),
    ("Gray Stained Clay", (0.22, 0.16, 0.14), (159, 7)),
    ("Light Gray Stained Clay", (0.53, 0.42, 0.38), (159, 8)),
    ("Cyan Stained Clay", (0.34, 0.35, 0.36), (159, 9)),
    ("Purple Stained Clay", (0.44, 0.25, 0.31), (159, 10)),
    ("Blue Stained Clay", (0.27, 0.22, 0.33), (159, 11)),
    ("Brown Stained Clay", (0.28, 0.19, 0.13), (159, 12)),
    ("Green Stained Clay", (0.29, 0.32, 0.16), (159, 13)),
    ("Red Stained Clay", (0.56, 0.24, 0.18), (159, 14)),
    ("Black Stained Clay", (0.13, 0.08, 0.06), (159, 15)),
    ("Stone", (0.47, 0.47, 0.47), (1, 0)),
    ("Polished Granite", (0.63, 0.44, 0.38), (1, 2)),
    ("Oak Wood Plank", (0.66, 0.53, 0.34), (5, 0)),
    ("Spruce Wood Plank", (0.46, 0.34, 0.20), (5, 1)),
    ("Birch Wood Plank", (0.79, 0.73, 0.49), (5, 2)),
    ("Jungle Wood Plank", (0.64, 0.46, 0.31), (5, 3)),
    ("Acacia Wood Plank", (0.59, 0.32, 0.17), (5, 4)),
    ("Sponge", (0.78, 0.78, 0.31), (19, 0)),
    ("Sandstone", (0.88, 0.85, 0.64), (24, 0)),
    ("Gold Block", (0.99, 0.99, 0.36), (41, 0)),
    ("Iron Block", (0.93, 0.93, 0.93), (42, 0)),
)
```

ブロックの色の定義をしたら、あとは点を色の近いブロックに変換してマインクラフト上に配置するだけ。

```py
from mcpi import minecraft, block
import pandas as pd
import numpy as np
from tqdm.auto import tqdm
import skimage

# ブロックリストから色とブロックIDを取り出す
block_rgb = np.array([b[1] for b in BLOCK_LIST])
block_type = np.array([b[2] for b in BLOCK_LIST])

# 点群ファイル読み込み
csv = 'pointcloud.csv'
df = pd.read_csv(csv, usecols=range(6), names=list('xyzrgb'), skiprows=1)

# 点を等間隔に
eps = 1e-6
size = 0.5
df[['x', 'y', 'z']] = (df[['x', 'y', 'z']] / size + eps).round(0) * size
df_group = df.groupby(['x', 'y', 'z']).median().reset_index()
df_group[['x', 'y', 'z']] -= df_group[['x', 'y', 'z']].min()

# 点の色とブロックの色を比較して、
point_lab = skimage.color.rgb2lab(df_group[['r', 'g', 'b']].values / 255)
block_lab = skimage.color.rgb2lab(block_rgb)
diff = skimage.color.deltaE_ciede2000(point_lab.reshape(-1, 1, 3), block_lab.reshape(1, -1,  3))
# 一番近い色のブロックを使用する
indices = diff.argmin(axis=-1)
block_types = block_type[indices]

# マインクラフト上にブロックを配置する
mc = minecraft.Minecraft.create()
for i, row in tqdm(df_group.iterrows(), total=len(df_group)):
    x, y, z = row[['x', 'y', 'z']] / size
    mc.setBlock(x, z, y, block.Block(*block_types[i]))
```

# できあがり

表示するとこんな感じに。これでお城を採掘できるよ！

https://twitter.com/kiyuka_study/status/1538385200316837890

# まとめ

点群をマインクラフトのブロックにして建築しました。
前準備さえできてしまえば、データをマイクラに流すのは簡単にできますね。
今回、一部水色のブロックが謎に配置されていますが、ブロックの色定義を増やしてやればもっと実際に近い色のブロックになるのではないかなーと思います ~~（非常にめんどくさいからやってない）~~。


# 参考

- [岸和田城 3次元点群データ](https://www.geospatial.jp/ckan/dataset/kishiwada-castle)
- [点群マイクラ化:youtube](https://www.youtube.com/channel/UCKpiQ9PwUZnrfGhD1T_8Lmg)
- [Blenderの3DデータをMinecraftに送りこむ](https://www.kabuku.co.jp/developers/blender2minecraft-by-python)
    - ソースコード：[b2mine](https://github.com/taxpon/b2mine)
- [【Pythonでマイクラ操作！】自動で迷路を作成してマインクラフト上で遊んでみよう 〜 Minecraftプログラミング入門 〜](https://www.youtube.com/watch?v=iK3V8q2EiI8)

---
title: NumPyで光線と線分の交点を求めたい！
tags:
  - Python
  - numpy
private: false
updated_at: '2024-06-16T13:33:46+09:00'
id: 6075dba9763c5ebe61ca
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

いろんなところでたくさん壁にぶつかっちゃう、どじっ子れいちゃんが、どこでぶつかっちゃったのかを知りたいんです！

...そんなわけでnumpyを使って光線(ray)と線分との交点を求めます。

## 条件

- れいちゃんは任意の位置 (x, y) から、任意の方向に向かってまっすぐ歩きます
- れいちゃんは壁をぶち破りません。そんな怪力ではないです
    - つまり光線が最初にぶつかった線分の交点を求めます
- れいちゃんは頻繁にぶつかっちゃうので、一度に計算したいです

![れいちゃん.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/a3b3accd-fd8c-3968-2521-111488504bfa.png)


# できたよー！

これで、れいちゃんがどこでドジしているのかすぐに分かるね！？

```py
def find_ray_segment_intersections(points, angles, segments):
    """光線と線分の交差判定

    Args:
        points (numpy.ndarray): 光線の始点の配列。各要素は (x, y) 座標。
        angles (numpy.ndarray): 光線の角度の配列。各要素はラジアンで表される角度。
        segments (numpy.ndarray): 線分の配列。各要素は [(x1, y1), (x2, y2)] 形式の始点と終点の座標。

    Returns:
        numpy.ndarray: 交点の配列。各要素は光線が最初に交差する点の (x, y) 座標。
    """    
    
    # 光線の方向ベクトルを計算
    directions = np.array([np.cos(angles), np.sin(angles)]).T

    # 線分の始点および終点から各点へのベクトルを計算
    vectors_to_start = segments[:, 0, :] - points[:, np.newaxis, :]
    vectors_to_end = segments[:, 1, :] - points[:, np.newaxis, :]

    # 各方向ベクトルとの外積を計算
    cross_starts = np.cross(directions[:, np.newaxis, :], vectors_to_start)
    cross_ends = np.cross(directions[:, np.newaxis, :], vectors_to_end)

    # 交差判定
    intersections = cross_starts * cross_ends < 0

    # 交差する光線と線分のインデックス
    rays_indices, segments_indices = np.where(intersections)

    # 交差する線分と光線ベクトルの取得
    segment_vectors = segments[:, 1] - segments[:, 0]
    valid_segment_vectors = segment_vectors[segments_indices]
    valid_vectors_to_start = vectors_to_start[rays_indices, segments_indices]
    valid_directions = directions[rays_indices]
    valid_points = points[rays_indices]

    # 交点までの符号付き距離を計算
    denominator = np.cross(valid_segment_vectors, valid_directions)
    t = np.cross(valid_segment_vectors, valid_vectors_to_start) / denominator

    # 光線の正方向にある交点を求める
    forward_intersections = t > 0
    intersection_points = (
        valid_points[forward_intersections]
        + valid_directions[forward_intersections] * t[forward_intersections, np.newaxis]
    )

    # 正方向に交差する光線と線分のインデックス
    intersection_rays_indices = rays_indices[forward_intersections]
    intersection_segments_indices = segments_indices[forward_intersections]

    # 光線と線分の距離
    distance = t[forward_intersections]
    dist_mat = np.full(intersections.shape, np.inf)
    dist_mat[intersection_rays_indices, intersection_segments_indices] = distance

    # 光線と最小距離で交差している交点
    intersection_points_mat = np.full((*intersections.shape, 2), np.nan)
    intersection_points_mat[
        intersection_rays_indices, intersection_segments_indices
    ] = intersection_points
    min_intersection_points = intersection_points_mat[
        np.arange(len(intersections)), dist_mat.argmin(axis=1)
    ]

    return min_intersection_points
```

こんなイメージ。10回歩いて8回もぶつかるなんて、ちょっと心配になりますね？

![output.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/a298ce14-09c5-25c7-f4d3-231dd79a4842.png)


# 解説

コードの解説だよ！手順としては以下のことをやっているよ！

1. 線分と直線の交差判定
1. 交差している直線と線分のペアを抽出
1. 光線と線分の交点を求める
1. 各光線のごとに、最初に交差する点を求める

## 線分と直線の交差判定

最初は複数の線分と直線との交差判定をしています。
交差判定については、[もっと簡単に－線分交差判定－](https://www5d.biglobe.ne.jp/~tomoya03/shtml/algorithm/Intersection.htm) がわかりやすいです。

```py
# 光線の方向ベクトルを計算
directions = np.array([np.cos(angles), np.sin(angles)]).T

# 線分の始点および終点から各点へのベクトルを計算
vectors_to_start = segments[:, 0, :] - points[:, np.newaxis, :]
vectors_to_end = segments[:, 1, :] - points[:, np.newaxis, :]

# 各方向ベクトルとの外積を計算
cross_starts = np.cross(directions[:, np.newaxis, :], vectors_to_start)
cross_ends = np.cross(directions[:, np.newaxis, :], vectors_to_end)

# 交差判定
intersections = cross_starts * cross_ends < 0
```

交差判定結果の `intersections` は (光線, 線分) のマトリックス形式になっています。直線と線分が交差していれば True のマトリックスです。光線ごとにどの線分と交差しているかが格納されます。

## 交差しているデータのみを抽出

光線と線分の交点を求める前に、交差しているデータのみを抽出しています。

```py
# 交差する光線と線分のインデックス
rays_indices, segments_indices = np.where(intersections)

# 交差する線分と光線ベクトルの取得
segment_vectors = segments[:, 1] - segments[:, 0]
valid_segment_vectors = segment_vectors[segments_indices]
valid_vectors_to_start = vectors_to_start[rays_indices, segments_indices]
valid_directions = directions[rays_indices]
valid_points = points[rays_indices]
```

## 光線と線分の交点を求める

光線と線分の交点を求めています。このとき、符号付き距離を計算することで光線の正方向の交点のみを求めています。

```py
# 交点までの符号付き距離を計算
denominator = np.cross(valid_segment_vectors, valid_directions)
t = np.cross(valid_segment_vectors, valid_vectors_to_start) / denominator

# 光線の正方向にある交点を求める
forward_intersections = t > 0
intersection_points = (
    valid_points[forward_intersections]
    + valid_directions[forward_intersections] * t[forward_intersections, np.newaxis]
)
```

## 光線と線分との距離を格納する

交点は求まったので、あとは各光線ごとに「最初に交差する点」を計算すればよいです。そのために光線と線分との距離を計算します。といっても交点を求めるときに計算済みなのでそれを使用するだけです。

また、距離を (光線, 線分) のマトリックスの形式に格納することで、各光線ごとに処理できるようにします。一次元である `distance` をマトリックス形状にする処理はちょっとテクニカルかも？

```py
# 正方向に交差する光線と線分のインデックス
intersection_rays_indices = rays_indices[forward_intersections]
intersection_segments_indices = segments_indices[forward_intersections]

# 光線と線分の距離
distance = t[forward_intersections]
dist_mat = np.full(intersections.shape, np.inf)
dist_mat[intersection_rays_indices, intersection_segments_indices] = distance
```

## 各光線のごとに、最初に交差する点を求める

最後に、光線ごとの一番近い交点を求めてできあがり！

```py
# 光線と最小距離で交差している交点
intersection_points_mat = np.full((*intersections.shape, 2), np.nan)
intersection_points_mat[
    intersection_rays_indices, intersection_segments_indices
] = intersection_points
min_intersection_points = intersection_points_mat[
    np.arange(len(intersections)), dist_mat.argmin(axis=1)
]
```

# まとめ

複数の光線（半直線）と線分の交差判定でした。
N x M の計算をループ処理無しで書けてしまうNumPyって強力ですね。

これで、れいちゃんがたくさん壁にぶつかっても安心だね！？でも歩きスマホは危ないからやめようね？

# 参考

交差判定

https://www5d.biglobe.ne.jp/~tomoya03/shtml/algorithm/Intersection.htm

交点の計算

https://www.nekonecode.com/math-lab/pages/collision2/line-and-segment/

# おまけ

最初は線分データをランダム生成していたのですが、気に入らなかったので（？）それっぽい線分のデータを作るために画像から線分のデータ作っていました。左の画像から右の画像を作る過程です。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2703301/fac7a723-142c-2309-a592-fe2ba3f216e6.png)

おまけなのでコードだけ

<details><summary>コード</summary>

結果とかの描画関数

```py
import cv2
from PIL import Image, ImageDraw, ImageFilter

def draw_intersection_ray_segments(
    points=[],
    angles=[],
    rays=[],
    segments=[],
    img=None,
    img_size=(800, 800),
):
    if img is None:
        img = Image.new("RGB", img_size, "white")
    draw = ImageDraw.Draw(img)

    # 点の描画
    def draw_circle(draw, point, color):
        draw.ellipse(
            [point[0] - 3, point[1] - 3, point[0] + 3, point[1] + 3],
            fill=color,
            outline=color,
        )

    # 光線の描画（衝突あり）
    for segment in rays:
        start = tuple(segment[0].astype(int))
        end = tuple(segment[1].astype(int))
        tipLength = 10 / np.power(segment[0] - segment[1], 2).sum() ** 0.5
        npimg = cv2.arrowedLine(
            np.array(img), start, end, (243, 152, 0), 2, tipLength=tipLength
        )

        img = Image.fromarray(npimg)
        draw = ImageDraw.Draw(img)
        draw_circle(draw, start, "pink")
        draw_circle(draw, end, "blue")

    # 光線の描画（衝突なし）
    ray_length = img.size[0] * img.size[1]
    for point, angle in zip(points, angles):
        end_point = point + np.array([np.cos(angle), np.sin(angle)]) * ray_length
        draw.line(tuple(map(tuple, [point, end_point])), fill="skyblue", width=3)
        draw_circle(draw, point, "pink")

    # セグメントの描画
    for segment in segments:
        draw.line(tuple(map(tuple, segment)), fill="black", width=2)

    return img
```

画像から線分取得

```py
img = Image.open("sample.png").convert("RGB")

# 画像を2値化する
img_gray = img.convert("L")
img_bin = img_gray.point(lambda x: 0 if x < 250 else 255)

# opencvで輪郭抽出して頂点の座標を取得する
contours, _ = cv2.findContours(
    ~np.array(img_bin), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
)

# 頂点のリストを線分のリストにする
segments = []
for contour in contours:
    contour = contour.squeeze()
    for i in range(len(contour) - 1):
        segments.append([contour[i], contour[i + 1]])
    segments.append([contour[-1], contour[0]])

segments = np.array(segments)
```

画像から適当に光線設定

```py
# れいちゃんは壁の中には入れない
img_erode = img_bin.filter(ImageFilter.MinFilter(25))
all_points = np.array(np.where(np.array(img_erode) == 255)[::-1]).T

N = 10
indices = np.random.choice(len(all_points), size=N, replace=False)
points = all_points[indices]
angles = np.random.rand(N) * np.pi * 2
```

交点を計算して画像に描画

```py
intersection_points = find_ray_segment_intersections(points, angles, segments)
is_intersection = ~np.isnan(intersection_points).any(axis=1)
draw_intersection_ray_segments(
    points=points[~is_intersection],
    angles=angles[~is_intersection],
    rays=np.stack([points, intersection_points], axis=1)[is_intersection],
    # segments=segments, # 線分を表示したいなら
    img=img, 
    img_size=img.size,
)
```

</details>

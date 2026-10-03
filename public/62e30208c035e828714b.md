---
title: Information Delivery Specification (IDS) をゆるく説明する
tags:
  - IFC
private: false
updated_at: '2025-11-16T10:38:08+09:00'
id: 62e30208c035e828714b
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

この記事はIDSについてゆるく説明する記事だよ。

Information Delivery Specification（IDS）は、IFCファイルに指定のデータが含まれているか、をチェックするルール（仕様）みたいなものだよ。正しい説明とかは[公式ドキュメント](https://github.com/buildingSMART/IDS/blob/development/Documentation/UserManual/README.md)を読んでね。ここではそんな厳密な説明はしないよ。ゆる～くふんわりやっていくよ。

あ、ちなみにIDSのバージョン1.0の説明だよ。できたてほやほやだね？

# できること

IDSはIFCファイルをチェックするルールの設定を行うものだよ。だから、できることというよりも、どういうルールを指定できるか、と言っても良いかもね。指定できる要素は大きく分けて2つあって「データが存在しているか」「属性が設定されているか」の2つになるよ。

細かく分けると次のようなルールが指定できるんだよ。

1. IFCには 〇〇 のデータが存在している必要がある  
1. IFCには 〇〇 のデータが存在していてはいけない  
1. IFCに 〇〇 のデータが存在し、かつそのデータの □□ 属性には ×× の値を設定する必要がある  
1. IFCに 〇〇 のデータが存在している場合、そのデータの □□ 属性には ×× の値を設定する必要がある 
1. IFCに 〇〇 のデータが存在し、かつそのデータに □□ 属性が設定されているなら、×× の値を設定する必要がある  
1. IFCに 〇〇 のデータが存在している場合、そのデータに □□ 属性が設定されているなら、×× の値を設定する必要がある  
1. IFCに 〇〇 のデータが存在し、かつそのデータの □□ 属性には ×× の値を設定してはいけない   
1. IFCに 〇〇 のデータが存在している場合、そのデータの □□ 属性には ×× の値を設定してはいけない

こういったルール設定によって、IFCファイルに指定のデータが存在しているか、属性が設定されているか、みたいなチェックができるわけだね。
ただ、IDSはあくまでルールなので、IFCがこのルールに従っているかのチェックは、なにかしらのソフトウェアで行う形になるんだよ。たとえば、[IfcTester](https://docs.ifcopenshell.org/ifctester.html) とかでチェックできるね。

---

ちなみに ↑ は公式ドキュメントの [この部分](https://github.com/buildingSMART/IDS/blob/development/Documentation/UserManual/specifications.md) の説明なんだよ。...ホントダヨーウソジャナイヨー(*ΦωΦ)

# 指定できるデータとか属性

「できること」の説明にあった □□の属性 には指定できるものが決まっていて、6種類の Facet と呼ばれる属性が指定できるんだよ。具体的には Entity, PartOf, Classification, Attribute, Property, Material が指定できるよ。
それぞれの属性が何かは [公式ドキュメント](https://github.com/buildingSMART/IDS/blob/development/Documentation/UserManual/README.md) を見てね。この記事では6種類の属性を指定できるんだなー、くらいに思っておけば大丈夫だよ。

それと 〇〇のデータ、については指定の属性値が入ったデータ、と言い換えても良いかもね。たとえば、Entity が ×× で Property が ×× のデータ、みたいな感じだね。

> 「【〇〇のデータ】には、【□□の属性】に【××の値】が設定されている必要がある」
> → 【Entity が ×× で Property が ×× のデータ】 には 【Material の属性】 に 【××の値】 が設定されている必要がある

---

<details><summary>細かい話だよ。読まなくて大丈夫だよ。</summary>

「できること」での表記の「□□ 属性が設定されているなら」の意味だが「Facetの属性が設定されているなら」ではない。各Facetごとに条件が異なる。

- Entity, PartOf: 設定不可能
- Classification: System の指定の値が設定されていれば
- Property: PropertySet, BaseName の指定の値が設定されていれば
- Attribute: Attribute Name の属性が存在していれば
- Material: Material が設定されていれば

よくわからないって？だから読まなくて大丈夫なんだってば。

</details>

# できることをもうちょっと詳しく

ここからは できること 8 種類について具体例を挙げつつもうちょっと説明していくよ。
もう一度ざっくり整理しておくね。

1. 存在必須
1. 存在禁止
1. 存在必須 + 指定属性の設定必須
1. 存在していれば、指定属性の設定必須
1. 存在必須 + もし属性が設定されていれば、指定の値設定が必須
1. 存在していて、属性が設定されていれば、指定の値設定が必須
1. 存在必須 + 指定属性値の設定禁止
1. 存在していれば、指定属性値の設定禁止

ちなみに、8個も覚えらんないよ！っていう人は、3つ目の「存在必須 + 属性必須」だけ覚えれば大丈夫だよ。タブンネ。

## 1. 存在必須

IFCファイルには 〇〇のデータが最低1つは存在する必要がある、というルールだよ。

たとえば、IFC ファイルには IfcSite が必須、みたいなルールが設定できるね。

<details><summary>IDSファイルサンプル: 存在必須01</summary>

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://standards.buildingsmart.org/IDS http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
  <ids:info>
    <ids:title>存在必須サンプル01</ids:title>
  </ids:info>
  <ids:specifications>
    <ids:specification ifcVersion="IFC2X3" name="IfcSite Required"
      description="IfcSiteさん、あなたにはいてもらわないと困るんです！">
      <ids:applicability minOccurs="1" maxOccurs="unbounded"> <!-- 存在必須 -->
        <ids:entity>
          <ids:name>
            <ids:simpleValue>IFCSITE</ids:simpleValue>
          </ids:name>
        </ids:entity>
      </ids:applicability>
    </ids:specification>
  </ids:specifications>
</ids:ids>
```

</details>

あとは、xx製の窓を1つ以上に使用する必要がある、とかもできるね。

<details><summary>IDSファイルサンプル: 存在必須02</summary>

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://standards.buildingsmart.org/IDS http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
  <ids:info>
    <ids:title>存在必須サンプル02</ids:title>
  </ids:info>
  <ids:specifications>
    <ids:specification ifcVersion="IFC4" name="Window by Manufacturer"
      instructions="顧客の注文でさーどこかしらにxx製の窓を使わないといけないんだよねー。一つでも良いからさ使っておいてよ、ね？">
      <ids:applicability minOccurs="1" maxOccurs="unbounded"> <!-- 存在必須 -->
        <ids:entity>
          <ids:name>
            <ids:simpleValue>IFCWINDOW</ids:simpleValue>
          </ids:name>
        </ids:entity>
        <ids:property>
          <ids:propertySet>
            <ids:simpleValue>製品情報</ids:simpleValue>
          </ids:propertySet>
          <ids:baseName>
            <ids:simpleValue>製造者</ids:simpleValue>
          </ids:baseName>
          <ids:value>
            <ids:simpleValue>小さなソフトウェア会社</ids:simpleValue>
          </ids:value>
        </ids:property>
      </ids:applicability>
    </ids:specification>
  </ids:specifications>
</ids:ids>
```

</details>


## 2. 存在禁止

IFCファイルには〇〇のデータが存在してはいけない、というルールだよ。
たとえば IFC4 では [IfcWallStandardCase](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/ifcsharedbldgelements/lexical/ifcwallstandardcase.htm) が非推奨になっているよね？これを禁止にするとかかな？

<details><summary>IDSファイルサンプル: 存在禁止</summary>

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://standards.buildingsmart.org/IDS http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
  <ids:info>
    <ids:title>存在禁止サンプル</ids:title>
  </ids:info>
  <ids:specifications>
    <ids:specification ifcVersion="IFC4 IFC4X3_ADD2" name="IfcWallStandardCase Prohibited"
      description="あ、IfcWallStandardCaseちゃんはここから先は一方通行でーす通れませーん^_^">
      <ids:applicability minOccurs="0" maxOccurs="0"> <!-- 存在禁止 -->
        <ids:entity>
          <ids:name>
            <ids:simpleValue>IFCWALLSTANDARDCASE</ids:simpleValue>
          </ids:name>
        </ids:entity>
      </ids:applicability>
    </ids:specification>
  </ids:specifications>
</ids:ids>
```

</details>

## 3. 存在必須 and 属性必須

IFCファイルには〇〇のデータが必須で、そのデータには指定の属性設定が必須、というルールだよ。

たとえば、IfcWall が必須で、その全てには耐火性能が必須、みたいなルールだね。

<details><summary>IDSファイルサンプル: 存在必須 and 属性必須</summary>

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://standards.buildingsmart.org/IDS http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
  <ids:info>
    <ids:title>存在必須 and 属性値必須サンプル</ids:title>
  </ids:info>
  <ids:specifications>
    <ids:specification ifcVersion="IFC4" name="IfcWall Required with FireRating"
      description="うおー壁は燃えぬぞ！燃えるのは魂だけだぜ！！！！">
      <ids:applicability minOccurs="1" maxOccurs="unbounded"> <!-- 存在必須 -->
        <ids:entity>
          <ids:name>
            <ids:simpleValue>IFCWALL</ids:simpleValue>
          </ids:name>
        </ids:entity>
      </ids:applicability>
      <ids:requirements>
        <!-- 属性必須 -->
        <ids:property cardinality="required" dataType="IFCLABEL"
          instructions="すべての壁の耐火性能は 60, 90 のいずれかである必要があります。">
          <ids:propertySet>
            <ids:simpleValue>Pset_WallCommon</ids:simpleValue>
          </ids:propertySet>
          <ids:baseName>
            <ids:simpleValue>FireRating</ids:simpleValue>
          </ids:baseName>
          <ids:value>
            <xs:restriction base="xs:string">
              <xs:enumeration value="60" />
              <xs:enumeration value="90" />
            </xs:restriction>
          </ids:value>
        </ids:property>
      </ids:requirements>
    </ids:specification>
  </ids:specifications>
</ids:ids>
```

</details>

たぶん8種類の中で一番よく使うルールなんじゃないかな？

## 4. もしデータが存在 → 属性必須

もし IFCファイルに 〇〇のデータが存在していた場合には、指定の属性値の設定必須、というルールだよ。
「3. 存在必須 and 属性必須」をデータが存在していれば、という条件付きにしたルールだね。

たとえば、もし壁が存在するなら、すべて耐火性能が必要、みたいなことができるね。

<details><summary>IDSファイルサンプル: もしデータが存在 → 属性値必須</summary>

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS"
  xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://standards.buildingsmart.org/IDS http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
  <ids:info>
    <ids:title>もし存在していれば属性必須のサンプル</ids:title>
  </ids:info>
  <ids:specifications>
    <ids:specification ifcVersion="IFC4" name="IfcWall FireRating Required If Wall Exists"
      description="壁？なくてもいいよ？でも壁があるなら...わかってるよね？">
      <ids:applicability minOccurs="0" maxOccurs="unbounded"> <!-- 存在するなら -->
        <ids:entity>
          <ids:name>
            <ids:simpleValue>IFCWALL</ids:simpleValue>
          </ids:name>
        </ids:entity>
      </ids:applicability>
      <ids:requirements>
        <ids:property cardinality="required" dataType="IFCLABEL"
          instructions="値は何でもいいけど、FireRating の設定は必須だよ">
          <ids:propertySet>
            <ids:simpleValue>Pset_WallCommon</ids:simpleValue>
          </ids:propertySet>
          <ids:baseName>
            <ids:simpleValue>FireRating</ids:simpleValue>
          </ids:baseName>
        </ids:property>
      </ids:requirements>
    </ids:specification>
  </ids:specifications>
</ids:ids>
```

</details>


## 5. 存在必須 and もし属性が設定 → 指定値必須

IFCファイルには 〇〇のデータが必須で、かつ □□の属性が設定されていた場合、指定した値を設定する必要がある、というルールだよ。
指定の属性が設定されていなくても良いけど、設定するのであれば指定の値を設定してね、という感じだね。

たとえば、壁は必須で、もしマテリアルの設定をするなら コンクリート を設定する必要がある（コンクリート以外のマテリアルが設定されていてはいけない）、みたいなことができるわけだね。

<details><summary>IDSファイルサンプル: 存在必須 and もし属性が設定 → 指定値必須</summary>

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS"
  xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://standards.buildingsmart.org/IDS http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
  <ids:info>
    <ids:title>存在必須 and もし属性が設定 → 指定値の設定必須 のサンプル</ids:title>
  </ids:info>
  <ids:specifications>
    <ids:specification ifcVersion="IFC4" name="IfcWindow Required with Colorful Happy Material"
      description="窓は絶対に必要だよ！あとさ、もしマテリアルを設定するなら 'GO!!' って値にしてね！...なんで？">
      <ids:applicability minOccurs="1" maxOccurs="unbounded"> <!-- 存在必須 -->
        <ids:entity>
          <ids:name>
            <ids:simpleValue>IFCWINDOW</ids:simpleValue>
          </ids:name>
        </ids:entity>
      </ids:applicability>
      <ids:requirements>
        <!-- もし属性が設定 → 指定値必須 -->
        <ids:material cardinality="optional"
          instructions="マテリアルを設定するなら、カラフルでハッピーな感じだと嬉しいよね！">
          <ids:value>
            <ids:simpleValue>GO!!</ids:simpleValue>
          </ids:value>
        </ids:material>
      </ids:requirements>
    </ids:specification>
  </ids:specifications>
</ids:ids>
```

</details>

## 6. もしデータが存在 → もし属性が設定 → 指定値必須

もし、IFCに 〇〇のデータ存在していて、かつ □□の属性が設定されていた場合、指定した値を設定する必要がある、というルールだよ。
「5. 存在必須 and もし属性が設定 → 指定値必須」を、データが存在していれば、という条件付きにしたルールだね。

<details><summary>IDSファイルサンプル: もし (データが存在 and 属性が設定) → 指定値必須</summary>

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS"
  xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://standards.buildingsmart.org/IDS http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
  <ids:info>
    <ids:title>もし (データが存在 and 属性が設定) → 指定値必須 のサンプル</ids:title>
  </ids:info>
  <ids:specifications>
    <ids:specification ifcVersion="IFC4" name="IfcWindow Optional with Colorful Happy Material"
      description="窓があってそれにマテリアルがあるなら、それはカラフルでハッピーなマテリアルなんだよ">
      <ids:applicability minOccurs="0" maxOccurs="unbounded"> <!-- 存在するなら -->
        <ids:entity>
          <ids:name>
            <ids:simpleValue>IFCWINDOW</ids:simpleValue>
          </ids:name>
        </ids:entity>
      </ids:applicability>
      <ids:requirements>
        <ids:material cardinality="optional"> <!-- もし属性が設定 → 指定値必須 -->
          <ids:value>
            <ids:simpleValue>GO!!</ids:simpleValue>
          </ids:value>
        </ids:material>
      </ids:requirements>
    </ids:specification>
  </ids:specifications>
</ids:ids>
```

</details>

## 7. 存在必須 and 属性値禁止

IFCファイルには 〇〇のデータが必須で、そのデータの □□の属性には指定した値は設定してはいけない、というルールだよ。

たとえば、梁は必須、でもプラスチック製にしてはいけない、みたいな？

<details><summary>IDSファイルサンプル: 存在必須 and 属性値禁止</summary>

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS"
  xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://standards.buildingsmart.org/IDS http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
  <ids:info>
    <ids:title>存在必須 and 属性値禁止 のサンプル</ids:title>
  </ids:info>
  <ids:specifications>
    <ids:specification ifcVersion="IFC4" name="IfcBeam Required without Orichalcum Material"
      description="梁は絶対に必要だけど、オリハルコンは使ったら絶対にダメだよ！">
      <ids:applicability minOccurs="1" maxOccurs="unbounded"> <!-- 存在必須 -->
        <ids:entity>
          <ids:name>
            <ids:simpleValue>IFCBEAM</ids:simpleValue>
          </ids:name>
        </ids:entity>
      </ids:applicability>
      <ids:requirements>
        <ids:material cardinality="prohibited"> <!-- 属性禁止 -->
          <ids:value>
            <ids:simpleValue>オリハルコン</ids:simpleValue>
          </ids:value>
        </ids:material>
      </ids:requirements>
    </ids:specification>
  </ids:specifications>
</ids:ids>
```

</details>


## 8. もしデータが存在 → 属性値禁止

上記を、データが存在していれば、という条件付きにしたルールだよ！

たとえば、梁が存在するのであれば、プラスチック製にしてはいけない、という感じだね。

<details><summary>IDSファイルサンプル: もしデータが存在 → 属性値禁止</summary>

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS"
  xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://standards.buildingsmart.org/IDS http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
  <ids:info>
    <ids:title>もしデータが存在 → 属性値禁止 のサンプル</ids:title>
  </ids:info>
  <ids:specifications>
    <ids:specification ifcVersion="IFC4" name="IfcBeam Optional without Adamantite Material"
      description="もし梁があるなら、アダマンタイトは使っちゃダメだよ！">
      <ids:applicability minOccurs="0" maxOccurs="unbounded"> <!-- 存在するなら -->
        <ids:entity>
          <ids:name>
            <ids:simpleValue>IFCBEAM</ids:simpleValue>
          </ids:name>
        </ids:entity>
      </ids:applicability>
      <ids:requirements>
        <ids:material cardinality="prohibited"> <!-- 属性禁止 -->
          <ids:value>
            <ids:simpleValue>アダマンタイト</ids:simpleValue>
          </ids:value>
        </ids:material>
      </ids:requirements>
    </ids:specification>
  </ids:specifications>
</ids:ids>
```

</details>


# おわり

そんなわけでゆるめのIDSの説明でしたのよ。誤解を恐れない説明を目指しました(｀・ω・´)
IDSというルールというか仕様というか、そういうきっちりした内容を記述したファイルを、あえてゆるく説明するということをやりたかったんです(・ω・｀)

きちっと要件を満たしたIFCが作成されているかのチェックはIDSに任せよう！そして人はゆるくだらっと作業しよう！？なんなら溶けてしまおう( ・∇・)㍍⊃

# 参考

公式ドキュメント

https://github.com/buildingSMART/IDS


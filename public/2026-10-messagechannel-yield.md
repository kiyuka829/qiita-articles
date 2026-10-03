---
title: 重いループ処理でUIを止めないために MessageChannel で yield する
tags:
  - JavaScript
  - TypeScript
  - MessageChannel
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# はじめに

JavaScriptで他の処理を邪魔しないように重いループ処理を実行したーい！

# 結論

できました！

```ts
// 重い処理のループ
async function processItems(items: Item[]) {
  for (const [i, item] of items.entries()) {
    heavyWork(item);

    if ((i + 1) % 100 === 0) {
      await yieldToEvents();
    }
  }
}

// これがポイント！
const yieldToEvents = (() => {
  const { port1, port2 } = new MessageChannel();
  const callbacks: (() => void)[] = [];
  port1.onmessage = () => callbacks.shift()?.();

  return () =>
    new Promise<void>((resolve) => {
      callbacks.push(resolve);
      port2.postMessage(null);
    });
})();
```

すべてCodexがやってくれました！

# 解説

解説というより、結論にたどり着くまでの流れ。

## async使えばええやろ（無理）

最初は単に非同期で呼び出ししてただけだったんですよね。
非同期呼び出しなんだからこれでメインの処理をブロックすることはないよね、と思っていました。

```ts
async function processItems(items: Item[]) {
  for (const item of items) {
    heavyWork(item);
  }
}
```

でもそんなことはないようで、なんで？と思っていたら、JavaScriptはあくまでシングルスレッドで動作しているので並列で実行してくれるわけではないようです。

このあたりはイベントループの話になるので、以下のような解説記事を読むのがおすすめです。（説明できるほど理解できていないとも言う。）

- [イベントループを裏側から腹落ちさせる：JavaScriptエンジンとブラウザの役割、TaskとMicrotaskの正体](https://zenn.dev/loglass/articles/8b0c06db7c9005)
- [JavaScriptのイベントループ](https://qiita.com/mattsu_mocha/items/18a39ec02e0e1ebf8e12)

## `setTimeout` を使うぜ（うまくいく場合もあるけど...）

そこで最初は、`setTimeout` で一瞬処理を中断してメインの処理に戻してやればいいんだ、と思って以下のようにしました。

```ts
async function processItems(items: Item[]) {
  for (const [i, item] of items.entries()) {
    heavyWork(item);

    if ((i + 1) % 100 === 0) {
      // 待ち時間0秒（？）でメインの処理に戻すことで分割して処理をする？
      await new Promise((resolve) => setTimeout(resolve, 0));
    }
  }
}
```

しかしこうしたらメインの処理には戻ったものの、`processItems` の処理がいつまで経っても戻ってきませんでした。
なんでー？と思いつつ調べていたら、MDNのドキュメントの [setTimeout() method](https://developer.mozilla.org/ja/docs/Web/API/Window/setTimeout) を見ると `delay=0` を指定しても、処理が積み重なった場合は最小4msの時間がかかるらしいです。

そうすると `setTimeout` の呼び出し回数 x 4ms がかかることになります。重い処理が数回実行されるケースでは問題なさそうですが、純粋にループ数が多い場合、この4msの積み重ねによって処理が終わらない、という状況になっていたようでした。

実際、返ってこなかった処理ではループ回数が1000万回近くになってたので、それだよそれ！ってなりました。

## MessageChannel で処理を分割する

そういうわけで `MessageChannel` を使用します。

```ts:最初のコードの再掲
async function processItems(items: Item[]) {
  for (const [i, item] of items.entries()) {
    heavyWork(item);

    if ((i + 1) % 100 === 0) {
      await yieldToEvents();
    }
  }
}

const yieldToEvents = (() => {
  const { port1, port2 } = new MessageChannel();
  const callbacks: (() => void)[] = [];
  port1.onmessage = () => callbacks.shift()?.();

  return () =>
    new Promise<void>((resolve) => {
      callbacks.push(resolve);
      port2.postMessage(null);
    });
})();
```

正直これでなんでうまくいくか正しく理解はできていないのですが、やっていることは

> メッセージを受信する処理を別のイベントとして実行させることで、現在実行している処理をいったん終了し、続きを別のタスクとして実行することで、その間にブラウザがほかの処理を行える機会を作っている

ということをしているらしいです。まあこのコードだけで言えば雑に言うと待ち時間なしで `setTimeout` をしている、くらいに思ってもらえば。（というよりそれくらいの理解しかしていない。）

## scheduler.yield() について

この記事を書いている途中で知ったのですが [`scheduler.yield()`](https://developer.mozilla.org/en-US/docs/Web/API/Scheduler/yield) というAPIもあるようです。

```ts
await scheduler.yield();
```

これが使える環境であれば、これが一番良さそうです。ただ、執筆時点では一部の主要ブラウザで未対応のようでした。

# おわりに

`MessageChannel` でループ処理を分割して非同期に実行する方法でした。
メッセージを送るという機能なのにこういう使い方ができるって面白いなーと思って記事にしました。面白いよね？

ちなみに理解できているかと言われるとそんなこともない。イベントループ難しいね？

# 参考

重い処理をどうにかしよう系の記事

- [長いタスクを最適化する（web.dev）](https://web.dev/articles/optimize-long-tasks?hl=ja)
  - 今回の内容とほぼ同じ内容を対象としている記事。この記事を書いてたら見つかった（Codexが見つけた）
- [setTimeout(…, 0) って何の意味があるの？](https://qiita.com/Yudai-HARA/items/fc5e755e17cedc1ed518)
- [フロントエンドでCPU負荷の高い計算を描画を止めずに実行する](https://zenn.dev/algoartis/articles/async_computation)
- [長いタスクを分割するscheduler.yieldという提案](https://zenn.dev/cybozu_frontend/articles/scheduler-yield)

イベントループ

- [イベントループを裏側から腹落ちさせる：JavaScriptエンジンとブラウザの役割、TaskとMicrotaskの正体](https://zenn.dev/loglass/articles/8b0c06db7c9005)
- [JavaScriptのイベントループ](https://qiita.com/mattsu_mocha/items/18a39ec02e0e1ebf8e12)
- [JavaScript のイベントループ：microtask と macrotask](https://ja.javascript.info/event-loop)

MDN

- [Scheduler: yield() method（MDN）](https://developer.mozilla.org/en-US/docs/Web/API/Scheduler/yield)
- [MessageChannel（MDN）](https://developer.mozilla.org/ja/docs/Web/API/MessageChannel)
- [Window: setTimeout() method（MDN）](https://developer.mozilla.org/en-US/docs/Web/API/Window/setTimeout)

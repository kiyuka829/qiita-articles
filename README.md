# Qiita Articles

[Qiita](https://qiita.com/kiyuka) に投稿する記事を、[Qiita CLI](https://github.com/increments/qiita-cli) で管理するリポジトリ。

## 構成

- `public/`: 記事本体。ファイル名は `YYYY-MM-内容を表すスラッグ.md` 形式。

## ローカルプレビュー

```sh
npm install
npx qiita preview
```

ブラウザで [http://localhost:8888](http://localhost:8888) を開く。

## 公開

`main` ブランチへの push をトリガーに、GitHub Actions が Qiita へ記事が反映される。

## License

- Articles, documentation, and original images: [CC BY 4.0](./LICENSE-CC-BY-4.0)
- Source code, code snippets, and configuration files: [MIT License](./LICENSE-MIT)

Unless otherwise noted, third-party materials are subject to their respective licenses.

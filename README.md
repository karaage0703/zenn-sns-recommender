# Zenn記事推薦＆SNS投稿文生成ツール

このリポジトリは、ZennのアカウントURLを入力すると、そのアカウントの過去の人気記事を分析し、SNS（Twitter/X）向けの投稿文を生成するツールです。

## 機能

- **Zennのアカウント情報取得**
  - 指定されたZennアカウントの過去記事を取得
  - 記事の「いいね数」をもとに人気記事を特定

- **SNS投稿文の生成**
  - OpenAIのLLMを活用し、SNS向けの投稿文を作成
  - 個人アカウントと企業アカウントで異なるトーンに対応

- **Gradioベースのユーザーインターフェース**
  - ZennアカウントURLの入力フォーム
  - 「個人向け / 企業向け」の選択
  - 生成された投稿文の表示（コピー可能）

## インストール

### 必要条件

- Python 3.8以上
- OpenAI APIキー

### セットアップ

1. リポジトリをクローン:

```bash
git clone https://github.com/yourusername/zenn-sns-recommender.git
cd zenn-sns-recommender
```

2. 依存パッケージをインストール:

```bash
pip install -e .
```

3. 環境変数の設定:

`.env.example`ファイルを`.env`にコピーし、OpenAI APIキーを設定します。

```bash
cp .env.example .env
# .envファイルを編集してOpenAI APIキーを設定
```

## 使い方

### コマンドラインから実行

```bash
python -m src.main
```

オプション:
- `--port`: Gradioサーバーのポート番号を指定（デフォルト: 7860）
- `--share`: Gradioの共有リンクを生成

例:
```bash
python -m src.main --port 8000 --share
```

### Dockerを使用する場合

1. 開発環境の起動:

```bash
docker compose up -d
```

2. ブラウザでアクセス:

```
http://localhost:7860
```

3. 開発環境の停止:

```bash
docker compose down
```

## 使用方法

1. ZennのアカウントURLまたはユーザー名を入力
   - 個人アカウント: `https://zenn.dev/username`、`@username`、または単に`username`
   - 企業アカウント: `https://zenn.dev/p/companyname`

2. 必要に応じて定型文を入力
   - 定型文は生成された投稿文の冒頭に追加されます
   - `{url}` は記事のURLに置き換えられます

3. 投稿のトーン（個人向け/企業向け）を選択

4. 「投稿文を生成」ボタンをクリック

5. 生成された投稿文をコピーしてSNSに投稿

## テスト

テストの実行:

```bash
pytest
```

### Dockerでのテスト実行

コンテナ内でテストを実行:

```bash
docker compose exec app pytest
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

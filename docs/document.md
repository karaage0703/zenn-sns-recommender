# 要件・設計書

## 1. 要件定義

### 1.1 基本情報
- **ソフトウェア名称**: Zenn記事推薦＆SNS投稿文生成ツール  
- **リポジトリ名**: zenn-sns-recommender  

### 1.2 プロジェクト概要

本プロジェクトは、ZennのアカウントURLを入力すると、そのアカウントの過去の人気記事を分析し、SNS（Twitter）向けの投稿文を生成するツールを開発することを目的としています。  
LLM（OpenAI API）を活用し、個人アカウントと企業アカウントの両方に適した投稿文を作成します。  
投稿は手動で行う形とし、ユーザーが簡単にコピー＆投稿できるようにします。  

### 1.3 機能要件

#### 1.3.1 基本機能
- **Zennのアカウント情報取得**
  - 指定されたZennアカウントの過去記事を取得
  - 記事の「いいね数」や「アクセス数」などをもとに人気記事を特定

- **SNS投稿文の生成**
  - OpenAIのLLMを活用し、SNS向けの投稿文を作成
  - 個人アカウントと企業アカウントで異なるトーンに対応

- **Gradioベースのユーザーインターフェース**
  - ZennアカウントURLの入力フォーム
  - 「個人向け / 企業向け」の選択
  - 生成された投稿文の表示（コピー可能）

#### 1.3.2 投稿文の特徴
- **個人向け**: カジュアルなトーンで、読者との対話を意識した投稿  
  - 例: 「最近の人気記事を振り返ってみました！特にこの記事が好評でした👇」  
- **企業向け**: フォーマルなトーンで、情報提供を意識した投稿  
  - 例: 「過去に多くの方に読まれた記事を改めてご紹介します📢」  

### 1.4 非機能要件

#### 1.4.1 性能要件
- Zennのデータ取得を高速に処理（APIがない場合はスクレイピング最適化）
- LLMのレスポンスをストリーミングで表示し、待ち時間を短縮

#### 1.4.2 セキュリティ要件
- OpenAI APIキーの安全な管理（環境変数で管理）
- Zennのデータ取得時に過剰なリクエストを送らないよう制御

#### 1.4.3 運用・保守要件
- エラーハンドリングの実装（ZennのURLが無効な場合など）
- ログ出力によるデバッグ情報の記録
- 設定ファイルによる容易な環境設定

### 1.5 制約条件
- **Python 3.8以上**での動作保証
- **ZennのAPIがない場合はスクレイピングを使用**
- **Gradioフレームワーク**を利用したUI構築
- **OpenAI API**を利用した投稿文生成

### 1.6 開発環境
- **言語**: Python  
- **フレームワーク**: Gradio  
- **外部API**: OpenAI API  
- **開発ツール**: VSCode, GitHub  

### 1.7 成果物
- ソースコード  
- 設計書  
- テストコード  
- README（セットアップ手順含む）  
- 要件定義書  

---

## 2. システム設計

### 2.1 システム概要設計

#### 2.1.1 システムアーキテクチャ
```
[Gradio UI] <-> [Zenn Data Fetcher] <-> [Post Generator (LLM)] <-> [OpenAI API]
```

#### 2.1.2 主要コンポーネント
1. **Gradio UI**
   - ZennアカウントURL入力フォーム
   - 個人/企業向けの選択
   - 生成された投稿文の表示（コピー可能）

2. **Zenn Data Fetcher**
   - Zennのアカウントページから記事情報を取得
   - いいね数やアクセス数をもとに人気記事を特定

3. **Post Generator (LLM)**
   - OpenAI APIを利用し、SNS向けの投稿文を生成
   - 個人向け・企業向けのトーンを調整

### 2.2 詳細設計

#### 2.2.1 クラス設計

##### 2.2.1.1 `ZennDataFetcher`
```python
class ZennDataFetcher:
    """Zennのアカウントから記事情報を取得するクラス"""
    
    def __init__(self, username: str, is_company: bool = False):
        self.username = username
        self.is_company = is_company
        # URLを設定
        self.setup_urls()
        
    def setup_urls(self):
        """URLを設定する"""
        # 企業アカウントか通常アカウントかによってURLを変更
        
    def fetch_articles(self) -> List[dict]:
        """ZennのRSSフィードから記事情報を取得"""
        
    def get_popular_articles(self, limit: int = 5, random_seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """人気記事を取得する（公開日でソートし、ランダムに選択）"""
```

##### 2.2.1.2 `PostGenerator`
```python
class PostGenerator:
    """SNS投稿文を生成するクラス"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def generate_post(self, articles: List[Dict[str, Any]], tone: str = "personal", template: str = "", max_tokens: int = 500) -> str:
        """LLMを使って投稿文を生成"""
        
    def generate_post_streaming(self, articles: List[Dict[str, Any]], tone: str = "personal", template: str = "", max_tokens: int = 500):
        """LLMを使って投稿文を生成（ストリーミング版）"""
```

##### 2.2.1.3 `GradioInterface`
```python
class GradioInterface:
    """Gradioインターフェースを管理するクラス"""
    
    def __init__(self, fetcher: Optional[ZennDataFetcher] = None, generator: Optional[PostGenerator] = None):
        self.fetcher = fetcher
        self.generator = generator
        self.current_articles = []

    def extract_username(self, url: str) -> Optional[str]:
        """ZennのURLからユーザー名を抽出する（企業アカウントにも対応）"""
        
    def process_url(self, url: str, tone: str, article_limit: int, template: str = "") -> Tuple[str, str]:
        """URLを処理して投稿文を生成する"""
        
    def process_url_streaming(self, url: str, tone: str, article_limit: int, template: str = ""):
        """URLを処理して投稿文を生成する（ストリーミング版）"""
        
    def build_interface(self) -> gr.Blocks:
        """Gradioインターフェースを構築"""
        
    def launch(self, **kwargs):
        """Gradioインターフェースを起動"""
```

#### 2.2.2 データフロー
1. ユーザーがZennのアカウントURLを入力  
2. `ZennDataFetcher` が記事情報を取得  
3. `PostGenerator` がLLMを使って投稿文を生成  
4. `GradioInterface` が結果を表示  

#### 2.2.3 エラーハンドリング
- ZennのURLが無効な場合のエラーメッセージ表示  
- OpenAI APIのエラー処理  
- スクレイピング失敗時のリトライ処理  

### 2.3 インターフェース設計

#### 2.3.1 Gradio UI構成
- **ZennアカウントURL入力フォーム**
  - 個人アカウントと企業アカウントの両方に対応
- **定型文入力フォーム（オプション）**
  - 生成された投稿文の冒頭に追加される定型文
  - `{url}` は記事のURLに置き換えられる
- **個人向け / 企業向けの選択**
- **取得する記事数の設定**
- **生成された投稿文の表示（コピー可能）**

### 2.4 セキュリティ設計
- APIキーの環境変数管理  
- スクレイピング時のリクエスト制御  

### 2.5 テスト設計
- **ユニットテスト**
  - `ZennDataFetcher` の記事取得テスト
  - `PostGenerator` の投稿文生成テスト
- **統合テスト**
  - UIからの入力 → 投稿文生成の一連の流れをテスト

### 2.6 開発環境・依存関係
- Python 3.8+  
- Gradio  
- OpenAI Python SDK  
- BeautifulSoup（スクレイピング用）  
- pytest（テスト用）  

### 2.7 開発工程

#### 2.7.1 開発フェーズ
1. **要件定義・設計（第1週）**  
2. **データ取得・スクレイピング実装（第2週）**  
3. **LLMを使った投稿文生成（第3週）**  
4. **Gradio UI実装（第4週）**  
5. **テスト・デバッグ（第5週）**  
6. **ドキュメント作成・リリース（第6週）**  

---

この設計で進めると、Zennの人気記事を活用したSNS投稿文を簡単に作成できるツールが実現できそうです！ 🚀  
ご意見や追加の要望があれば教えてください！ 😊
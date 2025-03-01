"""
Gradioインターフェースを管理するモジュール
"""

import re
import logging
import gradio as gr
from typing import Tuple, Optional
from .zenn_data_fetcher import ZennDataFetcher
from .post_generator import PostGenerator

# ロガーの設定
logger = logging.getLogger(__name__)


class GradioInterface:
    """Gradioインターフェースを管理するクラス"""

    def __init__(self, fetcher: Optional[ZennDataFetcher] = None, generator: Optional[PostGenerator] = None):
        """
        GradioInterfaceの初期化

        Args:
            fetcher: ZennDataFetcherのインスタンス
            generator: PostGeneratorのインスタンス
        """
        self.fetcher = fetcher
        self.generator = generator
        self.current_articles = []

    def extract_username(self, url: str) -> Optional[str]:
        """
        ZennのURLからユーザー名を抽出する

        Args:
            url: ZennのURL

        Returns:
            Optional[str]: 抽出されたユーザー名、抽出できない場合はNone
        """
        # 企業アカウントのURLからユーザー名を抽出するパターン
        company_pattern = r"https?://zenn\.dev/p/([a-zA-Z0-9_-]+)(?:/.*)?$"
        match = re.search(company_pattern, url)
        if match:
            return match.group(1)  # 企業アカウントの場合は、p/の後のユーザー名を返す

        # 通常のURLからユーザー名を抽出するパターン
        patterns = [
            r"https?://zenn\.dev/([a-zA-Z0-9_-]+)(?:/.*)?$",  # 通常のZenn URL
            r"@([a-zA-Z0-9_-]+)",  # @username形式
            r"^([a-zA-Z0-9_-]+)$",  # ユーザー名のみ
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def process_url(self, url: str, tone: str, article_limit: int, template: str = "") -> Tuple[str, str]:
        """
        URLを処理して投稿文を生成する

        Args:
            url: ZennのURL
            tone: 投稿のトーン（"personal"または"corporate"）
            article_limit: 取得する記事数
            template: 定型文（空文字列の場合は使用しない）

        Returns:
            Tuple[str, str]: 処理結果のメッセージと生成された投稿文
        """
        # URLからユーザー名を抽出
        username = self.extract_username(url)
        if not username:
            return "エラー: 有効なZennのURLまたはユーザー名を入力してください。", ""

        # 企業アカウントかどうかを判断
        is_company = url.startswith("https://zenn.dev/p/") or url.startswith("http://zenn.dev/p/")

        # ZennDataFetcherのインスタンスを作成（未設定の場合）
        if not self.fetcher:
            self.fetcher = ZennDataFetcher(username, is_company=is_company)
        else:
            self.fetcher.username = username
            self.fetcher.is_company = is_company
            # URLを再構築
            self.fetcher.setup_urls()

        # 人気記事を取得
        try:
            self.current_articles = self.fetcher.get_popular_articles(limit=article_limit)
            if not self.current_articles:
                return f"エラー: ユーザー '{username}' の記事が見つかりませんでした。", ""
        except Exception as e:
            logger.error(f"記事の取得中にエラーが発生しました: {e}")
            return f"エラー: 記事の取得中にエラーが発生しました: {e}", ""

        # PostGeneratorのインスタンスを作成（未設定の場合）
        if not self.generator:
            self.generator = PostGenerator()

        # 投稿文を生成
        try:
            post = self.generator.generate_post(self.current_articles, tone, template)

            # 定型文が使用された場合のメッセージを変更
            if template:
                return "成功: 定型文を使用して投稿文を生成しました。", post
            else:
                return f"成功: ユーザー '{username}' の人気記事から投稿文を生成しました。", post
        except Exception as e:
            logger.error(f"投稿文の生成中にエラーが発生しました: {e}")
            return f"エラー: 投稿文の生成中にエラーが発生しました: {e}", ""

    def process_url_streaming(self, url: str, tone: str, article_limit: int, template: str = ""):
        """
        URLを処理して投稿文を生成する（ストリーミング版）

        Args:
            url: ZennのURL
            tone: 投稿のトーン（"personal"または"corporate"）
            article_limit: 取得する記事数
            template: 定型文（空文字列の場合は使用しない）

        Yields:
            Tuple[str, str]: 処理結果のメッセージと生成された投稿文
        """
        # URLからユーザー名を抽出
        username = self.extract_username(url)
        if not username:
            yield "エラー: 有効なZennのURLまたはユーザー名を入力してください。", ""
            return

        # 企業アカウントかどうかを判断
        is_company = url.startswith("https://zenn.dev/p/") or url.startswith("http://zenn.dev/p/")

        # ZennDataFetcherのインスタンスを作成（未設定の場合）
        if not self.fetcher:
            self.fetcher = ZennDataFetcher(username, is_company=is_company)
        else:
            self.fetcher.username = username
            self.fetcher.is_company = is_company
            # URLを再構築
            self.fetcher.setup_urls()

        # 人気記事を取得
        try:
            yield f"処理中: ユーザー '{username}' の人気記事を取得しています...", ""
            self.current_articles = self.fetcher.get_popular_articles(limit=article_limit)
            if not self.current_articles:
                yield f"エラー: ユーザー '{username}' の記事が見つかりませんでした。", ""
                return
        except Exception as e:
            logger.error(f"記事の取得中にエラーが発生しました: {e}")
            yield f"エラー: 記事の取得中にエラーが発生しました: {e}", ""
            return

        # PostGeneratorのインスタンスを作成（未設定の場合）
        if not self.generator:
            self.generator = PostGenerator()

        # 投稿文を生成（ストリーミング）
        try:
            # 定型文が使用される場合のメッセージを変更
            if template:
                yield "処理中: 定型文を使用して投稿文を生成しています...", ""
            else:
                yield f"処理中: ユーザー '{username}' の人気記事から投稿文を生成しています...", ""

            post = ""
            for chunk in self.generator.generate_post_streaming(self.current_articles, tone, template):
                post += chunk

                # 定型文が使用された場合のメッセージを変更
                if template:
                    yield "成功: 定型文を使用して投稿文を生成しました。", post
                else:
                    yield f"成功: ユーザー '{username}' の人気記事から投稿文を生成しました。", post
        except Exception as e:
            logger.error(f"投稿文の生成中にエラーが発生しました: {e}")
            yield f"エラー: 投稿文の生成中にエラーが発生しました: {e}", post

    def build_interface(self) -> gr.Blocks:
        """
        Gradioインターフェースを構築

        Returns:
            gr.Blocks: Gradioインターフェース
        """
        with gr.Blocks(title="Zenn記事推薦＆SNS投稿文生成ツール") as interface:
            gr.Markdown("# Zenn記事推薦＆SNS投稿文生成ツール")
            gr.Markdown(
                "ZennのアカウントURLを入力すると、そのアカウントの過去の人気記事を分析し、SNS向けの投稿文を生成します。"
            )

            with gr.Row():
                with gr.Column():
                    url_input = gr.Textbox(
                        label="ZennのアカウントURL",
                        placeholder="https://zenn.dev/username または @username または username",
                        info="ZennのアカウントURLまたはユーザー名を入力してください",
                    )

                    template_input = gr.Textbox(
                        label="定型文（オプション）",
                        placeholder="定型文を入力してください。{url}は記事のURLに置き換えられます。",
                        info="定型文を入力すると、生成された投稿文の冒頭に追加されます。空欄の場合は追加されません。",
                        lines=3,
                    )

                    with gr.Row():
                        tone_radio = gr.Radio(
                            choices=["個人向け", "企業向け"],
                            label="投稿のトーン",
                            value="個人向け",
                            info="投稿文のトーンを選択してください（定型文を使用する場合は無視されます）",
                        )

                        article_limit = gr.Slider(
                            minimum=1, maximum=10, value=5, step=1, label="取得する記事数", info="分析に使用する人気記事の数"
                        )

                    generate_btn = gr.Button("投稿文を生成", variant="primary")

            with gr.Row():
                status_output = gr.Textbox(label="処理状況", interactive=False)
                post_output = gr.Textbox(
                    label="生成された投稿文", placeholder="ここに生成された投稿文が表示されます", interactive=False, lines=5
                )

            # トーンの選択肢を変換
            def map_tone(tone):
                return "personal" if tone == "個人向け" else "corporate"

            # ボタンクリック時の処理
            generate_btn.click(
                fn=lambda url, template, tone, limit: self.process_url(url, map_tone(tone), limit, template),
                inputs=[url_input, template_input, tone_radio, article_limit],
                outputs=[status_output, post_output],
            )

            gr.Markdown("""
            ## 使い方
            1. ZennのアカウントURLまたはユーザー名を入力してください
            2. 必要に応じて定型文を入力してください（{url}は記事のURLに置き換えられます）
            3. 投稿のトーン（個人向け/企業向け）を選択してください
            4. 「投稿文を生成」ボタンをクリックしてください
            5. 生成された投稿文をコピーしてSNSに投稿できます
            
            ## 注意事項
            - OpenAI APIキーが必要です（環境変数OPENAI_API_KEYに設定してください）
            - Zennのデータ取得にはスクレイピングを使用しています
            - 定型文を入力すると、生成された投稿文の冒頭に追加されます
            """)

        return interface

    def launch(self, **kwargs):
        """
        Gradioインターフェースを起動

        Args:
            **kwargs: gr.launch()に渡す追加の引数
        """
        interface = self.build_interface()
        interface.launch(**kwargs)

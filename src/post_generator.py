"""
SNS投稿文を生成するモジュール
"""

from typing import List, Dict, Any, Optional
import logging
import os
import openai

# ロガーの設定
logger = logging.getLogger(__name__)


class PostGenerator:
    """SNS投稿文を生成するクラス"""

    def __init__(self, api_key: Optional[str] = None):
        """
        PostGeneratorの初期化

        Args:
            api_key: OpenAI APIキー（Noneの場合は環境変数から取得）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI APIキーが設定されていません。環境変数OPENAI_API_KEYを設定してください。")
        else:
            openai.api_key = self.api_key

    def _format_articles_for_prompt(self, articles: List[Dict[str, Any]]) -> str:
        """
        記事情報をプロンプト用にフォーマット

        Args:
            articles: 記事情報のリスト

        Returns:
            str: フォーマットされた記事情報
        """
        formatted_text = "【人気記事リスト】\n"
        for i, article in enumerate(articles, 1):
            formatted_text += f"{i}. タイトル: {article['title']}\n"
            formatted_text += f"   URL: {article['url']}\n"
            formatted_text += f"   いいね数: {article['likes']}\n"
            formatted_text += f"   公開日: {article['published_at']}\n"
            formatted_text += f"   概要: {article['description']}\n"
            formatted_text += f"   タグ: {', '.join(article['tags'])}\n\n"
        return formatted_text

    def _create_personal_prompt(self, articles_text: str) -> Dict[str, str]:
        """
        個人向けのプロンプトを作成

        Args:
            articles_text: フォーマットされた記事情報

        Returns:
            Dict[str, str]: システムプロンプトとユーザープロンプト
        """
        system_prompt = """
あなたは個人のSNS投稿を作成する専門家です。
Zennの人気記事を紹介するTwitter（X）投稿を作成してください。
以下の特徴を持つ投稿を作成してください：

1. カジュアルで親しみやすいトーン
2. 読者との対話を意識した文体
3. 絵文字を適度に使用
4. 280文字以内に収める
5. ハッシュタグを1-2個含める
6. 記事のURLを含める（最も人気のある記事のURLを優先）
"""

        user_prompt = f"""
以下の人気記事情報をもとに、Twitterの投稿文を作成してください。

{articles_text}

最もいいね数の多い記事を中心に紹介し、読者の興味を引く投稿にしてください。
"""

        return {"system": system_prompt, "user": user_prompt}

    def _create_corporate_prompt(self, articles_text: str) -> Dict[str, str]:
        """
        企業向けのプロンプトを作成

        Args:
            articles_text: フォーマットされた記事情報

        Returns:
            Dict[str, str]: システムプロンプトとユーザープロンプト
        """
        system_prompt = """
あなたは企業のSNS投稿を作成する専門家です。
Zennの人気記事を紹介するTwitter（X）投稿を作成してください。
以下の特徴を持つ投稿を作成してください：

1. フォーマルで丁寧なトーン
2. 情報提供を意識した文体
3. 絵文字を控えめに使用
4. 280文字以内に収める
5. ハッシュタグを1-2個含める
6. 記事のURLを含める（最も人気のある記事のURLを優先）
"""

        user_prompt = f"""
以下の人気記事情報をもとに、Twitterの投稿文を作成してください。

{articles_text}

最もいいね数の多い記事を中心に紹介し、専門性と信頼性を感じさせる投稿にしてください。
"""

        return {"system": system_prompt, "user": user_prompt}

    def generate_post_streaming(
        self, articles: List[Dict[str, Any]], tone: str = "personal", template: str = "", max_tokens: int = 500
    ):
        """
        LLMを使って投稿文を生成（ストリーミング版）

        Args:
            articles: 記事情報のリスト
            tone: 投稿のトーン（"personal"または"corporate"）
            template: 定型文（空文字列の場合は使用しない）
            max_tokens: 生成する最大トークン数

        Yields:
            str: 生成された投稿文の一部
        """
        if not self.api_key:
            yield "OpenAI APIキーが設定されていないため、投稿文を生成できません。"
            return

        if not articles:
            yield "記事が見つかりませんでした。"
            return

        # 定型文の処理は後で行う（LLMの結果に追加する）
        processed_template = ""
        if template:
            # 記事のURLを定型文に埋め込む
            if "{url}" in template and articles:
                # 最初の記事のURLを使用
                url = articles[0]["url"]
                processed_template = template.replace("{url}", url)
            else:
                processed_template = template

        # 記事情報をテキスト形式に変換
        articles_text = self._format_articles_for_prompt(articles)

        # トーンに応じたプロンプトを作成
        if tone.lower() == "corporate":
            prompt = self._create_corporate_prompt(articles_text)
        else:
            prompt = self._create_personal_prompt(articles_text)

        try:
            # OpenAI APIを使用して投稿文を生成（ストリーミング）
            stream = openai.chat.completions.create(
                model="chatgpt-4o-latest",
                messages=[{"role": "system", "content": prompt["system"]}, {"role": "user", "content": prompt["user"]}],
                max_tokens=max_tokens,
                temperature=0.7,
                stream=True,
            )

            # 定型文が指定されている場合は、最初に定型文を出力
            if processed_template:
                yield processed_template + "\n\n"

            # LLMの出力をストリーミング
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"投稿文の生成中にエラーが発生しました: {e}")
            yield f"投稿文の生成中にエラーが発生しました: {e}"

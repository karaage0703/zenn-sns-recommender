"""
Zennのアカウントから記事情報を取得するモジュール
"""

from typing import List, Dict, Any, Optional
import re
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import random
import json

# ロガーの設定
logger = logging.getLogger(__name__)


class ZennDataFetcher:
    """Zennのアカウントから記事情報を取得するクラス"""

    def __init__(self, username: str, is_company: bool = False):
        """
        ZennDataFetcherの初期化

        Args:
            username: Zennのユーザー名
            is_company: 企業アカウントかどうか
        """
        self.username = username
        self.is_company = is_company
        self.base_url = "https://zenn.dev"

        # URLを設定
        self.setup_urls()

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def setup_urls(self):
        """URLを設定する"""
        if self.is_company:
            # 企業アカウントの場合
            self.user_url = f"{self.base_url}/p/{self.username}"
            self.articles_url = f"{self.user_url}/articles"
            self.feed_url = f"{self.user_url}/feed"
            # APIエンドポイント
            self.api_url = f"{self.base_url}/api/p/{self.username}/articles?count=20"
        else:
            # 通常のアカウントの場合
            self.user_url = f"{self.base_url}/{self.username}"
            self.articles_url = f"{self.user_url}/articles"
            self.feed_url = f"{self.user_url}/feed"
            # APIエンドポイント
            self.api_url = f"{self.base_url}/api/{self.username}/articles?count=20"

    def _validate_username(self) -> bool:
        """
        ユーザー名が有効かどうかを検証する

        Returns:
            bool: ユーザー名が有効な場合はTrue、そうでない場合はFalse
        """
        # ユーザー名の検証をスキップ（常にTrueを返す）
        return True

    def fetch_articles(self, max_articles: int = 200) -> List[Dict[str, Any]]:
        """
        ZennのRSSフィードから記事情報を取得し、APIからいいね数を取得

        Args:
            max_articles: 取得する最大記事数（デフォルト: 200）

        Returns:
            List[Dict[str, Any]]: 記事情報のリスト
        """
        if not self._validate_username():
            logger.error(f"無効なユーザー名です: {self.username}")
            return []

        articles = []

        try:
            # RSSフィードを取得
            logger.info(f"RSSフィードを取得します: {self.feed_url}")
            response = self.session.get(self.feed_url)

            if response.status_code != 200:
                logger.warning(f"フィードの取得に失敗しました: {self.feed_url}, ステータスコード: {response.status_code}")
                return []

            # XMLをパース
            try:
                root = ET.fromstring(response.content)
                # チャンネル情報を取得
                channel = root.find(".//channel")
                if channel is None:
                    logger.warning("RSSフィードのチャンネル情報が見つかりませんでした")
                    return []

                # 記事アイテムを取得
                items = root.findall(".//item")
                logger.info(f"RSSフィードから {len(items)} 個の記事が見つかりました")

                for item in items[:max_articles]:
                    try:
                        # タイトル
                        title_elem = item.find("title")
                        title = title_elem.text if title_elem is not None else ""

                        # リンク
                        link_elem = item.find("link")
                        url = link_elem.text if link_elem is not None else ""

                        # 説明
                        description_elem = item.find("description")
                        description = description_elem.text if description_elem is not None else ""

                        # 公開日
                        pubdate_elem = item.find("pubDate")
                        published_at = pubdate_elem.text if pubdate_elem is not None else ""

                        # GUID
                        guid_elem = item.find("guid")
                        guid = guid_elem.text if guid_elem is not None else ""

                        # いいね数（初期値は0）
                        likes = 0

                        # タグ（RSSフィードには含まれていないので空リストとする）
                        tags = []

                        # 記事のスラッグを抽出
                        slug_match = re.search(r"/articles/([^/]+)$", url)
                        if slug_match:
                            slug = slug_match.group(1)
                            # 記事ページから直接いいね数を取得
                            try:
                                article_page_url = url
                                article_response = self.session.get(article_page_url)
                                if article_response.status_code == 200:
                                    # いいね数を抽出
                                    likes_match = re.search(r'"liked_count":(\d+)', article_response.text)
                                    if likes_match:
                                        likes = int(likes_match.group(1))

                                    # タグを抽出
                                    tags_match = re.findall(r'"name":"([^"]+)"', article_response.text)
                                    if tags_match:
                                        tags = list(set(tags_match))  # 重複を削除
                            except Exception as e:
                                logger.error(f"記事ページからのいいね数取得中にエラーが発生しました: {e}")

                        article_data = {
                            "title": title,
                            "url": url,
                            "likes": likes,
                            "published_at": published_at,
                            "description": description,
                            "tags": tags,
                            "guid": guid,
                        }

                        articles.append(article_data)
                    except Exception as e:
                        logger.error(f"記事アイテムの解析中にエラーが発生しました: {e}")
                        continue

            except ET.ParseError as e:
                logger.error(f"XMLの解析中にエラーが発生しました: {e}")
                return []

        except Exception as e:
            logger.error(f"記事の取得中にエラーが発生しました: {e}")
            return []

        return articles

    def get_popular_articles(self, limit: int = 5, random_seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        人気記事を取得する

        Args:
            limit: 取得する記事数（デフォルト: 5）
            random_seed: ランダムシードの値（Noneの場合は現在時刻を使用）

        Returns:
            List[Dict[str, Any]]: 人気記事のリスト
        """
        # ランダムモジュールはすでにインポート済み

        # ランダムシードを設定
        if random_seed is None:
            random_seed = int(datetime.now().timestamp())
        random.seed(random_seed)

        articles = self.fetch_articles()

        if not articles:
            logger.warning("記事が見つかりませんでした")
            return []

        # いいね数でソート（多い順）
        sorted_articles = sorted(articles, key=lambda x: x.get("likes", 0), reverse=True)

        # 上位20件からランダムに選択
        top_articles = sorted_articles[:20]
        if len(top_articles) > limit:
            selected_articles = random.sample(top_articles, limit)
        else:
            selected_articles = top_articles

        return selected_articles

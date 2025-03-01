"""
Zennのアカウントから記事情報を取得するモジュール
"""

from typing import List, Dict, Any, Optional
import re
import logging
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
import random

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
        else:
            # 通常のアカウントの場合
            self.user_url = f"{self.base_url}/{self.username}"
            self.articles_url = f"{self.user_url}/articles"
            self.feed_url = f"{self.user_url}/feed"

    def _validate_username(self) -> bool:
        """
        ユーザー名が有効かどうかを検証する

        Returns:
            bool: ユーザー名が有効な場合はTrue、そうでない場合はFalse
        """
        # ユーザー名の検証をスキップ（常にTrueを返す）
        return True

    def fetch_articles(self, max_articles: int = 100) -> List[Dict[str, Any]]:
        """
        ZennのRSSフィードから記事情報を取得

        Args:
            max_articles: 取得する最大記事数（デフォルト: 100）

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
                # フィードが取得できない場合は、従来のスクレイピング方法を試みる
                return self._fetch_articles_by_scraping()

            # XMLをパース
            try:
                root = ET.fromstring(response.content)
                # チャンネル情報を取得
                channel = root.find(".//channel")
                if channel is None:
                    logger.warning("RSSフィードのチャンネル情報が見つかりませんでした")
                    return self._fetch_articles_by_scraping()

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

                        # いいね数（RSSフィードには含まれていないので0とする）
                        likes = 0

                        # タグ（RSSフィードには含まれていないので空リストとする）
                        tags = []

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
                # XMLの解析に失敗した場合は、従来のスクレイピング方法を試みる
                return self._fetch_articles_by_scraping()

        except Exception as e:
            logger.error(f"記事の取得中にエラーが発生しました: {e}")
            # エラーが発生した場合は、従来のスクレイピング方法を試みる
            return self._fetch_articles_by_scraping()

        return articles

    def _fetch_articles_by_scraping(self, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        従来のスクレイピング方法でZennのアカウントページから記事情報を取得

        Args:
            max_pages: 取得する最大ページ数（デフォルト: 5）

        Returns:
            List[Dict[str, Any]]: 記事情報のリスト
        """
        logger.info("RSSフィードからの取得に失敗したため、スクレイピングで記事を取得します")

        articles = []
        page = 1

        while page <= max_pages:
            page_url = f"{self.articles_url}?page={page}"
            try:
                response = self.session.get(page_url)
                if response.status_code != 200:
                    logger.warning(f"ページの取得に失敗しました: {page_url}, ステータスコード: {response.status_code}")
                    break

                soup = BeautifulSoup(response.text, "html.parser")

                # デバッグ情報
                logger.info(f"ページのタイトル: {soup.title.text if soup.title else 'タイトルなし'}")
                logger.info(f"ページのURL: {page_url}")

                # 記事要素を探すためのさまざまなセレクタを試す
                selectors = [
                    "article",
                    ".ArticleCard",
                    "div[role='article']",
                    "div.article",
                    "div.post",
                    "div.card",
                    "a[href*='/articles/']",
                    "div.relative",  # Zennの記事カードは相対位置指定されていることが多い
                ]

                article_elements = []
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        logger.info(f"セレクタ '{selector}' で {len(elements)} 個の要素が見つかりました")
                        article_elements = elements
                        break

                # 記事が見つからない場合は、リンクから記事を探す
                if not article_elements:
                    logger.warning(f"ページ {page} で記事が見つかりませんでした。リンクから記事を探します。")
                    article_links = soup.select("a[href*='/articles/']")
                    if article_links:
                        logger.info(f"{len(article_links)} 個の記事リンクが見つかりました")
                        # リンクから記事情報を抽出
                        for link in article_links:
                            article_data = self._parse_article_from_link(link)
                            if article_data:
                                articles.append(article_data)
                        break
                    else:
                        logger.warning("記事リンクも見つかりませんでした。HTMLの構造が変わった可能性があります。")
                        # HTMLの一部をログに出力
                        logger.debug(f"HTML: {soup.prettify()[:1000]}...")
                        break

                for article in article_elements:
                    article_data = self._parse_article(article)
                    if article_data:
                        articles.append(article_data)

                # 次のページがあるか確認
                next_button = soup.select_one("button.PaginationButton_button__Rlh9n[aria-label='Next page']")
                if not next_button or "disabled" in next_button.attrs:
                    break

                page += 1
            except Exception as e:
                logger.error(f"記事の取得中にエラーが発生しました: {e}")
                break

        return articles

    def _parse_article_from_link(self, link_element) -> Optional[Dict[str, Any]]:
        """
        リンク要素から記事情報を抽出する

        Args:
            link_element: BeautifulSoupのリンク要素

        Returns:
            Optional[Dict[str, Any]]: 記事情報の辞書、抽出に失敗した場合はNone
        """
        try:
            # リンクのhref属性から記事URLを取得
            article_path = link_element.get("href", "")
            if not article_path or "/articles/" not in article_path:
                return None

            # 既に完全なURLの場合はそのまま使用
            if article_path.startswith("http"):
                article_url = article_path
            else:
                article_url = f"{self.base_url}{article_path}" if article_path else ""

            # タイトルを取得
            title = link_element.text.strip()
            if not title:
                # 子要素からタイトルを探す
                title_element = link_element.select_one("h2, h3, h4, .title, .heading")
                if title_element:
                    title = title_element.text.strip()

            # タイトルが見つからない場合はURLからタイトルを推測
            if not title:
                title_match = re.search(r"/articles/([^/]+)$", article_path)
                if title_match:
                    title = title_match.group(1).replace("-", " ").title()

            # 親要素からいいね数を探す
            likes = 0
            parent = link_element.parent
            if parent:
                likes_element = parent.select_one("span:contains('Likes'), .likes, [data-test='likes-count']")
                if likes_element:
                    likes_text = likes_element.text.strip()
                    likes_match = re.search(r"(\d+)", likes_text)
                    if likes_match:
                        likes = int(likes_match.group(1))

            # 親要素から公開日を探す
            published_at = ""
            if parent:
                date_element = parent.select_one("time, [datetime], .date")
                if date_element:
                    published_at = date_element.text.strip()

            # 親要素から概要を探す
            description = ""
            if parent:
                description_element = parent.select_one("p, .description, .summary")
                if description_element and description_element != link_element:
                    description = description_element.text.strip()

            # 親要素からタグを探す
            tags = []
            if parent:
                tag_elements = parent.select("a[href*='/topics/'], .tag, .topic")
                for tag in tag_elements:
                    if tag != link_element:
                        tag_text = tag.text.strip()
                        if tag_text and tag_text not in tags:
                            tags.append(tag_text)

            return {
                "title": title,
                "url": article_url,
                "likes": likes,
                "published_at": published_at,
                "description": description,
                "tags": tags,
            }
        except Exception as e:
            logger.error(f"リンクからの記事解析中にエラーが発生しました: {e}")
            return None

    def _parse_article(self, article_element) -> Optional[Dict[str, Any]]:
        """
        記事要素から情報を抽出する

        Args:
            article_element: BeautifulSoupの記事要素

        Returns:
            Optional[Dict[str, Any]]: 記事情報の辞書、抽出に失敗した場合はNone
        """
        try:
            # タイトルと記事URLの取得（より汎用的なセレクタを使用）
            title_element = (
                article_element.select_one("h3 a")
                or article_element.select_one("h2 a")
                or article_element.select_one("a[href*='/articles/']")
            )

            if not title_element:
                logger.warning("記事のタイトル要素が見つかりませんでした")
                return None

            title = title_element.text.strip()
            article_path = title_element.get("href", "")
            # 既に完全なURLの場合はそのまま使用
            if article_path.startswith("http"):
                article_url = article_path
            else:
                article_url = f"{self.base_url}{article_path}" if article_path else ""

            # いいね数の取得（より汎用的なセレクタを使用）
            likes = 0
            likes_element = (
                article_element.select_one("[data-test='likes-count']")
                or article_element.select_one("span:contains('Likes')")
                or article_element.select_one("span.likes")
                or article_element.select_one("div span")  # 最後の手段として一般的なspan要素を探す
            )

            if likes_element:
                likes_text = likes_element.text.strip()
                likes_match = re.search(r"(\d+)", likes_text)
                if likes_match:
                    likes = int(likes_match.group(1))
                else:
                    logger.debug(f"いいね数のパターンが一致しませんでした: {likes_text}")

            # 公開日の取得（より汎用的なセレクタを使用）
            date_element = (
                article_element.select_one("time")
                or article_element.select_one("[datetime]")
                or article_element.select_one(".date")
            )
            published_at = date_element.text.strip() if date_element else ""

            # 概要の取得（より汎用的なセレクタを使用）
            description_element = (
                article_element.select_one("p")
                or article_element.select_one(".description")
                or article_element.select_one(".summary")
            )
            description = description_element.text.strip() if description_element else ""

            # タグの取得（より汎用的なセレクタを使用）
            tags = []
            tag_elements = (
                article_element.select("a[href*='/topics/']")
                or article_element.select(".tag")
                or article_element.select(".topic")
            )
            for tag in tag_elements:
                tag_text = tag.text.strip()
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)

            return {
                "title": title,
                "url": article_url,
                "likes": likes,
                "published_at": published_at,
                "description": description,
                "tags": tags,
            }
        except Exception as e:
            logger.error(f"記事の解析中にエラーが発生しました: {e}")
            return None

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

        # RSSフィードから取得した場合、いいね数の情報がないため、公開日でソート
        # 公開日の形式を解析してdatetimeオブジェクトに変換
        for article in articles:
            try:
                pub_date = article.get("published_at", "")
                if pub_date:
                    # RFC 822形式の日付を解析
                    try:
                        from email.utils import parsedate_to_datetime

                        dt = parsedate_to_datetime(pub_date)
                        article["pub_datetime"] = dt
                    except Exception:
                        # 他の形式の日付を試す
                        try:
                            dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                            article["pub_datetime"] = dt
                        except Exception:
                            # 日付の解析に失敗した場合は現在時刻を使用
                            article["pub_datetime"] = datetime.now()
                else:
                    article["pub_datetime"] = datetime.now()
            except Exception as e:
                logger.error(f"公開日の解析中にエラーが発生しました: {e}")
                article["pub_datetime"] = datetime.now()

        # 公開日でソート（新しい順）
        sorted_articles = sorted(articles, key=lambda x: x.get("pub_datetime", datetime.now()), reverse=True)

        # 上位20件からランダムに選択
        top_articles = sorted_articles[:20]
        if len(top_articles) > limit:
            selected_articles = random.sample(top_articles, limit)
        else:
            selected_articles = top_articles

        return selected_articles

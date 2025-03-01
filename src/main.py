"""
Zenn記事推薦＆SNS投稿文生成ツールのメインモジュール
"""

import os
import logging
import argparse
from dotenv import load_dotenv
from .gradio_interface import GradioInterface

# ロギングの設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# .envファイルの読み込み
load_dotenv()


def main():
    """メイン関数"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="Zenn記事推薦＆SNS投稿文生成ツール")
    parser.add_argument("--port", type=int, default=7860, help="Gradioサーバーのポート番号")
    parser.add_argument("--share", action="store_true", help="Gradioの共有リンクを生成")
    args = parser.parse_args()

    # OpenAI APIキーの確認
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("環境変数OPENAI_API_KEYが設定されていません。.envファイルを作成するか、環境変数を設定してください。")

    # Gradioインターフェースの起動
    logger.info("Zenn記事推薦＆SNS投稿文生成ツールを起動しています...")
    interface = GradioInterface()
    interface.launch(server_port=args.port, share=args.share)


if __name__ == "__main__":
    main()

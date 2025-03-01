FROM python:3.11-slim

WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ruffをインストール（コードフォーマッタ）
RUN pip install --no-cache-dir ruff==0.9.1

# アプリケーションのコードをコピー
COPY . .

# アプリケーションをインストール
RUN pip install -e .

# Gradioサーバーのポートを公開
EXPOSE 7860

# コマンドを実行
CMD ["python", "-m", "src.main", "--host", "0.0.0.0"]
FROM python:3.9-slim

WORKDIR /app

# 依存関係のインストールに必要なパッケージを追加
RUN apt-get update && apt-get install -y \
    build-essential \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# scikit-learnを明示的にインストール
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir scikit-learn

COPY . .

CMD cd app && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} 
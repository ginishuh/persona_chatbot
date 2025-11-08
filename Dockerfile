FROM python:3.11-slim

WORKDIR /app

# Git 및 CLI 설치 도구 준비
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# Droid CLI 설치 (컨테이너 내부에서 Factory.ai 호출 지원)
RUN curl -fsSL https://app.factory.ai/cli | sh && \
    cp /root/.local/bin/droid /usr/local/bin/droid && \
    chmod 755 /usr/local/bin/droid

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY server/ ./server/
COPY web/ ./web/

# WebSocket 포트
EXPOSE 8765
# HTTP 정적 파일 서빙 포트
EXPOSE 8000

CMD ["python", "-u", "server/websocket_server.py"]

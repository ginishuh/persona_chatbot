FROM python:3.11-slim

WORKDIR /app

# Git 설치 (git 명령어 사용을 위해)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

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

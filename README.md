# 📖 Persona Chat – 멀티 캐릭터 대화 시스템

웹 기반 멀티 캐릭터 대화/서사 관리 시스템입니다. Claude Code, Droid CLI, Gemini CLI를 이용해 실시간 스트리밍 대화를 제공합니다.

> 2025-11-12 기준: Claude ✅, Droid ✅, Gemini ✅ (로컬/Docker 모두 동작 확인)

 # Persona Chat

간단한 요약
- Persona Chat는 캐릭터(유저/ NPC)를 포함한 대화·서사 실험을 위한 경량 WebSocket 서버입니다.
- 로컬 개발과 Docker 배포를 지원하며 Claude/Gemini/Droid CLI로 모델을 연결할 수 있습니다.

중요 보안 안내
- 기본 예시(`docker-compose.yml.example`)는 서비스 바인딩을 `127.0.0.1`로 설정합니다. 운영 환경에서 직접 `0.0.0.0`으로 노출하지 말고 nginx 같은 리버스 프록시로 TLS와 접근 제어를 적용하세요.
- HTTP 로그인(`APP_LOGIN_PASSWORD`) 사용 시 `APP_JWT_SECRET`을 함께 설정해야 합니다.

빠른 시작 — 로컬
1) 가상환경과 의존성

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) AI CLI(선택)
- Claude/Gemini/Droid 중 최소 1개를 인증해 사용하세요.

3) 서버 실행

```bash
python server/websocket_server.py
```

접속: HTTP UI `http://localhost:9000`, WS `ws://localhost:8765`

빠른 시작 — Docker
1) `.env` 준비(예: `cp examples/env/.env.example.local-dev .env`)
2) 예시 복사 및 실행

```bash
cp docker-compose.yml.example docker-compose.yml
docker compose up -d --build
docker compose logs -f
```

개발 · 테스트
- 테스트: `pytest -q`
- Pre-commit 훅: `pip install pre-commit && bash scripts/install_hooks.sh`
- 스모크 테스트: `python scripts/ws_chat_test.py --provider claude --prompt "테스트"`

환경 변수(핵심)
- `APP_LOGIN_PASSWORD`, `APP_JWT_SECRET` — HTTP 로그인 사용 시 필수로 함께 설정
- `APP_BIND_HOST` — 기본값은 예시에서 `127.0.0.1` (운영 시 nginx 뒤에서 관리)
- `FACTORY_AUTH_DIR`, `CLAUDE_AUTH_DIR`, `GEMINI_AUTH_DIR` — 호스트 인증 디렉터리 절대 경로

데이터 및 persona_data
- `persona_data/`는 캐릭터·프리셋 저장소입니다. 민감 데이터는 별도 개인 프라이빗 레포로 관리하세요.
- 로컬 개발용 DB는 `data/`에 생성됩니다. Docker에서는 `./data:/app/data` 마운트를 권장합니다.

프로젝트 구조(요약)

```
persona_chatbot/
├─ server/            # 백엔드(WebSocket/HTTP, 핸들러)
├─ web/               # 정적 UI
├─ persona_data/      # 캐릭터/프리셋(프라이빗 권장)
├─ chatbot_workspace/ # 챗봇 전용 지침(로컬 편집)
└─ docker-compose.yml.example
```

기여
- 이슈/PR 환영. 커밋 메시지는 한국어 요약을 권장합니다.

더 읽기
- 내부 운영·세부 가이드는 `AGENTS.md`를 참고하세요.

라이선스
- MIT

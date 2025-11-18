# 저장소 지침 - 베이스 지침

## 프로젝트 구조 및 모듈 조직
- `server/` – Python 백엔드. 진입점: `server/websocket_server.py`; 공통 로직은 아래에 있음:
  - `server/core/` – 핵심 유틸리티 (session_manager, app_context, auth)
  - `server/handlers/` – 비즈니스 로직 (file, Claude/Gemini/Droid, context, history, mode, workspace, db)
  - `server/http/` – 정적 파일 및 내보내기 API를 위한 HTTP 서버
  - `server/ws/` – WebSocket 라우팅 및 액션 핸들러
- `web/` – Python HTTP 도우미가 제공하는 정적 프론트엔드 (`index.html`, `app.js`, `style.css`)
- `persona_data/stories/` – 저장된 서사 (마크다운). 레거시 `STORIES/` 폴더는 더 이상 사용되지 않음.
- `chatbot_workspace/` – 챗봇 전용 작업공간 (`chatbot_workspace/CLAUDE.md` 읽음).
- `persona_data/` – 프리셋 및 워크스페이스 설정.
- `docs/` – 저장소 문서 및 지침 (이 파일 위치).
- 루트: `requirements.txt`, `Dockerfile.full`, `docker-compose.yml.example`, `.env.example`, `README.md`, `CLAUDE.md`, `AGENTS.md`.

## 빌드, 테스트, 개발 명령어
- 환경 생성: `python3 -m venv venv && source venv/bin/activate`
- 의존성 설치: `pip install -r requirements.txt`
- Claude CLI (처음): `claude auth login`
- 로컬 실행: `python3 -m server.websocket_server`
  - HTTP: `http://127.0.0.1:9000` (정적 UI)
  - WebSocket: `ws://127.0.0.1:8765`
- Docker (선택사항): `docker-compose.yml.example` → `docker-compose.yml` 복사 후 `docker compose up --build`
  - 포트는 `.env` (`HTTP_PORT`, `WS_PORT`) 따름 (Docker 전용).

## 언어 지침

**중요**: 이 문서는 저장소 지침의 단일 진실 원천(SSOT)입니다.

### 언어 규칙
- **코드/주석/커밋**: 한국어 (한글)
- **식별자(변수/함수/API)**: 상호운용성을 위해 영어
- **사용자 문서**: 한국어 (README.md 등)
- **커뮤니케이션(이슈·PR·리뷰·내부 채널)**: 문서에서 영어를 요구하는 경우를 제외하고 기본적으로 한국어 사용
- **예외 - 기준 문서**: 영어만
  - `docs/agents_base_en.md` (이 파일 - SSOT)
  - `CLAUDE.md` (영어 지침)
  - `AGENTS.md` (영어 지침)

### 문서 동기화
- CLAUDE.md 동기화 시 `python3 scripts/sync_docs.py` 사용
- 베이스 문서는 직접 편집 금지 - 항상 `docs/agents_base_en.md` 편집

## 코딩 스타일 및 명명 규칙
- Python: PEP 8, 4스페이스 들여쓰기, 실용적인 곳에 타입 힌트, 모듈/함수 `snake_case`, 클래스 `PascalCase`, 상수 `UPPER_SNAKE_CASE`.
- `logging` 사용 (`print` 금지); 공개 함수에는 간단한 독스트링 포함.
- JS: ES6+ (`const`/`let`), `web/app.js`의 작은 순수 함수; DOM 셀렉터와 렌더링 로직 분리.

## 테스트 지침
- 프레임워크: `pytest` (기여 시 추가).
- 위치: 소스 경로와 대응 (예: `tests/handlers/test_history_handler.py`).
- 명명: 파일 `test_*.py`, 함수 `test_*`.
- 실행: `pip install pytest && pytest -q`.
- 외부 호출 모킹 (Claude CLI, 파일시스템, 네트워크). 핸들러의 의미 있는 커버리지 목표.

## 커밋 및 풀 리퀘스트 지침
- 커밋: 법령형 어조와 범위 접두어 (예: `fix(server): ...`). 주제/설명은 한국어로 작성. 예: `fix(server): websockets v13 연결 종료 처리`.
- PR: 문제/해결 요약 (한국어), 로컬 실행 단계, UI 변경 스크린샷, 관련 이슈 포함. PR은 집중적으로 유지; 관련 없는 리팩토리 금지. 검토 요청 전에 9000/8765에서 앱 실행 확인.

## 보안 및 설정 팁
- 시크릿 커밋 금지. Docker 워크플로우를 위해 `.env.example`를 `.env`로 복사; 로컬 실행은 `websocket_server.py`에 하드코딩된 포트 사용.
- 인증: 액세스/리프레시 토큰 기반 JWT. 필수 환경 변수:
  - `APP_JWT_SECRET` – `APP_LOGIN_PASSWORD` 사용 시 반드시 설정
  - `APP_LOGIN_PASSWORD` – 선택적 간단 비밀번호 보호
  - `APP_ACCESS_TTL`, `APP_REFRESH_TTL` – 토큰 수명
  - `APP_BIND_HOST` – 기본값: `127.0.0.1` (보안)
- 관리자 계정 생성: **SQLite 잠금 방지를 위해 반드시 컨테이너 안에서 생성**:
  ```bash
  docker compose exec persona-chatbot python3 -c "
  from server.handlers.db_handler import DBHandler
  import asyncio
  async def create_admin():
      db = DBHandler('./data')
      await db.initialize()
      success = await db.create_admin_user('admin', 'password')
      print('관리자 생성 성공' if success else '이미 존재함')
  asyncio.run(create_admin())
  "
  ```
- 모드 전환: UI 제어가 제거됨. 백엔드 도우미 `server/handlers/mode_handler.py`는 스크립트나 수동 사용을 위해 계속 존재함. 수동으로 사용 시 "coding" 모드에서 편집/커밋하는 것을 선호.

## 현재 상태 및 스모크 테스트

- 2025-11-17 기준, 모든 제공자가 종단적으로 동작 확인 완료: Claude ✅, Droid ✅, Gemini ✅ (Docker와 로컬 실행 모두).
- 빠른 스모크 테스트 스크립트가 `scripts/ws_chat_test.py`에 제공됨 (로그인, 컨텍스트 설정, 채트 스트림, 완료 처리).

예시:

```bash
# 컨테이너 시작
docker compose up -d --build

# WebSocket 스모크 테스트
python scripts/ws_chat_test.py --provider claude --prompt "Smoke: Claude"
python scripts/ws_chat_test.py --provider droid  --prompt "Smoke: Droid"
python scripts/ws_chat_test.py --provider gemini --prompt "Smoke: Gemini"
```

참고:
- `APP_LOGIN_PASSWORD` 설정 시, 서버 시작 시 `APP_JWT_SECRET`도 설정되어 있는지 확인. 그렇지 않으면 서버가 강제로 종료됨.
- Docker의 경우, `.env`에서 호스트 절대 경로 사용 선호:
  - `FACTORY_AUTH_DIR=$HOME/.factory`, `CLAUDE_AUTH_DIR=$HOME/.claude`, `GEMINI_AUTH_DIR=$HOME/.gemini`.

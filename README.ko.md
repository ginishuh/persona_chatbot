[English](README.md) | 한국어

# Persona Chat

> 멀티 캐릭터 AI 대화와 서사 오케스트레이션을 위한 오픈소스 웹 앱

[![CI](https://github.com/ginishuh/persona_chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/ginishuh/persona_chatbot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-brightgreen.svg)](https://www.docker.com/)

Persona Chat은 브라우저에서 멀티 캐릭터 AI 대화를 운영할 수 있게 만든 공개 오픈소스 웹 애플리케이션입니다. 실시간 WebSocket 스트리밍, CLI 기반 AI 제공자 전환, 서사 맥락 제어, 내보내기 워크플로를 하나의 로컬 퍼스트 작업공간으로 묶었습니다.

이 프로젝트는 실제로 바로 써볼 수 있는 도구이면서, 아래 같은 용도의 참고 구현체로도 적합합니다.

- 여러 캐릭터가 한 방에서 대화하는 롤플레이/서사형 챗
- GM 보조가 있는 시나리오 진행
- 프라이빗한 로컬 AI 대화 워크플로
- 여러 AI 백엔드를 같은 UI에서 비교·운영하는 스트리밍 챗 앱

바로가기: [기여 가이드](CONTRIBUTING.ko.md) · [영문 기여 가이드](CONTRIBUTING.md) · [보안 안내](SECURITY.md) · [라이선스](LICENSE)

## 이 프로젝트가 하는 일

- **멀티 캐릭터 대화**: 여러 캐릭터가 같은 세션 안에서 순차적으로 말하는 방을 운영할 수 있습니다.
- **서사 오케스트레이션**: 세계관, 현재 상황, 플레이어 캐릭터, NPC, 진행자 모드를 함께 관리합니다.
- **실시간 스트리밍**: WebSocket 기반으로 생성 중인 응답을 바로 확인할 수 있습니다.
- **멀티 제공자 지원**: Claude Code CLI, Gemini CLI, Droid CLI를 전환해 사용할 수 있습니다.
- **맥락·세션 제어**: 대화 히스토리 길이, 무제한 모드, 세션 유지, 세션 초기화를 제어할 수 있습니다.
- **Export / Import 워크플로**: JSON, Zip, NDJSON 스트림 내보내기와 WebSocket 기반 가져오기를 지원합니다.
- **로컬 퍼스트 운영**: `persona_data`, 인증 정보, 서사 로그를 직접 관리하는 구조입니다.

## 이런 분께 잘 맞습니다

- 로컬에서 구조화된 스토리/롤플레이 작업공간이 필요한 분
- 멀티 제공자 AI 오케스트레이션 패턴을 살펴보려는 개발자
- 브라우저 기반 스트리밍 AI 챗 참고 구현체가 필요한 팀
- 호스팅형 서비스보다 사내·개인 환경에서 직접 운영하는 방식을 선호하는 분

## 대표 사용 사례

- 파티원 여러 명이 차례로 대화하는 세션 운영
- 진행자 유무를 바꿔가며 시나리오형 대화 진행
- 대화 기록을 서사 로그로 남기고 백업/검토
- 동일한 인터페이스에서 제공자별 응답 특성 비교

## 빠른 시작

### 로컬 실행

준비물:

- Python 3.11 이상
- Node.js
- 지원되는 AI CLI 중 최소 1개 이상 로컬 인증

설치 예시:

```bash
# Claude Code
npm install -g @anthropic-ai/claude-code
claude auth login

# Gemini CLI
npm install -g @google/gemini-cli
gemini auth login

# Droid CLI
curl -fsSL https://app.factory.ai/cli | sh
droid auth login
```

실행:

```bash
git clone https://github.com/ginishuh/persona_chatbot.git
cd persona_chatbot

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 -m server.websocket_server
```

기본 접속 주소:

- 웹 UI: `http://127.0.0.1:9000`
- WebSocket: `ws://127.0.0.1:8765`

### Docker Compose

`examples/env/`에서 환경에 맞는 `.env` 예시를 고른 뒤 아래처럼 실행합니다.

```bash
cp docker-compose.yml.example docker-compose.yml
docker compose up -d --build
docker compose logs -f
```

Docker에서는 `.env`의 `HTTP_PORT`, `WS_PORT`를 따릅니다.

로그인을 켠 경우에는 SQLite 잠금 문제를 피하기 위해 관리자 계정을 반드시 컨테이너 안에서 생성하세요.

```bash
docker compose exec persona-chatbot python3 -c "
from server.handlers.db_handler import DBHandler
import asyncio
async def create_admin():
    db = DBHandler('./data')
    await db.initialize()
    success = await db.create_admin_user('admin', 'password')
    print('Admin created' if success else 'Already exists')
asyncio.run(create_admin())
"
```

## 핵심 워크플로

### 컨텍스트와 세션 관리

좌측 작업공간에서 아래 항목을 함께 관리합니다.

- 세계관과 현재 상황
- 플레이어 캐릭터와 NPC 정의
- 진행자 모드 선택
- 맥락 윈도우 길이
- 세션 유지와 세션 초기화

### 내보내기와 가져오기

- HTTP Export 엔드포인트: `GET /api/export`, `GET /api/export/stream`
- 지원 형식: JSON, Zip, NDJSON 스트림
- 가져오기 경로: WebSocket `import_data` 액션
- 백업 UI: `/backup` 화면에서 사용 가능

### WebSocket 인터페이스

WebSocket 메시지는 JSON 형식으로 주고받습니다. 자주 쓰는 액션은 아래와 같습니다.

- `set_context`, `get_context`
- `chat`, `clear_history`, `get_narrative`
- `set_history_limit`, `set_session_retention`, `reset_sessions`
- `list_files`, `read_file`, `write_file`
- `import_data`

### Workspace 분리

레포 개발 지침과 챗봇 런타임 지침을 분리해 둔 구조입니다.

- 루트 `CLAUDE.md`: 레포 개발용 지침
- `chatbot_workspace/CLAUDE.md`: 챗봇 런타임 지침
- `chatbot_workspace/GEMINI.md`: Gemini 런타임 지침

샘플 파일은 아래처럼 복사해서 로컬에서 사용하면 됩니다.

```bash
cp chatbot_workspace/CLAUDE.sample.md chatbot_workspace/CLAUDE.md
cp chatbot_workspace/GEMINI.sample.md chatbot_workspace/GEMINI.md
```

애플리케이션은 `persona_data/` 폴더명을 기준으로 동작하며, 캐릭터 프리셋·세계관·스토리 데이터는 별도 비공개 동반 저장소로 관리해도 잘 맞습니다.

## AI 제공자

- **Claude Code CLI**: 로컬 OAuth 인증, 세션 유지 지원
- **Gemini CLI**: 로컬 OAuth 인증, 세션 유지 지원
- **Droid CLI**: OAuth 또는 API 키 인증, 세션 유지 지원

## 프로젝트 구조

```text
persona_chatbot/
├── server/                # Python 백엔드, WebSocket 서버, HTTP export API
├── web/                   # 정적 프런트엔드
├── tests/                 # Pytest 및 e2e 스모크 테스트
├── scripts/               # 스모크 테스트와 유지보수 스크립트
├── chatbot_workspace/     # 챗봇 전용 런타임 지침
├── persona_data/          # 캐릭터, 프리셋, 세계관, 스토리
├── examples/env/          # 환경 변수 예시
├── README.md
└── README.ko.md
```

## 설정 포인트

구체적인 예시는 `.env.example`, `examples/env/`를 참고하면 됩니다. 자주 보는 항목은 아래와 같습니다.

- `APP_LOGIN_PASSWORD`, `APP_JWT_SECRET`: 선택적 로그인 보호
- `APP_ACCESS_TTL`, `APP_REFRESH_TTL`: 토큰 수명
- `APP_BIND_HOST`: 로컬 바인딩 보안 설정
- `APP_PUBLIC_WS_URL`: 외부 공개 환경의 WebSocket 주소
- `SHOW_TOKEN_USAGE`: 토큰 사용량 표시 여부
- `FACTORY_AUTH_DIR`, `CLAUDE_AUTH_DIR`, `GEMINI_AUTH_DIR`: 호스트 인증 디렉터리

WSL 환경에서는 SQLite DB를 `/mnt/c` 아래보다 리눅스 파일시스템 쪽에 두는 편이 안전합니다.

## 개발과 검증

```bash
pip install -r requirements.txt
pytest -q
python scripts/ws_chat_test.py --provider claude --prompt "Smoke: Claude"
pre-commit run --all-files
```

현재 GitHub Actions에서는 아래를 수행합니다.

- 전체 리포지토리 `pre-commit`
- 핵심 핸들러 대상 `pytest` 커버리지 검사
- `tests/e2e` 기반 WebSocket 스모크 테스트

문서 개선도 코드 기여와 동일하게 환영합니다.

## 기여

기여 방법은 [CONTRIBUTING.ko.md](CONTRIBUTING.ko.md) 또는 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고해 주세요. 버그 제보, 기능 제안, 테스트 보강, 문서 정리는 모두 도움이 됩니다. 범위가 큰 변경은 먼저 이슈로 방향을 맞춰 주시면 좋습니다.

## 보안

민감한 취약점은 공개 이슈로 올리지 말고 [SECURITY.md](SECURITY.md)를 따라 비공개로 제보해 주세요.

## 라이선스

이 프로젝트는 [MIT License](LICENSE)로 배포됩니다.

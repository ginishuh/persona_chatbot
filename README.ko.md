[English](README.md) | 한국어

# Persona Chat

> 혼자 쓰는 채팅창을, 캐릭터들이 모여 이야기를 만드는 테이블로 바꿔 보세요.

[![CI](https://github.com/ginishuh/persona_chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/ginishuh/persona_chatbot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-brightgreen.svg)](https://www.docker.com/)

Persona Chat은 여러 AI 캐릭터가 **같은 방 안에서 대화**하는 오픈소스 웹 앱입니다.
응답은 WebSocket으로 실시간 스트리밍되고, TRPG 세션·협업 소설·멀티보이스 브레인스톰 같은 시나리오를 로컬 환경에서 바로 돌릴 수 있습니다.

바로가기: [기여 가이드](CONTRIBUTING.ko.md) · [영문 기여 가이드](CONTRIBUTING.md) · [보안 안내](SECURITY.md) · [라이선스](LICENSE)

---

## 한눈에 보는 특징

| 기능 | 왜 좋은가 |
|------|----------|
| **멀티 캐릭터 대화방** | 여러 캐릭터가 순서대로 말하는 파티 채팅 — 1:1 핑퐁이 아닙니다. |
| **TRPG식 진행자 모드** | 적극·보통·소극적 AI 진행자를 고르거나, 직접 GM 자리에 앉을 수 있습니다. |
| **실시간 스트리밍** | 응답이 토큰 단위로 WebSocket에 흘러옵니다. 끝까지 기다릴 필요 없습니다. |
| **제공자 즉시 전환** | Claude Code CLI, Gemini CLI, Droid CLI를 같은 인터페이스에서 전환합니다. |
| **서사 맥락 패널** | 세계관·시나리오·PC·NPC·GM 스타일을 사이드 패널에서 한 번에 설정합니다. |
| **전체 내보내기** | JSON, Zip, NDJSON 스트림으로 백업. WebSocket으로 복원. 데이터가 외부로 나가지 않습니다. |

## 이런 분께 잘 맞습니다

- **작가·TRPG 플레이어** — 브라우저에서 구조화된 파티 대화와 시나리오 세션을 운영하고 싶은 분.
- **개발자** — 멀티 제공자 AI 오케스트레이션, WebSocket 스트리밍, 세션 관리를 실제 동작하는 코드로 살펴보고 싶은 분.
- **프라이버시 중시** — 캐릭터·스토리·인증 정보를 전부 로컬에 두고 싶은 분. 클라우드 계정 불필요.

## 아키텍처 한눈에 보기

```text
┌─────────────┐  WebSocket   ┌──────────────────────────────────┐
│  브라우저 UI  │◄────────────►│  Python 서버                      │
│  (web/)      │   JSON msgs  │  ├─ ws/        라우팅 + 액션      │
└─────────────┘              │  ├─ handlers/  비즈니스 로직      │
       ▲                     │  ├─ core/      세션, 인증         │
       │  HTTP :9000         │  └─ http/      정적 파일 + export │
       └─────────────────────┤                                  │
                             │  AI 제공자 레이어                  │
                             │  ├─ Claude Code CLI              │
                             │  ├─ Gemini CLI                   │
                             │  └─ Droid CLI                    │
                             └──────────────────────────────────┘
```

## 빠른 시작

### 로컬 실행

**준비물:** Python 3.11+, Node.js, 지원 AI CLI 중 최소 하나 로컬 인증 완료.

```bash
# 제공자 설치 (하나 이상 선택)
npm install -g @anthropic-ai/claude-code && claude auth login
npm install -g @google/gemini-cli       && gemini auth login
curl -fsSL https://app.factory.ai/cli | sh && droid auth login
```

```bash
git clone https://github.com/ginishuh/persona_chatbot.git
cd persona_chatbot

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python3 -m server.websocket_server
# 웹 UI  → http://127.0.0.1:9000
# WS     → ws://127.0.0.1:8765
```

### Docker Compose

`examples/env/`에서 환경에 맞는 `.env` 예시를 고른 뒤:

```bash
cp docker-compose.yml.example docker-compose.yml
# .env 수정
docker compose up -d --build
docker compose logs -f
```

Docker 포트는 `.env`(`HTTP_PORT`, `WS_PORT`)를 따릅니다.

<details>
<summary>관리자 계정 생성 (로그인 활성화 시)</summary>

SQLite 잠금 방지를 위해 반드시 컨테이너 안에서 실행하세요.

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
</details>

## 핵심 워크플로

### 컨텍스트와 세션 관리

좌측 작업공간 패널에서 AI가 응답 전에 읽는 모든 맥락을 설정합니다.

- **세계관·시나리오** — 한 번 세팅하면 세션 내내 참조됩니다.
- **플레이어 캐릭터·NPC** — 방에 누가 있고 어떻게 행동하는지 정의합니다.
- **진행자 모드** — GM 스타일을 고르거나 꺼둘 수 있습니다.
- **히스토리 윈도우** — AI가 보는 과거 턴 수를 조절하거나 무제한으로 열 수 있습니다.
- **세션 수명** — 재접속 시 세션 유지 또는 즉시 초기화를 선택합니다.

### 내보내기와 가져오기

| 경로 | 형식 | 비고 |
|------|------|------|
| `GET /api/export` | JSON 또는 Zip | 전체 스냅샷 다운로드 |
| `GET /api/export/stream` | NDJSON | 대용량 스트리밍 내보내기 |
| WebSocket `import_data` | JSON | 이전 백업 복원 |
| `/backup` UI | — | 브라우저 기반 백업 화면 |

### WebSocket 액션 (주요)

```text
set_context / get_context          — 서사 패널 읽기·쓰기
chat / clear_history               — 메시지 전송 또는 로그 초기화
set_history_limit / reset_sessions — 세션 동작 조절
list_files / read_file / write_file — 작업공간 파일 조작
import_data                        — 백업 복원
```

### Workspace 분리

레포 개발 지침과 챗봇 런타임 지침을 분리해 둔 구조입니다.

| 파일 | 용도 |
|------|------|
| 루트 `CLAUDE.md` | 기여자를 위한 개발 가이드 |
| `chatbot_workspace/CLAUDE.md` | 챗봇이 읽는 런타임 지침 |
| `chatbot_workspace/GEMINI.md` | Gemini 전용 런타임 지침 |

샘플 파일을 복사해서 시작하면 됩니다.

```bash
cp chatbot_workspace/CLAUDE.sample.md chatbot_workspace/CLAUDE.md
cp chatbot_workspace/GEMINI.sample.md chatbot_workspace/GEMINI.md
```

캐릭터 프리셋·세계관·스토리는 `persona_data/`에 저장됩니다. 이 폴더를 별도 비공개 저장소로 관리해도 잘 맞습니다.

## AI 제공자

| 제공자 | 인증 방식 | 세션 유지 |
|--------|----------|----------|
| Claude Code CLI | 로컬 OAuth | 지원 |
| Gemini CLI | 로컬 OAuth | 지원 |
| Droid CLI | OAuth 또는 API 키 | 지원 |

## 프로젝트 구조

```text
persona_chatbot/
├── server/                # Python 백엔드 — WS 서버, HTTP export, 핸들러
│   ├── core/              #   세션, 인증, 앱 컨텍스트
│   ├── handlers/          #   도메인별 비즈니스 로직
│   ├── http/              #   정적 파일 서빙 + export API
│   └── ws/                #   WebSocket 라우팅 + 액션 핸들러
├── web/                   # 정적 프런트엔드 (vanilla JS)
├── tests/                 # pytest 단위 + e2e 스모크 테스트
├── scripts/               # 유지보수·스모크 테스트 유틸리티
├── chatbot_workspace/     # 챗봇 런타임 지침 (개발 문서가 아님)
├── persona_data/          # 캐릭터, 프리셋, 세계관, 스토리
├── examples/env/          # 다양한 환경용 .env 템플릿
├── README.md
└── README.ko.md           # ← 지금 보고 계신 문서
```

## 설정 포인트

구체적인 예시는 `.env.example`, `examples/env/`를 참고하세요.

| 변수 | 용도 |
|------|------|
| `APP_LOGIN_PASSWORD` | 간단한 비밀번호 로그인 활성화 |
| `APP_JWT_SECRET` | 로그인 활성화 시 **필수** |
| `APP_ACCESS_TTL` / `APP_REFRESH_TTL` | 토큰 수명 |
| `APP_BIND_HOST` | 바인드 주소 (기본 `127.0.0.1`) |
| `APP_PUBLIC_WS_URL` | 리버스 프록시 환경의 외부 WebSocket 주소 |
| `SHOW_TOKEN_USAGE` | UI에 토큰 사용량 표시 여부 |
| `FACTORY_AUTH_DIR` / `CLAUDE_AUTH_DIR` / `GEMINI_AUTH_DIR` | Docker용 호스트 인증 디렉터리 마운트 |

> **WSL 팁:** SQLite DB는 `/mnt/c` 아래보다 리눅스 파일시스템 쪽에 두는 게 안전합니다.

## 개발과 검증

```bash
pip install -r requirements.txt
pytest -q
python scripts/ws_chat_test.py --provider claude --prompt "Smoke: Claude"
pre-commit run --all-files
```

CI (GitHub Actions) 수행 항목:
- 전체 리포지토리 `pre-commit`
- 핵심 핸들러 대상 `pytest` 커버리지 검사
- `tests/e2e` 기반 WebSocket 스모크 테스트

## 기여

[CONTRIBUTING.ko.md](CONTRIBUTING.ko.md)에서 셋업, 코드 스타일, PR 가이드를 확인할 수 있습니다.
버그 제보, 기능 아이디어, 테스트 보강, 문서 정리 모두 환영합니다.
간단한 수정이 아닌 경우, 먼저 이슈를 열어 범위를 맞춰 주세요.

## 보안

[SECURITY.md](SECURITY.md)를 참고하세요. 민감한 취약점은 공개 이슈 대신 비공개로 제보해 주세요.

## 라이선스

[MIT](LICENSE)

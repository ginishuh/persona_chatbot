# 📖 Persona Chat: 멀티 캐릭터 대화 스튜디오

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-brightgreen.svg)](https://www.docker.com/)

> "혼자 쓰는 채팅창"을 "캐릭터들이 뛰어노는 TRPG 테이블"로 바꾸는 웹 앱

Persona Chat은 **웹 기반 멀티 캐릭터 대화·서사 관리 시스템**입니다.
Claude Code, Droid CLI, Gemini CLI를 AI 백엔드로 사용하고, WebSocket으로 **실시간 스트리밍 대화**를 제공합니다.

> **2025-11 기준**
> Claude ✅ / Droid ✅ / Gemini ✅
> 로컬 실행과 Docker Compose 환경 모두에서 동작 확인 완료

---

## 🧭 목차

- [주요 특징](#-주요-특징)
- [이런 분이 쓰면 잘 맞습니다](#-이런-분이-쓰면-잘-맞습니다)
- [빠른 시작(로컬)](#-빠른-시작로컬)
- [빠른 시작(Docker Compose)](#-빠른-시작docker-compose)
- [사용 가이드](#-사용-가이드)
- [AI 제공자 설정](#-ai-제공자-설정)
- [프로젝트 구조](#-프로젝트-구조)
- [WebSocket API 개요](#-websocket-api-개요)
- [persona_data 동기화](#-persona_data-동기화)
- [환경 변수env](#-환경-변수env)
- [Docker 아키텍처](#-docker-아키텍처)
- [문제 해결faq](#-문제-해결faq)
- [UI 레이아웃](#-ui-레이아웃)
- [토큰 사용량 표시](#-토큰-사용량-표시)
- [향후 개선 계획](#-향후-개선-계획)
- [기여, 라이선스, 크레딧](#-기여-라이선스-크레딧)

---

## ✨ 주요 특징

- **멀티 캐릭터 대화**
  - 여러 캐릭터가 동시에 말하는 그룹 채팅 형태
  - TRPG 파티 대화나 시나리오형 스토리텔링에 최적화

- **TRPG 스타일 GM 시스템**
  - AI 진행자(적극적, 보통, 소극적)
  - 내가 진행자 모드 (AI는 캐릭터만 연기)
  - 진행자 없음 모드

- **실시간 스트리밍 응답**
  - WebSocket 기반 스트리밍 출력
  - 타이핑되는 느낌 그대로 확인

- **히스토리 & Export**
  - 우측 패널에서 **서사 전용 마크다운 뷰** 제공
  - `GET /api/export`, `GET /api/export/stream`으로
    - JSON 혹은 Zip
    - NDJSON 스트리밍(대용량 백업용) 지원

- **멀티 AI 제공자**
  - Claude Code CLI
  - Gemini CLI
  - Droid CLI
  필요에 따라 선택 사용

- **세션 & 맥락 관리**
  - 최근 N턴만 프롬프트에 포함하는 슬라이딩 윈도우
  - 세션 유지 토글, 세션 초기화 버튼

- **토큰 사용량 추적**
  - 헤더에 모델별 토큰 사용량 표기
  - Claude Code 기준 입력/출력/캐시 토큰까지 세부 집계

- **3단 레이아웃 UI**
  - 좌측: 세계관·캐릭터·진행자 설정
  - 중앙: 실시간 채팅
  - 우측: 읽기 좋은 서사 기록

---

## 🧑‍💻 이런 분이 쓰면 잘 맞습니다

- 혼자 LLM 채팅만 하기 아쉬운 분
- **복수 캐릭터 롤플레이**나 **TRPG 로그**를 깔끔하게 관리하고 싶은 분
- Claude/Gemini/Droid CLI를 이미 쓰고 있고,
  "이거로 내 전용 TRPG 테이블 만들면 좋겠다" 싶으신 분
- 로컬에서 돌아가는, **개인 데이터가 밖으로 나가지 않는** 스토리 스튜디오가 필요한 분

---

## 🚀 빠른 시작(로컬)

### 1) 사전 요구사항

- Python 3.11 이상 (권장: 3.12)
- Node.js (AI CLI 설치용)
- 아래 AI CLI 중 최소 1개 이상 설치 및 인증

```bash
# Claude Code 설치 및 인증
npm install -g @anthropic-ai/claude-code
claude auth login

# Gemini CLI (선택)
npm install -g @google/gemini-cli
gemini auth login

# Droid CLI (선택)
curl -fsSL https://app.factory.ai/cli | sh
droid auth login
````

### 2) 설치 및 실행

```bash
# 프로젝트 클론
git clone https://github.com/ginishuh/persona_chatbot.git
cd persona_chatbot

# Python 가상환경 설정(권장 디렉터리명: .venv)
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 시작
python3 -m server.websocket_server
```

서버가 뜨면:

* 웹 UI: [http://localhost:9000](http://localhost:9000)
* WebSocket: ws://localhost:8765

### 3) persona_data 프라이빗 레포 설정(권장)

`persona_data/` 디렉터리는 **캐릭터 프리셋과 세계관 템플릿**을 담는 곳입니다.
실제 플레이 로그나 민감한 텍스트는 **별도 프라이빗 저장소**에 두는 것을 권장합니다.

1. GitHub/GitLab에서 새 프라이빗 저장소 생성

   * 예: `my-persona-data`
   * 반드시 Private

2. `persona_chatbot` 내부에 클론

```bash
cd persona_chatbot

# 폴더명을 반드시 persona_data로 맞춰야 합니다.
git clone git@github.com:YOURNAME/YOUR-PRIVATE-REPO.git persona_data
```

3. 폴더 구조 예시

```text
persona_chatbot/
├── server/
├── web/
├── chatbot_workspace/
├── persona_data/         # 프라이빗 데이터 레포 (이름 고정)
├── README.md
└── ...
```

> 서버는 `persona_data`라는 폴더명을 고정으로 참조합니다.
> 다른 이름으로 클론했다면 폴더명을 꼭 `persona_data`로 변경하세요.

### 4) DB 경로(특히 WSL 환경)

* 기본 DB 경로: `data/chatbot.db` (git ignore 처리)
* WSL에서는 `/mnt/c` 경로보다 리눅스 파일시스템(예: `~/persona_chatbot/data`) 사용을 권장합니다.
* 환경 변수 예시

```bash
DB_PATH=/home/<user>/.persona_chatbot/chatbot.db
```

### 5) Pre-commit 훅 설치(선택)

```bash
pip install pre-commit
bash scripts/install_hooks.sh
pre-commit run --all-files
```

---

## 🐳 빠른 시작(Docker Compose)

Docker Compose로 한 번에 올릴 수 있습니다.

```bash
# 1) 환경에 맞는 .env 템플릿 선택
cp examples/env/.env.example.vps-root .env       # 예: VPS 루트 컨테이너

# 2) docker-compose 템플릿 복사
cp docker-compose.yml.example docker-compose.yml

# 3) 컨테이너 빌드 및 실행
docker compose up -d

# 로그 확인
docker compose logs -f

# 컨테이너 중지
docker compose down
```

접속: [http://localhost:9000](http://localhost:9000)

### 4) 관리자 계정 생성 (중요)

**SQLite Lock 방지를 위해 관리자 계정은 반드시 컨테이너 안에서 생성**해야 합니다:

```bash
# 컨테이너 접속 후 관리자 계정 생성
docker-compose -f docker-compose.yml.example exec persona-chatbot python3 -c "
from server.handlers.db_handler import DBHandler
import asyncio

async def create_admin():
    db = DBHandler('./data')
    await db.initialize()
    success = await db.create_admin_user('admin', 'your-password')
    print('관리자 생성 성공' if success else '이미 존재함')

asyncio.run(create_admin())
"
```

호스트에서 직접 실행하면 SQLite Lock 문제가 발생합니다.

---

## 🎮 사용 가이드

### 1) 컨텍스트 설정

좌측 패널에서 "이 방이 어떤 세계인지"를 정의합니다.

1. **세계관/배경**

   * 예: `근미래 서울`, `중세 판타지 왕국`
2. **현재 상황**

   * 예: `길드 회의가 막 끝난 상황`, `수업 시작 5분 전 강의실`
3. **나의 캐릭터**

   * 이름, 역할, 성격 등
4. **진행자 설정** (선택)

   * AI 진행자: 서사와 배경을 AI가 풀어가는 모드
   * 내가 진행자: 사용자가 상황 설명, AI는 캐릭터 연기 전담
   * 진행자 없음
5. **캐릭터 추가**

   * 파티원이나 NPC들을 등록
6. 마지막으로 **💾 컨텍스트 저장** 버튼

### 2) 대화 모드 예시

#### 일반 대화

```text
사용자: 오늘 뭐 할까?

[민수]: 나는 게임하려고! 너도 할래?
[지은]: 민수야, 너 숙제 다 했어?
[민수]: 아... 그게... 나중에 할게ㅋㅋ
```

#### AI 진행자 모드

```text
[진행자]: 갑자기 복도에서 큰 소리가 들린다.
[민수]: 어? 저거 뭐야? (호기심 가득한 표정으로)
[지은]: 나가서 확인해볼까?
```

### 3) 맥락 길이 & 세션 관리

좌측 설정에서 진행자 관련 옵션과 함께 아래를 조절합니다.

| 기능           | 위치      | 설명                                |
| ------------ | ------- | --------------------------------- |
| 🧠 맥락 길이     | 슬라이더    | 5~60턴 (기본 30). 프롬프트에 포함되는 최대 턴 수  |
| 무제한 토글       | 슬라이더 아래 | 모든 대화를 프롬프트에 포함. 토큰 소모 증가 주의      |
| ♻️ 세션 유지     | 체크박스    | ON: CLI 세션 재사용, OFF: 매 메시지마다 새 세션 |
| 세션 상태 배지     | 헤더 우측   | 현재 세션 유지 상태 표시 (ON/OFF)           |
| ♻️ 세션 초기화 버튼 | 헤더 우측   | 모든 세션 ID 초기화                      |
| 🗑️ 대화 초기화   | 헤더 우측   | 대화 내용과 세션을 모두 초기화                 |

참고

* 서사(Markdown) 저장은 항상 **전체 대화 기준**입니다.
* Gemini는 stateless만 지원합니다. (세션 유지 불가)
* 세션 유지 OFF로 전환하면 기존 세션은 바로 초기화됩니다.

### 4) 히스토리 & Export

* 우측 패널에서 대화를 **읽기 전용 마크다운**으로 확인
* 백업/공유는 HTTP Export를 사용합니다.

```bash
# 단일 방(JSON)
curl -OJ "http://localhost:9000/api/export?scope=single&room_id=default"

# 선택 방 + 토큰 포함(Zip)
curl -OJ "http://localhost:9000/api/export?scope=selected&room_ids=room1,room2&include=messages,context,token_usage&format=zip"

# 기간 필터(전체, JSON)
curl -OJ "http://localhost:9000/api/export?scope=full&start=2025-11-01&end=2025-11-12"
```

NDJSON 스트리밍(대용량)도 지원합니다.

```bash
# 단일 방(메시지+컨텍스트)
curl -OJ "http://localhost:9000/api/export/stream?scope=single&room_id=default&include=messages,context"

# 전체(메시지+토큰 사용량)
curl -OJ "http://localhost:9000/api/export/stream?scope=full&include=messages,token_usage"

# 날짜 범위 필터
curl -OJ "http://localhost:9000/api/export/stream?scope=single&room_id=default&start=2025-11-01&end=2025-11-12"
```

라인 타입: `meta`, `room`, `message`, `token_usage`, `end`

---

## 🤖 AI 제공자 설정

좌측 패널에서 **AI 제공자**를 고를 수 있습니다.

### Claude (Anthropic)

* 인증: OAuth (`~/.claude/...`)
* 설치:

```bash
npm install -g @anthropic-ai/claude-code
claude auth login
```

* 세션 유지 지원

### Gemini (Google)

* 인증: OAuth (`~/.config/gemini/...`)
* 설치:

```bash
npm install -g @google/gemini-cli
gemini auth login
```

* stateless 동작 (세션 유지 불가)

### Droid (Factory.ai)

* 인증: OAuth (`~/.factory/auth.json`) 또는 API 키
* 설치:

```bash
curl -fsSL https://app.factory.ai/cli | sh
droid auth login
```

* 세션 유지 지원
* 기본 모델을 바꾸고 싶다면 `server/handlers/droid_handler.py`에서 조정

---

## 🗂 프로젝트 구조

```text
persona_chatbot/
├── server/
│   ├── websocket_server.py          # WebSocket 서버(핵심 엔트리)
│   ├── core/                        # AppContext/세션/인증 유틸
│   ├── http/                        # HTTP 서버(SPA fallback + /api/export)
│   ├── ws/                          # WebSocket 액션 라우터/액션들
│   └── handlers/                    # 모델/워크스페이스/히스토리 등
│       ├── claude_handler.py        # Claude Code CLI 통신
│       ├── droid_handler.py         # Droid CLI 통신
│       ├── gemini_handler.py        # Gemini CLI 통신
│       ├── context_handler.py       # 컨텍스트 관리
│       ├── history_handler.py       # 대화 히스토리(윈도우) 관리
│       ├── db_handler.py            # SQLite 영속 계층(aiosqlite)
│       ├── workspace_handler.py     # 프리셋/파일(템플릿) 관리
│       └── mode_handler.py          # 모드 상태 관리(스크립트용)
├── web/
│   ├── index.html                   # 레이아웃 UI(좌:설정 / 중:채팅 / 우:히스토리)
│   ├── app.js                       # 프론트엔드 로직
│   └── style.css                    # 라이트 테마 스타일
├── chatbot_workspace/
│   ├── CLAUDE.md                    # 챗봇 전용 지침(샘플에서 복사)
│   └── GEMINI.md                    # Gemini 전용 지침(샘플에서 복사)
├── persona_data/                    # 캐릭터/세계관 프리셋(별도 레포 권장)
├── requirements.txt                 # Python 의존성
└── README.md
```

---

## 🔌 WebSocket API 개요

모든 메시지는 JSON 형식입니다.

```json
{ "action": "액션명", "data": { ... } }
```

### 주요 액션

| 액션                                        | 설명                        |
| ----------------------------------------- | ------------------------- |
| `set_context`                             | 컨텍스트 설정(세계관, 캐릭터 등)       |
| `get_context`                             | 현재 컨텍스트 조회                |
| `chat`                                    | AI 대화 시작 (스트리밍 응답)        |
| `clear_history`                           | 대화 히스토리 초기화               |
| `get_narrative`                           | 히스토리 마크다운 가져오기            |
| `get_history_settings`                    | 맥락 길이 설정 조회               |
| `set_history_limit`                       | 맥락 길이 변경 (5~1000 또는 null) |
| `get_session_settings`                    | 세션 유지 설정 조회               |
| `set_session_retention`                   | 세션 유지 토글(true/false)      |
| `reset_sessions`                          | 모든 세션 ID 초기화              |
| `list_files` / `read_file` / `write_file` | 파일 관리                     |

### 예시: 대화 전송

요청

```json
{
  "action": "chat",
  "prompt": "안녕? 오늘 뭐 할까?"
}
```

스트리밍 응답

```json
{
  "action": "chat_stream",
  "data": {
    "type": "assistant",
    "message": {
      "content": [
        { "type": "text", "text": "[민수]: 오 나는 게임하려고!" }
      ]
    }
  }
}
```

완료 응답

```json
{
  "action": "chat_complete",
  "data": {
    "success": true,
    "message": "[민수]: 오 나는 게임하려고!\n[지은]: 숙제 다 했어?",
    "session_id": "abc123",
    "provider_used": "claude"
  }
}
```

---

## 📦 Import

간단한 Import는 WebSocket으로 처리합니다. JSON 스키마는 Export 결과를 그대로 사용합니다.

요청 예시

```json
{
  "action": "import_data",
  "import_mode": "new",           // "new" | "merge"
  "target_room_id": "room1",      // merge일 때 대상 방
  "duplicate_policy": "skip",     // "skip" | "add"
  "json_data": { /* export JSON */ }
}
```

응답 예시

```json
{
  "action": "import_data",
  "data": {
    "success": true,
    "rooms_imported": 1,
    "messages_imported": 245,
    "new_room_ids": ["fantasy_adventure_001"]
  }
}
```

클라이언트에서는 `/backup` 화면에서 Export 파라미터를 구성하고 다운로드할 수 있습니다.
대용량 업로드가 필요하다면 추후 `POST /api/import`가 추가될 예정입니다.

---

## 🔁 persona_data 동기화 & Workspace 격리

### Workspace 격리

개발용 설정과 챗봇용 설정을 분리합니다.

* 루트 `/CLAUDE.md`: 개발용 지침
* `chatbot_workspace/CLAUDE.md`: 챗봇 전용 지침

핵심 아이디어

```python
# server/handlers/claude_handler.py
args = [
    "claude",
    "--setting-sources", "user,local",  # project 제외 (루트 CLAUDE.md 무시)
    # ...
]

self.process = await asyncio.create_subprocess_exec(
    *args,
    cwd=str(self.chatbot_workspace)      # chatbot_workspace/에서 실행
)
```

동작 원리

1. `cwd=chatbot_workspace`로 설정
2. `--setting-sources user,local`로 project 레벨 설정 무시
3. 결과적으로 `chatbot_workspace/CLAUDE.md`만 읽음

### 챗봇 지침 파일 준비

레포에는 샘플 파일만 포함되어 있습니다.

```bash
cp chatbot_workspace/CLAUDE.sample.md  chatbot_workspace/CLAUDE.md
cp chatbot_workspace/GEMINI.sample.md chatbot_workspace/GEMINI.md
```

이 파일들은 `.gitignore`에 포함되어 있어 로컬에서 마음껏 수정 가능합니다.

---

## ⚙️ 환경 변수(.env)

```bash
# AI CLI 인증(호스트 절대 경로)
FACTORY_AUTH_DIR=/home/user/.factory
CLAUDE_AUTH_DIR=/home/user/.claude
GEMINI_AUTH_DIR=/home/user/.gemini

# Droid API 키 (선택)
FACTORY_API_KEY=your-api-key

# 간단 로그인 (비워두면 인증 없음)
APP_LOGIN_PASSWORD=yourpassword
APP_JWT_SECRET=your-secret-key  # 로그인 사용 시 반드시 함께 설정

# 토큰 수명 (리프레시 토큰 도입)
# ACCESS 기본값: APP_JWT_TTL (없으면 7일), REFRESH 기본값 30일
APP_ACCESS_TTL=3600
APP_REFRESH_TTL=2592000
APP_REFRESH_ROTATE=1    # 1이면 갱신 시마다 새 토큰 발급

# 포트 바인딩 (기본: 127.0.0.1, 외부 공개 시 0.0.0.0)
APP_BIND_HOST=127.0.0.1

# 토큰 사용량 표시 (1=표시, 0=숨김)
SHOW_TOKEN_USAGE=1
```

환경별 샘플

* VPS(루트 컨테이너): `examples/env/.env.example.vps-root`
* VPS(일반 사용자 컨테이너): `examples/env/.env.example.vps-user`
* 일반 Linux(루트 컨테이너): `examples/env/.env.example.root-linux`
* 일반 Linux(사용자 컨테이너): `examples/env/.env.example.user-linux`
* 로컬 개발(프록시 없음): `examples/env/.env.example.local-dev`

핵심 포인트

* UID/GID: 루트(0:0) vs 일반 사용자(1000:1000)
* 인증 디렉터리 3종은 반드시 채워야 합니다.
* 외부 도메인을 사용할 경우 `APP_PUBLIC_WS_URL=wss://<도메인>/ws`

---

## 🐳 Docker 아키텍처

이미지에 포함되는 것

* Node.js 22
* Python 3.11
* Claude Code CLI, Gemini CLI, Droid CLI
* Python 의존성 (websockets, aiofiles)
* 애플리케이션 코드(`server/`, `web/`)

호스트에서 마운트되는 것

* AI CLI 인증 정보(`~/.claude`, `~/.factory`, `~/.gemini`)
* 개발 코드(`./server`, `./web`) – 실시간 반영
* 데이터(`./persona_data`, `./chatbot_workspace`)

Compose는 기본적으로 `Dockerfile.full`을 사용합니다.

추가 커스텀은 `docker-compose.override.yml`에 넣고,
공용 `docker-compose.yml`은 템플릿으로만 유지합니다.

---

## 🛠 문제 해결(FAQ)

### Pre-commit이 CI에서만 실패해요

* 로컬에 훅이 설치되지 않았을 수 있습니다.

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### 9000/8765 포트 충돌

```bash
# 기존 서버 종료
lsof -ti:8765 | xargs -r kill -9
lsof -ti:9000 | xargs -r kill -9

# 또는
pkill -f "python.*websocket_server.py"
```

### 로그인 활성화 후 토큰 오류

* `APP_LOGIN_PASSWORD`를 설정했다면, 반드시 `APP_JWT_SECRET`도 함께 설정해야 합니다.

### AI CLI 인증 확인

```bash
# Claude
claude auth login

# Gemini
gemini auth login

# Droid
droid auth login
```

### WebSocket 연결 실패

1. 서버 실행 여부

```bash
ps aux | grep websocket_server
```

2. 포트 확인

```bash
lsof -i :9000
lsof -i :8765
```

3. 서버 로그 확인(서버 실행 터미널)

### 대화가 맥락을 잊어버리는 경우

* 🧠 맥락 길이 슬라이더를 늘리거나, `무제한` 토글을 켭니다.
* ♻️ 세션 유지 토글을 ON으로 설정합니다(Claude/Droid만).
* 서버 기본값을 바꾸려면
  `server/handlers/history_handler.py`의 `HistoryHandler(max_turns=50)` 값을 조정합니다.

---

## 🧱 UI 레이아웃

```text
┌─────────────────────────────────────────────────────────────┐
│  📖 Persona Chat    [OFF] 🗑️ 초기화  ♻️ 세션  ● 연결됨   │
├──────────┬──────────────────────────┬──────────────────────┤
│          │                          │                      │
│ 컨텍스트  │     메인 채팅창           │   서사 기록           │
│ 설정     │                          │                      │
│ (접기/펼치기) │   [사용자 메시지]        │  # 서사 기록          │
│          │   [캐릭터 응답]           │                      │
│  세계관   │   [캐릭터 응답]           │  ## 1. 사용자        │
│  상황    │                          │  ...                │
│  캐릭터   │   ┌──────────────────┐   │                      │
│  진행자   │   │ 메시지 입력...    │   │  ## 2. AI 응답       │
│  모드    │   │                  │   │  ...                │
│          │   └─────────── [전송] │   │                      │
│  💾 저장  │                          │  💾 저장             │
└──────────┴──────────────────────────┴──────────────────────┘
```

반응형 동작

* 가로 1200px 이하: 패널 크기 축소
* 가로 900px 이하: 세 패널이 세로로 스택

---

## 📊 토큰 사용량 표시

헤더 영역에 모델별 토큰 사용량이 표시됩니다.

지원 현황

* ✅ Claude Code: 입력/출력/캐시 토큰 상세 정보
* ❌ Gemini CLI: 토큰 정보 미제공
* ❌ Droid CLI: 토큰 정보 미제공

표시 정보

* 누적 사용량: 전체 대화 토큰 총합
* 최근 사용량: 마지막 메시지에서 사용한 토큰
* 상세 내역: 입력/출력/캐시 읽기/캐시 생성 토큰 (툴팁)
* 사용률: 컨텍스트 윈도우 대비 사용 비율

  * 🟢 50% 미만
  * 🟡 50~80%
  * 🔴 80% 이상

`.env`에서 On/Off 가능

```bash
# 토큰 사용량 표시 (1=표시, 0=숨김)
SHOW_TOKEN_USAGE=1
```

주의사항

* 토큰 사용량은 채팅방(room) 단위로 추적
* 대화 히스토리 초기화 시 토큰 카운트도 함께 리셋
* 토큰 정보를 제공하지 않는 모델은 `"토큰: 정보 없음"`으로 표시

---

## 🔮 향후 개선 계획

* [x] 대화 히스토리 관리(슬라이더, 무제한, 세션 토글)
* [x] 서사 기록 자동 생성 및 다운로드
* [x] GM/진행자 모드
* [x] 3단 레이아웃 UI
* [x] Docker 지원
* [x] 멀티 AI 제공자 지원(Claude, Droid, Gemini)
* [x] 캐릭터 프리셋 저장 및 관리
* [x] 간단 로그인 + JWT 세션 갱신
* [x] 모델별 토큰 사용량 표시(Claude)
* [x] 다크/라이트 테마 전환
* [x] 회원제 시스템 (사용자별 데이터 격리)
* [ ] Claude API 직접 연동(현재는 CLI 기반)
* [ ] 다중 컨텍스트 프로필(세이브 슬롯)
* [ ] 캐릭터 아바타/이미지 지원
* [ ] 음성 출력(TTS) 연동
* [ ] 다국어 지원

---

## 🤝 기여, 라이선스, 크레딧

### 기여

* 이슈와 Pull Request를 언제든 환영합니다.
* 버그 제보, 기능 제안, 문서 개선 모두 큰 도움이 됩니다.

### 라이선스

* MIT License

### 크레딧

* AI 제공자: Claude Code CLI(Anthropic), Gemini CLI(Google), Droid CLI(Factory.ai)
* 주요 라이브러리: `websockets`, `aiofiles`

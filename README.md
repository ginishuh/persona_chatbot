# 📖 Persona Chat – 멀티 캐릭터 대화 시스템

웹 기반 멀티 캐릭터 대화/서사 관리 시스템입니다. Claude Code, Droid CLI, Gemini CLI를 이용해 실시간 스트리밍 대화를 제공합니다.

> 2025-11-12 기준: Claude ✅, Droid ✅, Gemini ✅ (로컬/Docker 모두 동작 확인)

목차

- 주요 기능
- 빠른 시작(로컬)
- 빠른 시작(Docker Compose)
- 개발 가이드(테스트/커버리지/훅)
- AI 제공자 설정
- 프로젝트 구조
- WebSocket API 개요
- persona_data 동기화(컨테이너/호스트)
- 환경 변수(.env)
- 문제 해결(FAQ)

## 주요 기능

- **멀티 캐릭터 대화**: 여러 캐릭터가 동시에 참여하는 그룹 채팅 형식
- **TRPG 스타일 GM 시스템**: AI 진행자(적극적/보통/소극적), 사용자 진행자, 진행자 없음 모드
- **실시간 스트리밍**: WebSocket 기반 즉각 응답
- **히스토리/Export**: 대화 히스토리를 우측 패널에서 확인하고, HTTP `/api/export`로 JSON(선택 Zip) 다운로드. 대용량은 `/api/export/stream`(NDJSON) 권장.
- **멀티 AI 지원**: Claude, Gemini, Droid CLI 중 선택 가능
- **세션 & 맥락 관리**: 대화 히스토리 길이 조절, 세션 유지/리셋 기능
- **토큰 사용량 추적**: 모델별 토큰 사용량 실시간 표시 (Claude 지원)
- **3단 레이아웃**: 컨텍스트 설정(좌) / 채팅(중) / 서사 기록(우)

## 빠른 시작

### 1) 사전 요구사항

- Python 3.11+ (권장: 3.12)
- Node.js (AI CLI 설치용)
- AI CLI 중 최소 1개 이상 설치 및 인증

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
```

### 2) 설치 및 실행 (로컬)

```bash
# 프로젝트 클론
git clone <repository-url>
cd persona_chatbot

# Python 가상환경 설정(권장 디렉터리명: .venv)
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 시작
python server/websocket_server.py
```

서버가 시작되면:
- 웹 UI: http://localhost:9000
- WebSocket: ws://localhost:8765

### 3) 데이터 경로 및 persona_data 설정 (권장)

`persona_data/` 디렉토리는 캐릭터 프리셋/세계관 등 템플릿을 담습니다(스토리 파일 기능은 제거). 민감 데이터는 **별도 프라이빗 저장소**로 관리하는 것을 권장합니다.

#### 프라이빗 레포 생성 및 클론

1. **GitHub/GitLab에서 새 프라이빗 저장소 생성**
   - 저장소 이름은 자유롭게 설정 (예: `my-persona-data`)
   - 반드시 **Private**으로 설정

2. **persona_chatbot 디렉토리 내부에 클론**
   ```bash
   # persona_chatbot 프로젝트 디렉토리로 이동
   cd persona_chatbot

   # 프라이빗 레포 클론 (폴더명을 반드시 persona_data로 지정)
   git clone git@github.com:YOURNAME/YOUR-PRIVATE-REPO.git persona_data
   ```

3. **폴더 구조 확인**
   ```
   persona_chatbot/
   ├── server/
   ├── web/
   ├── chatbot_workspace/
   ├── persona_data/         # 프라이빗 데이터 레포 (이름 고정!)
   ├── README.md
   └── ...
   ```

> **중요**: 서버는 `persona_data` 폴더명을 고정으로 참조합니다. 다른 이름으로 클론한 경우 반드시 폴더명을 `persona_data`로 변경하세요.

WSL 권장 DB 경로
- 기본 DB 경로는 레포 내부 `data/chatbot.db` 입니다(`.gitignore` 처리). WSL에서는 속도/락 이슈를 피하기 위해 `/mnt/c`가 아닌 리눅스 파일시스템(예: `~/persona_chatbot/data`)을 사용하세요.
- 환경 변수로 DB 경로를 바꾸려면 `DB_PATH=/home/<user>/.persona_chatbot/chatbot.db`처럼 설정할 수 있습니다.

### 4) 로컬 훅(린트/보안) 설치

커밋/푸시 전 자동 포맷/린트/보안 점검을 위해 Pre-commit 훅 설치를 권장합니다.

```bash
pip install pre-commit
bash scripts/install_hooks.sh
pre-commit run --all-files  # 스모크
```

## 사용 가이드

### 컨텍스트 설정

좌측 패널에서 대화 환경을 설정합니다:

1. **세계관/배경**: 스토리의 배경 설정 (예: "현대 한국 대학교")
2. **현재 상황**: 현재 벌어지는 상황 (예: "점심시간 학생식당")
3. **나의 캐릭터**: 사용자 캐릭터 설정
4. **진행자 설정** (선택):
   - **AI 진행자**: AI가 상황 묘사 (적극적/보통/소극적)
   - **내가 진행자**: 사용자가 상황 설명, AI는 캐릭터만 연기
5. **캐릭터 추가**: 대화에 참여할 NPC 캐릭터 추가
6. **💾 컨텍스트 저장** 클릭

### 대화 모드

#### 일반 대화
```
사용자: 오늘 뭐 할까?

[민수]: 나는 게임하려고! 너도 할래?
[지은]: 민수야, 너 숙제 다 했어?
[민수]: 아... 그게... 나중에 할게ㅋㅋ
```

#### AI 진행자 모드
```
[진행자]: 갑자기 복도에서 큰 소리가 들린다.
[민수]: 어? 저거 뭐야? (호기심 가득한 표정으로)
[지은]: 나가서 확인해볼까?
```

### 맥락 길이 & 세션 관리

좌측 패널에서 진행자 관련 설정을 제어할 수 있습니다. (이전 버전의 ‘모드 전환(챗봇↔코딩)’ UI는 제거되었습니다.)

| 기능 | 위치 | 설명 |
| --- | --- | --- |
| **🧠 맥락 길이** | 슬라이더 | 5~60턴 선택 (기본 30턴). 모델에 전달되는 최근 대화 길이 제어 |
| **무제한 토글** | 슬라이더 아래 | 모든 대화를 prompt에 포함 (토큰 소모 증가 주의) |
| **♻️ 세션 유지** | 체크박스 | ON: CLI 세션 재사용, OFF: 매 메시지마다 새 세션 (기본) |
| **세션 상태 배지** | 헤더 우측 | 현재 세션 유지 상태 표시 (ON/OFF) |
| **♻️ 세션 버튼** | 헤더 우측 | 모든 세션 ID 초기화 |
| **🗑️ 대화 초기화** | 헤더 우측 | 대화 내용과 세션 모두 초기화 |

참고
- 서사(MD) 저장은 항상 전체 대화 기준(슬라이더와 무관)
- Gemini는 현재 stateless만 지원(세션 유지 불가)
- 세션 유지 OFF 전환 시 즉시 모든 세션 초기화

### 히스토리 & Export

- 우측 패널에서 대화 히스토리를 읽기 전용으로 확인합니다(마크다운 렌더링).
- 백업/공유는 HTTP Export 사용: `GET /api/export?scope=single&room_id=<id>`.
  - scope: `single` | `selected` | `full`
  - 선택 파라미터: `room_ids=a,b`(selected), 추후 `format=zip`, 날짜 필터 등 확장 예정
- WebSocket 기반 stories 파일(저장/불러오기/이어하기) 기능은 제거되었습니다.

## AI 제공자 설정

좌측 패널/설정에서 **AI 제공자**를 선택할 수 있습니다. (이전의 `모드` 탭은 제거되었습니다.)

### Claude (Anthropic)
- 인증: OAuth (`~/.claude/...`)
- 설치: `npm install -g @anthropic-ai/claude-code`
- 상태: 세션 유지 지원

### Gemini (Google)
- 인증: OAuth (`~/.config/gemini/...`) – API 키 미사용
- 설치: `npm install -g @google/gemini-cli`
- 상태: stateless 동작

### Droid (Factory.ai)
- 인증: OAuth (`~/.factory/auth.json`) 또는 API 키
- 설치: `curl -fsSL https://app.factory.ai/cli | sh`
- 상태: 세션 유지 지원
- 참고: 모델 변경이 필요하면 `server/handlers/droid_handler.py`에서 조정

## 프로젝트 구조

```
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

## API 요약

모든 메시지는 JSON 형식: `{"action": "액션명", "data": {...}}`

### 주요 액션

| 액션 | 설명 |
|------|------|
| `set_context` | 컨텍스트 설정 (세계관, 캐릭터 등) |
| `get_context` | 현재 컨텍스트 조회 |
| `chat` | AI 대화 (스트리밍 응답) |
| `clear_history` | 대화 히스토리 초기화 |
| `get_narrative` | 히스토리 마크다운 가져오기 |
| `get_history_settings` | 맥락 길이 설정 조회 |
| `set_history_limit` | 맥락 길이 변경 (5~1000 또는 null) |
| `get_session_settings` | 세션 유지 설정 조회 |
| `set_session_retention` | 세션 유지 토글 (true/false) |

HTTP Export

| 파라미터 | 값 | 기본값 | 설명 |
|---|---|---|---|
| `scope` | `single`/`selected`/`full` | `single` | Export 범위 |
| `room_id` | 문자열 | `default` | `scope=single`일 때 대상 방 |
| `room_ids` | `a,b,c` | - | `scope=selected`일 때 대상 방 목록 |
| `include` | `messages,context,token_usage` | `messages,context` | 포함 항목 선택 |
| `start` | `YYYY-MM-DD` 또는 `YYYY-MM-DDTHH:MM:SS` | - | 시작 시점 필터 |
| `end` | `YYYY-MM-DD` 또는 `YYYY-MM-DDTHH:MM:SS` | - | 종료 시점 필터 |
| `format` | `json`/`zip` | `json` | zip은 내부에 JSON 1개 포함 |

예시

```bash
# 단일 방(JSON)
curl -OJ "http://localhost:9000/api/export?scope=single&room_id=default"

# 선택 방 + 토큰 포함(Zip)
curl -OJ "http://localhost:9000/api/export?scope=selected&room_ids=room1,room2&include=messages,context,token_usage&format=zip"

# 기간 필터(전체, JSON)
curl -OJ "http://localhost:9000/api/export?scope=full&start=2025-11-01&end=2025-11-12"
```

NDJSON 스트리밍(대용량 권장)

```bash
# 단일 방(메시지+컨텍스트)
curl -OJ "http://localhost:9000/api/export/stream?scope=single&room_id=default&include=messages,context"

# 전체(메시지+토큰사용량)
curl -OJ "http://localhost:9000/api/export/stream?scope=full&include=messages,token_usage"

# 날짜 범위 필터
curl -OJ "http://localhost:9000/api/export/stream?scope=single&room_id=default&start=2025-11-01&end=2025-11-12"
```

라인 타입: `meta`, `room`, `message`, `token_usage`, `end`

### Import (초기: WebSocket)

간단한 Import는 WebSocket 액션으로 지원합니다. JSON 스키마는 Export 결과(single_room/full_backup)를 그대로 사용합니다.

요청
```json
{
  "action": "import_data",
  "import_mode": "new",           // "new" | "merge"
  "target_room_id": "room1",      // merge일 때 대상 방
  "duplicate_policy": "skip",     // "skip" | "add"
  "json_data": { /* export JSON */ }
}
```

응답
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

참고
- 현재는 WS 중심. 대용량 업로드가 필요하면 HTTP `POST /api/import`를 추가 예정입니다.

### /backup UI (클라이언트)

- 주소창에 `/backup`으로 진입하거나, 앱 내에서 백업 모달을 열어 파라미터를 구성하고 다운로드할 수 있습니다.
- scope/include/date/format(JSON/ZIP/NDJSON)를 선택하면 적합한 HTTP 경로(`/api/export` 또는 `/api/export/stream`)를 호출합니다.

라우팅(History API)
- 클라이언트는 History API 라우팅을 사용합니다(`/`, `/rooms/:id`, `/rooms/:id/history`, `/backup`).
- 서버는 SPA fallback을 제공해 새로고침 404가 발생하지 않습니다.
| `reset_sessions` | 모든 세션 ID 초기화 |
| `list_files` / `read_file` / `write_file` | 파일 관리 |

### 예시: 대화 전송

**요청:**
```json
{
  "action": "chat",
  "prompt": "안녕? 오늘 뭐 할까?"
}
```

**스트리밍 응답:**
```json
{
  "action": "chat_stream",
  "data": {
    "type": "assistant",
    "message": {
      "content": [{"type": "text", "text": "[민수]: 오 나는 게임하려고!"}]
    }
  }
}
```

**완료 응답:**
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

## 빠른 시작(Docker Compose)

Docker Compose를 사용하여 컨테이너로 실행할 수 있습니다.

### 빠른 시작

```bash
# 1) .env 생성(환경에 맞는 템플릿 택1)
#    예) VPS 루트 컨테이너 환경
cp examples/env/.env.example.vps-root .env

# 2) Compose 템플릿 복사(레포는 예시만 커밋합니다)
cp docker-compose.yml.example docker-compose.yml

# 3) 컨테이너 빌드 및 실행
docker compose up -d

# 로그 확인
docker compose logs -f

# 컨테이너 중지
docker compose down
```

접속: http://localhost:9000

## 개발 가이드(테스트/커버리지/훅)

- 테스트: `pytest -q`
- 커버리지 기준: 타깃 모듈 총합 ≥ 90% (CI 동일)
  - 타깃: `server.handlers.{history,context,mode,file}_handler`
- 훅 설치: `pip install pre-commit && bash scripts/install_hooks.sh`
- 수동 전체 검사: `pre-commit run --all-files`
  - 구성: `.pre-commit-config.yaml`, `pyproject.toml`, `bandit.yaml`, `.secrets.baseline`
  - `persona_data/`는 전역 exclude 처리

## CI (GitHub Actions)

공개 레포지토리용 CI를 제공합니다.

- 워크플로: `.github/workflows/ci.yml`
- 단계:
  - Pre-commit 훅 실행(Black/Ruff/Bandit/detect-secrets)
  - PyTest + 커버리지(타깃 모듈 ≥ 90%)
  - 커버리지 타깃: `server.handlers.{history_handler,context_handler,mode_handler,file_handler}` (`--cov-fail-under=90`)
  - CLI 의존이 큰 핸들러(claude/droid/gemini, git/workspace)는 단계적으로 모킹 테스트를 추가 예정입니다.


### 상태/스모크 테스트 (2025-11-10 확인)

- 현재 상태: ✅ Claude / ✅ Droid / ✅ Gemini 모두 정상 동작 확인됨 (Docker/로컬 모두).
- 간단 스모크 테스트 스크립트: `scripts/ws_chat_test.py`

실행 예시:

```bash
# 1) 컨테이너 기동
docker compose up --build -d

# 2) WebSocket 스모크 테스트 (로그인/컨텍스트/스트리밍 포함)
python scripts/ws_chat_test.py --provider claude --prompt "테스트: Claude"
python scripts/ws_chat_test.py --provider droid  --prompt "테스트: Droid"
python scripts/ws_chat_test.py --provider gemini --prompt "테스트: Gemini"
```

참고
- 로그인 사용 시 `.env`의 `APP_LOGIN_PASSWORD`와 `APP_JWT_SECRET`를 함께 설정해야 합니다.
- Docker 사용 시 인증 디렉토리는 호스트 절대 경로 권장:
  - `FACTORY_AUTH_DIR=$HOME/.factory`, `CLAUDE_AUTH_DIR=$HOME/.claude`, `GEMINI_AUTH_DIR=$HOME/.gemini`

### 환경 변수(.env)

```bash
# AI CLI 인증 (호스트 경로 절대 경로)
FACTORY_AUTH_DIR=/home/user/.factory
CLAUDE_AUTH_DIR=/home/user/.claude
GEMINI_AUTH_DIR=/home/user/.gemini

# Droid API 키 (선택)
FACTORY_API_KEY=your-api-key

# 간단 로그인 (선택, 비워두면 인증 없음)
APP_LOGIN_PASSWORD=yourpassword
APP_JWT_SECRET=your-secret-key  # 로그인 사용 시 반드시 함께 설정

# 토큰 수명 (리프레시 토큰 도입)
# ACCESS 기본값: APP_JWT_TTL (없으면 7일), REFRESH 기본 30일
# 운영 권장: ACCESS 15~60분, REFRESH 7~30일
APP_ACCESS_TTL=3600
APP_REFRESH_TTL=2592000
# 리프레시 토큰 회전 (1=매 갱신 시 새 토큰 발급)
APP_REFRESH_ROTATE=1

# 포트 바인딩 (기본: 127.0.0.1, 외부 공개 시 0.0.0.0)
APP_BIND_HOST=127.0.0.1

# 토큰 사용량 표시 (1=표시, 0=숨김)
# 기본값: 1 (표시)
# 민감 정보일 수 있으므로 필요에 따라 비활성화할 수 있습니다.
SHOW_TOKEN_USAGE=1
```

#### 환경별 .env 선택표

- 상황에 맞는 샘플을 복사해 `.env`로 사용하세요.
  - VPS(루트 컨테이너): `examples/env/.env.example.vps-root`
  - VPS(일반 사용자 컨테이너): `examples/env/.env.example.vps-user`
  - 일반 Linux(루트 컨테이너): `examples/env/.env.example.root-linux`
  - 일반 Linux(사용자 컨테이너): `examples/env/.env.example.user-linux`
  - 로컬 개발(프록시 없음): `examples/env/.env.example.local-dev`

- 핵심 분기
  - UID/GID: 루트(`0:0`) vs 일반 사용자(`1000:1000`)
  - 인증 디렉터리 3종: `FACTORY_AUTH_DIR`, `CLAUDE_AUTH_DIR`, `GEMINI_AUTH_DIR` 반드시 채우기
  - 도메인/프록시: `APP_PUBLIC_WS_URL=wss://<도메인>/ws`

#### docker-compose 로컬 커스텀

- 레포의 기본 `docker-compose.yml`은 공용 템플릿입니다. 로컬 환경 차이는 `docker-compose.override.yml`로 분리하세요.
- `docker-compose.override.yml`은 `.gitignore`에 포함되어 커밋되지 않습니다.
- 예시:

```yaml
services:
  persona-chatbot:
    environment:
      - APP_PUBLIC_WS_URL=wss://chat.example.com/ws
    # 필요 시 추가 볼륨/리소스/포트 오버라이드
```

> 참고: Compose는 `.env` 값을 자동으로 읽습니다. 가능하면 Compose 수정 대신 `.env`로 관리하세요.

### Docker 아키텍처

#### 이미지에 포함된 것
- Node.js 22 + Python 3.11
- Claude Code CLI, Gemini CLI, Droid CLI
- Python 의존성 (websockets, aiofiles)
- 애플리케이션 코드 (`server/`, `web/`)

> Compose는 `Dockerfile.full`을 사용합니다(Claude/Gemini/Droid CLI 포함). 최소 `Dockerfile`은 제거했습니다.

#### 호스트에서 마운트되는 것
- AI CLI 인증 정보(`~/.claude`, `~/.factory`, `~/.gemini`)
- 개발 코드(`./server`, `./web`) – 실시간 반영
- 데이터(`./persona_data`, `./chatbot_workspace`)
  - 서사 파일은 `persona_data/stories/`에 저장됩니다(별도 `STORIES/` 마운트 불필요).

#### Workspace 격리

개발용 지침(`/CLAUDE.md`)과 챗봇용 지침(`chatbot_workspace/CLAUDE.md`)을 분리합니다:

```python
# server/handlers/claude_handler.py
args = [
    "claude",
    "--setting-sources", "user,local",  # project 제외 (루트 CLAUDE.md 무시)
    # ...
]

self.process = await asyncio.create_subprocess_exec(
    *args,
    cwd=str(self.chatbot_workspace)  # chatbot_workspace/에서 실행
)
```

**동작 원리**:
1. `cwd=chatbot_workspace` → AI CLI가 `chatbot_workspace/`에서 실행
2. `--setting-sources user,local` → project 레벨 설정 무시
3. 결과: `chatbot_workspace/CLAUDE.md`만 읽고, 루트 `CLAUDE.md`는 무시

### 챗봇 지침 파일 준비

레포에는 샘플 파일만 포함되어 있으므로, 최초 실행 전 복사하세요:

```bash
cp chatbot_workspace/CLAUDE.sample.md chatbot_workspace/CLAUDE.md
cp chatbot_workspace/GEMINI.sample.md chatbot_workspace/GEMINI.md
```

이 파일들은 `.gitignore`에 포함되어 로컬에서 자유롭게 수정할 수 있습니다.

## 문제 해결(FAQ)

- Pre-commit이 CI에서만 실패해요
  - 로컬에서 훅이 설치되지 않았을 수 있습니다. `pip install pre-commit && pre-commit install && pre-commit run --all-files`로 확인하세요.
- 9000/8765 포트 충돌
  - 이미 사용 중인 프로세스를 종료하거나 Docker로 실행하세요.
- 로그인 활성화 후 토큰 오류
  - `APP_LOGIN_PASSWORD` 설정 시 `APP_JWT_SECRET`가 반드시 있어야 합니다. 둘 다 `.env`에 설정하세요.

### Docker vs 로컬 실행

| 항목 | Docker | 로컬 실행 |
|------|--------|-----------|
| **환경 격리** | ✅ 완전 격리 | ❌ 호스트 환경 영향 |
| **의존성 관리** | ✅ 이미지에 포함 | ❌ 수동 설치 |
| **배포** | ✅ 어디서나 동일 | ❌ 환경별 설정 |
| **개발 속도** | ⚠️ 빌드 시간 | ✅ 즉시 실행 |
| **디버깅** | ⚠️ 컨테이너 진입 | ✅ 직접 디버깅 |

**권장 시나리오**:
- **Docker**: 프로덕션 배포, 환경 통일
- **로컬**: 빠른 개발, 디버깅

## 문제 해결

### 포트 충돌

```bash
# 기존 서버 종료
lsof -ti:8765 | xargs -r kill -9
lsof -ti:9000 | xargs -r kill -9

# 또는 pkill 사용
pkill -f "python.*websocket_server.py"
```

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

1. 서버 실행 확인:
   ```bash
   ps aux | grep websocket_server
   ```

2. 포트 확인:
   ```bash
   lsof -i :9000
   lsof -i :8765
   ```

3. 로그 확인 (서버 터미널)

### 대화가 맥락을 잊어버리는 경우

- 좌측 패널/설정의 **🧠 맥락 길이** 슬라이더를 늘리거나 `무제한` 토글 활성화
- **♻️ 세션 유지** 토글을 ON으로 설정 (Claude/Droid만)
- 서버 기본값 변경: `server/handlers/history_handler.py` → `HistoryHandler(max_turns=50)`

## UI 레이아웃

```
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

**반응형 디자인**:
- 1200px 이하: 패널 크기 축소
- 900px 이하: 수직 스택 레이아웃

## 토큰 사용량 표시

헤더 영역에 모델별 토큰 사용량이 실시간으로 표시됩니다.

### 지원 현황
- ✅ **Claude Code**: 입력/출력/캐시 토큰 상세 정보 제공
- ❌ **Gemini CLI**: 토큰 정보 미제공
- ❌ **Droid CLI**: 토큰 정보 미제공

### 표시 정보
- **누적 사용량**: 전체 대화에서 사용한 총 토큰 수
- **최근 사용량**: 마지막 메시지에서 사용한 토큰 수
- **상세 내역**: 입력/출력/캐시 읽기/캐시 생성 토큰 (툴팁에 표시)
- **사용률**: 컨텍스트 윈도우 대비 사용 비율 (색상으로 표시)
  - 🟢 초록색: 50% 미만 (정상)
  - 🟡 노란색: 50-80% (주의)
  - 🔴 빨간색: 80% 이상 (경고)

### 설정 방법
`.env` 파일에서 토큰 표시 ON/OFF를 제어할 수 있습니다:

```bash
# 토큰 사용량 표시 (1=표시, 0=숨김)
SHOW_TOKEN_USAGE=1
```

- `SHOW_TOKEN_USAGE=1`: 토큰 사용량 표시 (기본값)
- `SHOW_TOKEN_USAGE=0`: 토큰 사용량 숨김 (민감 정보 보호)

### 주의사항
- 토큰 사용량은 채팅방(room) 단위로 추적됩니다
- 대화 히스토리를 초기화하면 토큰 카운트도 함께 초기화됩니다
- 토큰 정보를 제공하지 않는 AI 모델 사용 시 "토큰: 정보 없음"으로 표시됩니다

## 향후 개선 사항

- [x] 대화 히스토리 관리 (슬라이더/무제한/세션 토글)
- [x] 서사 기록 자동 생성 및 다운로드
- [x] GM/진행자 모드
- [x] 3단 레이아웃 UI
- [x] Docker 지원
- [x] 멀티 AI 제공자 지원 (Claude, Droid, Gemini)
- [x] 캐릭터 프리셋 저장 및 관리
- [x] 간단 로그인 + JWT 세션 갱신
- [x] 모델별 토큰 사용량 표시 (Claude 지원)
- [ ] Claude API 직접 연동 (현재는 CLI만)
- [ ] 대화 히스토리 영구 저장 (DB)
- [ ] 다중 컨텍스트 프로필 (세이브 슬롯)
- [ ] 캐릭터 아바타/이미지 지원
- [ ] 음성 출력 (TTS) 연동
- [ ] 다국어 지원
- [ ] 다크/라이트 테마 전환

## 기여

이슈 및 Pull Request를 환영합니다.

## 라이선스

MIT License

## 크레딧

- **AI 제공자**: Claude Code CLI (Anthropic), Gemini CLI (Google), Droid CLI (Factory.ai)
- **라이브러리**: websockets, aiofiles

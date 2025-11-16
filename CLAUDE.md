# CLAUDE.md

Persona Chat용 Claude Code 개발 지침입니다.

## 프로젝트 개요

Persona Chat은 Claude Code CLI를 AI 백엔드로 사용하는 멀티캐릭터 대화 시스템입니다. WebSocket 실시간 통신과 TRPG 스타일의 게임 마스터 기능을 지원합니다.

**핵심**: 채팅봇은 `chatbot_workspace/` 격리 공간에서 실행되며 자체 CLAUDE.md(성인 콘텐츠 지침)를 가집니다.

## 실행 방법

### Docker Compose (권장)

```bash
# 환경변수 설정
export UID=$(id -u) GID=$(id -g)
export CLAUDE_AUTH_DIR=$HOME/.claude
export GEMINI_AUTH_DIR=$HOME/.gemini
export FACTORY_AUTH_DIR=$HOME/.factory
export APP_JWT_SECRET=$(openssl rand -hex 32)
export APP_LOGIN_PASSWORD=your-admin-password

# 서버 시작
docker-compose -f docker-compose.yml.example up -d

# 서버 중지
docker-compose -f docker-compose.yml.example down
```

서버 접속:
- HTTP: `http://127.0.0.1:9000` (web/ 정적 파일)
- WebSocket: `ws://127.0.0.1:8765`

### 직접 실행 (개발용)

```bash
# 서버 시작 (프로젝트 루트에서)
python3 -m server.websocket_server

# 또는 가상환경 사용
./venv/bin/python -m server.websocket_server
```

### 서버 중지

```bash
pkill -f "python.*websocket_server"
# 또는
lsof -ti:8765 | xargs -r kill -9
lsof -ti:9000 | xargs -r kill -9
```

## 아키텍처

### 핵심 구조

```
브라우저 (WebSocket) → 서버 (8765) → 핸들러 → Claude Code CLI (subprocess)
```

**중요**: 각 메시지마다 새 Claude Code 프로세스가 생성됩니다. 세션 연속성은 대화 기록을 시스템 프롬프트에 주입하여 유지합니다.

### 디렉토리

```
persona_chatbot/
├── server/
│   ├── websocket_server.py       # 메인 서버 + 라우팅
│   ├── http/                     # HTTP 서버 (정적 파일)
│   ├── ws/                       # WebSocket 액션 핸들러
│   └── handlers/                 # 비즈니스 로직
├── web/                          # 프론트엔드 (HTML/CSS/JS)
├── data/                         # DB 및 영속성 데이터 (도커 볼륨)
├── persona_data/                 # 프리셋/워크스페이스 공유 (도커 볼륨)
├── chatbot_workspace/            # Claude Code 격리 작업공간
│   └── CLAUDE.md                 # 채팅봇 전용 지침
├── docker-compose.yml.example    # Docker Compose 설정 예제
├── Dockerfile.full              # 전체 기능 포함 도커 이미지
└── .claude/                      # 개발용 지침
```

### 핵심 핸들러

- **ClaudeHandler**: Claude Code subprocess 관리 (120초 타임아웃)
- **HistoryHandler**: 슬라이딩 윈도우 대화 기록 (기본 30 턴)
- **ContextHandler**: 시스템 프롬프트 빌더 (월드/캐릭터/진행자 설정)
- **FileHandler**: 파일 입출력
- **WorkspaceHandler**: 페르소나 데이터 관리

### WebSocket API

주요 액션들:
- `set_context` - 월드/캐릭터/진행자 모드 설정
- `get_context` - 현재 컨텍스트 조회
- `chat` - 메시지 전송 (스트리밍 응답)
- `clear_history` - 대화 기록 초기화
- `get_narrative` - 대화 내보내기 (마크다운)
- 파일 관련 액션들 (`list_files`, `read_file`, `write_file`)

### 인증

JWT 기반 인증 사용:
- Access Token: 7일
- Refresh Token: 30일
- 환경변수: `APP_JWT_SECRET`, `APP_JWT_ALGORITHM`, `APP_ACCESS_TTL`, `APP_REFRESH_TTL`

## 개발 작업

### 빠른 수정

- **히스토리 윈도우 크기**: `server/websocket_server.py`에서 `HistoryHandler(max_turns=N)`
- **Claude Code 경로**: `server/handlers/claude_handler.py`의 `__init__()` 수정
- **로깅 레벨**: `server/websocket_server.py`의 `logging.basicConfig(level=logging.DEBUG)`

### 프론트엔드 파싱

캐릭터 대화 형식: `[캐릭터명]: 대화 내용`

`web/app.js`에서 정규식 `/^\[(.+?)\]:\s*(.*)$/`로 파싱하며, 각 캐릭터는 색상 클래스(`character-0`~`character-4`)를 할당받습니다. `[진행자]`는 특별한 금색 스타일링을 사용합니다.

## 요구사항

### Docker (권장)
- Docker와 Docker Compose
- Claude Code CLI 인증 정보: `$HOME/.claude/`
- Gemini CLI 인증 정보: `$HOME/.gemini/` (선택)
- Factory 인증 정보: `$HOME/.factory/` (Droid용, 선택)

### 직접 실행
- Python 3.8+
- Claude Code CLI 설치 및 인증 (`claude auth login`)
- 의존성 (`requirements.txt`): websockets 12.0, aiofiles 23.2.1, PyJWT 2.10.1, aiosqlite 0.19.0, bcrypt 4.1.2

## Docker 주요 설정

### 볼륨 마운트
- `./data:/app/data` - DB 및 영속성 데이터
- `./persona_data:/app/persona_data` - 프리셋/워크스페이스
- `./chatbot_workspace:/app/chatbot_workspace` - 채팅봇 작업공간
- 인증 디렉토리들 (`~/.claude`, `~/.gemini`, `~/.factory`)

### 보안
- 포트는 `127.0.0.1`에만 바인딩 (로컬 전용)
- 운영 환경에서는 nginx 등 리버스 프록시 사용 권장
- JWT Secret 필수 설정

### 중요: 관리자 계정 생성

**관리자 시드 생성은 반드시 컨테이너 안에서 실행**해야 합니다:

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

## 중요 제약사항

### 워크스페이스 격리

채팅봇은 `chatbot_workspace/`에서 실행되어 이 디렉토리의 `CLAUDE.md`만 읽습니다. 이는 개발 지침과 채팅봇 지침이 섞이는 것을 방지합니다. `chatbot_workspace/CLAUDE.md`는 사용자 요청이 없으면 수정하지 마세요.

### WebSocket API 버전

websockets v13+ API 사용: `async def websocket_handler(websocket)` (path 파라미터 없음)

### 프로세스 상태

Claude Code 프로세스는 stdin을 닫으면 종료되므로 각 메시지마다 새 프로세스를 생성해야 합니다. 이는 핸들러에서 자동으로 관리됩니다.

---

참고: 성인 콘텐츠/크리에이티브 지침은 `chatbot_workspace/CLAUDE.md`에 있으며 의도적으로 격리되어 있습니다.

# 📖 Persona Chat - 멀티 캐릭터 대화 시스템

Claude Code와 Droid CLI, GEMINI CLI를 활용한 웹 기반 멀티 캐릭터 대화 및 서사 관리 시스템입니다.

## 주요 기능

- **멀티 캐릭터 대화**: 여러 캐릭터가 동시에 참여하는 그룹 채팅 형식
- **TRPG 스타일 GM 시스템**: AI 진행자(적극적/보통/소극적), 사용자 진행자, 진행자 없음 모드
- **실시간 스트리밍**: WebSocket 기반 즉각 응답
- **서사 기록**: 대화 내용을 마크다운으로 자동 기록 및 다운로드
- **멀티 AI 지원**: Claude, Gemini, Droid CLI 중 선택 가능
- **세션 & 맥락 관리**: 대화 히스토리 길이 조절, 세션 유지/리셋 기능
- **3단 레이아웃**: 컨텍스트 설정(좌) / 채팅(중) / 서사 기록(우)

## 빠른 시작

### 1. 사전 요구사항

- Python 3.8+
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

### 2. 설치 및 실행

```bash
# 프로젝트 클론
git clone <repository-url>
cd persona_chatbot

# Python 가상환경 설정
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 시작
python server/websocket_server.py
```

서버가 시작되면:
- **웹 UI**: http://localhost:9000
- **WebSocket**: ws://localhost:8765

### 3. persona_data 디렉토리 설정 (권장)

`persona_data/` 디렉토리는 캐릭터 프리셋, 세계관, 스토리 등 민감한 데이터를 담으므로 **별도 프라이빗 저장소**로 관리하는 것을 권장합니다.

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

> **참고**: 웹 UI의 **🔄 동기화** 버튼은 `persona_data` 레포에서 `git add/commit/push`를 수행합니다.

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

**참고**:
- 서사(MD) 저장은 항상 **전체 대화** 기준 (슬라이더 값과 무관)
- Gemini는 현재 stateless만 지원 (세션 유지 불가)
- 세션 유지 OFF 전환 시 즉시 모든 세션 초기화됨

### 서사 기록

우측 패널에서 대화 기록을 관리합니다:

- **자동 기록**: 대화가 진행되면 마크다운 형식으로 자동 저장
- **💾 저장 버튼**: `.md` 파일로 다운로드
- **전체 대화 보존**: 맥락 길이 설정과 무관하게 전체 내용 유지

### persona_data 동기화

헤더의 **🔄 동기화** 버튼으로 캐릭터/세계관 데이터를 백업할 수 있습니다:

**동작 방식**:
1. `persona_data/` 디렉토리의 모든 변경사항을 자동으로 감지
2. Git에 추가 (`git add -A`)
3. 타임스탬프와 함께 커밋 (`git commit -m "Sync: YYYY-MM-DD HH:MM:SS"`)
4. 원격 저장소에 푸시 (`git push`)

**주의사항**:
- `persona_data/`가 Git 저장소로 초기화되어 있어야 함
- 원격 저장소(GitHub/GitLab 등)가 설정되어 있어야 푸시 가능
- 동기화 실패 시 서버 로그 확인 필요

**저장되는 데이터**:
- 캐릭터 프리셋 (`characters/`)
- 세계관 설정 (`worlds/`)
- NPC 데이터 (`npcs/`)
- 저장된 스토리/시나리오

## AI 제공자 설정

좌측 패널/설정에서 **AI 제공자**를 선택할 수 있습니다. (이전의 `모드` 탭은 제거되었습니다.)

### Claude (Anthropic)
- **모델**: Claude Sonnet 4.5
- **인증**: OAuth (`~/.claude/.credentials.json`)
- **설치**: `npm install -g @anthropic-ai/claude-code`
- **상태**: ✅ 완벽 지원 (세션 유지 지원)

### Gemini (Google)
- **모델**: Gemini 2.5 Pro
- **인증**: OAuth (`~/.config/gemini/oauth_creds.json`) - API 키 미지원
- **할당량**: 60 requests/min, 1,000 requests/day (무료)
- **설치**: `npm install -g @google/gemini-cli`
- **상태**: ✅ 완벽 지원 (stateless만)

### Droid (Factory.ai)
- **모델**: 사용자 설정 가능 (기본: `custom:glm-4.6`, 무료)
- **인증**: OAuth (`~/.factory/auth.json`) 또는 API 키
- **설치**: `curl -fsSL https://app.factory.ai/cli | sh`
- **상태**: ✅ 완벽 지원 (세션 유지 지원)
- **참고**: 다른 모델 사용 시 `server/handlers/droid_handler.py` 수정 필요

## 프로젝트 구조

```
persona_chatbot/
├── server/
│   ├── websocket_server.py          # WebSocket 서버
│   └── handlers/
│       ├── claude_handler.py        # Claude Code CLI 통신
│       ├── droid_handler.py         # Droid CLI 통신
│       ├── gemini_handler.py        # Gemini CLI 통신
│       ├── context_handler.py       # 컨텍스트 관리
│       ├── history_handler.py       # 대화 히스토리 & 서사 생성
│       ├── workspace_handler.py     # 파일 관리
│       └── mode_handler.py          # 모드 상태 관리
├── web/
│   ├── index.html                   # 3단 레이아웃 UI
│   ├── app.js                       # 프론트엔드 로직
│   └── style.css                    # VS Code 스타일 테마
├── chatbot_workspace/
│   ├── CLAUDE.md                    # 챗봇 전용 지침 (성인 콘텐츠 규칙)
│   └── GEMINI.md                    # Gemini 전용 지침
├── persona_data/                    # 캐릭터/세계관 데이터 (별도 레포)
├── STORIES/                         # 서사 파일 저장
├── requirements.txt                 # Python 의존성
└── README.md
```

## WebSocket API

모든 메시지는 JSON 형식: `{"action": "액션명", "data": {...}}`

### 주요 액션

| 액션 | 설명 |
|------|------|
| `set_context` | 컨텍스트 설정 (세계관, 캐릭터 등) |
| `get_context` | 현재 컨텍스트 조회 |
| `chat` | AI 대화 (스트리밍 응답) |
| `clear_history` | 대화 히스토리 초기화 |
| `get_narrative` | 서사 마크다운 가져오기 |
| `get_history_settings` | 맥락 길이 설정 조회 |
| `set_history_limit` | 맥락 길이 변경 (5~1000 또는 null) |
| `get_session_settings` | 세션 유지 설정 조회 |
| `set_session_retention` | 세션 유지 토글 (true/false) |
| `reset_sessions` | 모든 세션 ID 초기화 |
| `list_files` / `read_file` / `write_file` | 파일 관리 |
| `git_status` / `git_push` | Git 작업 |

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

## Docker 실행

Docker Compose를 사용하여 컨테이너로 실행할 수 있습니다.

### 빠른 시작

```bash
# 컨테이너 빌드 및 실행
docker compose up -d

# 로그 확인
docker compose logs -f

# 컨테이너 중지
docker compose down
```

접속: http://localhost:9000

### Docker/Git 동기화 가이드 (중요)

웹 UI의 "🔄 동기화" 버튼은 `persona_data/` 디렉토리에서 `git add/commit/push`를 수행합니다. 컨테이너 내부 사용자(`node`, UID 1000)에는 전역 Git 사용자 설정이 없으므로, 다음을 참고해 주세요.

#### 1) "Author identity unknown" 오류 해결

증상:

```
Author identity unknown
Please tell me who you are.
```

원인: 컨테이너 내부에 전역 Git 사용자 정보가 없어 커밋 작성자 정보를 알 수 없습니다.

해결(레포 로컬 설정 권장):

```bash
# 호스트에서 실행 (권장)
git -C persona_data config user.name "YOUR_NAME"
git -C persona_data config user.email "you@example.com"

# 또는 컨테이너 안에서 실행
docker compose exec persona-chatbot bash -lc \
  'git -C /app/persona_data config user.name "YOUR_NAME" && \
   git -C /app/persona_data config user.email "you@example.com"'
```

참고: 컨테이너에 `git config --global`을 넣어도 됩니다만, 이미지/컨테이너 재생성 시 유실될 수 있으므로 레포 **로컬 설정**을 추천합니다.

#### 2) 원격 푸시 설정(선택)

`persona_data`를 프라이빗 원격 저장소로 백업하려면 아래 중 하나를 선택하세요.

- HTTPS + PAT(권장):
  ```bash
  # 1) 원격이 HTTPS인지 확인/변경
  git -C persona_data remote set-url origin https://github.com/<USER>/<REPO>.git

  # 2) 최초 푸시 시 사용자명/PAT 입력(토큰은 GitHub Settings → Developer settings → PAT 생성)
  git -C persona_data push -u origin master

  # 선택) 자격 증명 저장(개발 PC 한정, 보안 주의)
  git -C persona_data config credential.helper store
  ```

- SSH 키 사용:
  ```bash
  # 원격을 SSH로 설정
  git -C persona_data remote set-url origin git@github.com:<USER>/<REPO>.git

  # 컨테이너에 SSH 키를 마운트(예시)
  # docker-compose.yml 의 volumes 아래 추가 (호스트 경로는 환경에 맞게 수정)
  #   - ~/.ssh:/home/node/.ssh:ro
  ```

#### 2.5) 호스트 푸시 모드(보안 선호)

컨테이너에서 `git push`를 수행하지 않고, UI의 동기화 버튼은 커밋과 함께
호스트에 "푸시 요청" 트리거 파일을 남기고, 실제 푸시는 호스트에서 수행하는 모드입니다.

장점: 컨테이너에 PAT/SSH 자격증명을 저장하지 않아도 되며, 호스트의 Git 설정을 그대로 활용합니다.

사용법:

1) Compose 환경변수 설정(컨테이너 푸시 비활성화)

docker-compose.yml의 `environment` 블록에 추가:

```
  - APP_GIT_SYNC_MODE=host
```

2) 호스트 워처 실행(별도 터미널)

```
chmod +x scripts/host_git_sync_*.sh
# REPO_DIR는 생략 가능(기본은 현재 저장소 기준 ../persona_data)
REPO_DIR="$(pwd)/persona_data" ./scripts/host_git_sync_watch.sh
```

동작: 컨테이너는 `persona_data/.sync/push_*.json` 파일을 생성하고,
호스트 워처는 이를 감지하여 `git -C persona_data pull --rebase && git -C persona_data push`를 실행합니다.

팁: systemd --user 유닛으로 등록하면 백그라운드에서 영속 실행할 수 있습니다.

#### 3) 권한/소유권 이슈(특히 STORIES)

`STORIES/` 디렉토리가 `root:root` 소유이고 권한이 `755`인 경우, 호스트에서 서버를 실행하면 쓰기 실패가 날 수 있습니다. 다음 명령으로 소유권을 현재 사용자로 변경하세요.

```bash
sudo chown -R $(id -u):$(id -g) STORIES
```

Docker를 사용하는 경우에도 호스트 디렉토리의 소유자가 현재 사용자(UID/GID)와 일치하는지 확인하는 것이 안전합니다. 본 프로젝트의 Compose는 컨테이너를 `${UID}:${GID}`로 실행하므로, 호스트와 UID/GID가 맞으면 권한 이슈가 줄어듭니다.

### 환경 변수 설정 (.env)

```bash
# AI CLI 인증 (호스트 경로 절대 경로)
FACTORY_AUTH_DIR=/home/user/.factory
CLAUDE_AUTH_DIR=/home/user/.claude
GEMINI_AUTH_DIR=/home/user/.gemini

# Droid API 키 (선택)
FACTORY_API_KEY=your-api-key

# 간단 로그인 (선택, 비워두면 인증 없음)
APP_LOGIN_PASSWORD=yourpassword
APP_JWT_SECRET=your-secret-key

# 토큰 수명 (리프레시 토큰 도입)
# ACCESS 기본값: APP_JWT_TTL (없으면 7일), REFRESH 기본 30일
# 운영 권장: ACCESS 15~60분, REFRESH 7~30일
APP_ACCESS_TTL=3600
APP_REFRESH_TTL=2592000
# 리프레시 토큰 회전 (1=매 갱신 시 새 토큰 발급)
APP_REFRESH_ROTATE=1

# 포트 바인딩 (기본: 127.0.0.1, 외부 공개 시 0.0.0.0)
APP_BIND_HOST=127.0.0.1
```

### Docker 아키텍처

#### 이미지에 포함된 것
- Node.js 22 + Python 3.11
- Claude Code CLI, Gemini CLI, Droid CLI
- Python 의존성 (websockets, aiofiles)
- 애플리케이션 코드 (`server/`, `web/`)

#### 호스트에서 마운트되는 것
- AI CLI 인증 정보 (`~/.claude`, `~/.factory`, `~/.gemini`)
- 개발 코드 (`./server`, `./web`) - 실시간 반영
- 데이터 (`./persona_data`, `./chatbot_workspace`, `./STORIES`)

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

## 향후 개선 사항

- [x] 대화 히스토리 관리 (슬라이더/무제한/세션 토글)
- [x] 서사 기록 자동 생성 및 다운로드
- [x] GM/진행자 모드
- [x] 3단 레이아웃 UI
- [x] Docker 지원
- [x] 멀티 AI 제공자 지원 (Claude, Droid, Gemini)
- [x] 캐릭터 프리셋 저장 및 관리
- [x] 간단 로그인 + JWT 세션 갱신
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

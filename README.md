# 📖 Persona Chat - 멀티 캐릭터 대화 시스템

Claude Code를 활용한 웹 기반 멀티 캐릭터 대화 및 서사 관리 시스템입니다.

## 주요 기능

### 1. 멀티 캐릭터 대화 시스템
- 여러 캐릭터가 동시에 대화에 참여하는 그룹 채팅 형식
- 각 캐릭터는 고유한 색상으로 구분되어 표시
- `[캐릭터명]: 대화내용` 형식으로 자동 파싱
- 실시간 스트리밍 응답
- **대화 히스토리 관리**: 최근 15턴 자동 유지로 맥락 있는 대화 가능
- **효과음 자동 줄바꿈**: `*...*` 형식의 효과음이 자동으로 줄바꿈되어 표시

### 2. TRPG 스타일 GM/진행자 시스템
- **AI 진행자 모드**: AI가 게임 마스터(GM) 역할 수행
  - **적극적**: 매 턴마다 상세한 상황 묘사와 이벤트 발생
  - **보통**: 중요한 장면에서만 개입
  - **소극적**: 캐릭터 대화 위주, 필요시에만 설명
- **사용자 진행자 모드**: 사용자가 GM 역할, AI는 캐릭터만 연기
- **진행자 비활성화**: 순수 캐릭터 간 대화만

### 3. 컨텍스트 관리
- **세계관/배경**: 스토리의 세계관과 시대적 배경 설정
- **현재 상황**: 현재 벌어지고 있는 상황 설명
- **나의 캐릭터**: 사용자 자신의 캐릭터 설정 (이름, 성격, 배경)
- **캐릭터 관리**: 대화에 참여할 캐릭터들을 추가/삭제 및 설정
- **성인 콘텐츠 모드**: 18+ 콘텐츠 허용 (선택적)

### 4. 서사 기록 시스템
- 대화 내용을 자동으로 마크다운 형식으로 기록
- 실시간 서사 업데이트
- 마크다운 파일(.md)로 다운로드 가능
- 대화 히스토리 초기화 기능

### 5. 3단 레이아웃 UI
- **좌측 패널**: 컨텍스트 설정 (접기/펼치기 가능)
- **중앙 패널**: 메인 채팅창 (가장 큰 영역)
- **우측 패널**: 서사 기록 및 다운로드

## 기술 스택

### Backend
- Python 3.x
- asyncio (비동기 처리)
- websockets 12.0 (WebSocket 통신)
- aiofiles 23.2.1 (비동기 파일 I/O)
- **AI 제공자 (3개 지원)**:
  - **Claude** (Anthropic) - Claude Code CLI
  - **Gemini** (Google) - Gemini CLI
  - **Droid** (Factory.ai) - Droid CLI

### Frontend
- HTML5 / CSS3 / Vanilla JavaScript
- WebSocket API (실시간 통신)
- VS Code 스타일 UI

### AI 제공자 상세

시스템은 3개의 AI CLI를 지원하며, UI에서 선택하여 사용할 수 있습니다:

#### 1. Claude (Anthropic)
- **인증**: OAuth (`~/.claude/.credentials.json`)
- **모델**: Claude Sonnet 4.5
- **상태**: ✅ 완벽 지원
- **설치**: `npm install -g @anthropic-ai/claude-code`

#### 2. Gemini (Google)
- **인증**: OAuth (`~/.config/gemini/oauth_creds.json`)  ← API 키 미지원
- **모델**: Gemini 2.5 Pro
- **무료 할당량**: 60 requests/min, 1,000 requests/day
- **상태**: ✅ 완벽 지원
- **설치**: `npm install -g @google/gemini-cli`

#### 3. Droid (Factory.ai)
- **인증**: OAuth (`~/.factory/auth.json`)
- **모델**: ⚠️ **사용자 설정 가능** (기본: `custom:glm-4.6`)
- **중요 사항**:
  - Droid는 `~/.factory/config.json`에서 사용자별 모델 설정을 읽습니다
  - 이 프로젝트는 `custom:glm-4.6` 모델을 사용하도록 기본 설정되어 있습니다 (무료)
  - 다른 모델을 사용하려면 `server/handlers/droid_handler.py`에서 `--model` 파라미터를 수정하세요
  - Factory.ai의 Claude 모델은 유료 구독이 필요합니다
- **상태**: ✅ 완벽 지원 (GLM-4.6)
- **설치**: `curl -fsSL https://app.factory.ai/cli | sh`

## 설치 및 실행

### 1. 사전 요구사항
- Python 3.8 이상
- **AI CLI 중 최소 1개 이상** 설치 및 인증 완료:
  - **Claude Code CLI** (권장)
  - **Gemini CLI** (선택)
  - **Droid CLI** (선택)
- Git (선택사항, Git 기능 사용 시)

```bash
# Claude Code 인증 확인
claude auth login

# Gemini CLI 인증 (OAuth)
gemini auth login

# Droid CLI 인증
droid auth login
```

### 2. 설치

```bash
# 프로젝트 클론 또는 다운로드
cd persona_chatbot

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Python 의존성 설치
pip install -r requirements.txt

# STORIES 디렉토리 생성 (없는 경우)
mkdir -p STORIES

# AI CLI 설치 (선택한 제공자에 따라)
# Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Gemini CLI (선택사항)
npm install -g @google/gemini-cli

# Droid CLI (선택사항)
curl -fsSL https://app.factory.ai/cli | sh
```

### 3. 실행

```bash
# 서버 시작
./venv/bin/python server/websocket_server.py

# 또는 가상환경 활성화 후
# source venv/bin/activate
# python server/websocket_server.py
```

서버가 시작되면 다음 포트에서 접근 가능합니다:
- **HTTP 서버**: http://localhost:9000
- **WebSocket 서버**: ws://localhost:8765

### 4. 웹 브라우저에서 접속

```
http://localhost:9000
```

## 사용법

### 1. 컨텍스트 설정

1. 좌측 패널 상단의 ⚙️ 아이콘으로 접기/펼치기
2. 세계관/배경 입력 (예: "현대 한국의 대학교")
3. 현재 상황 입력 (예: "점심시간, 학생식당에서")
4. 나의 캐릭터 설정 입력 (예: "이름: 김철수, 성격: 내성적이고 조용함")
5. **진행자(GM) 설정** (선택):
   - "AI 진행자" 체크: AI가 상황 설명 및 진행
     - 모드 선택: 적극적/보통/소극적
     - 진행자 성향 입력 가능
   - "내가 진행자" 체크: 사용자가 상황 설명, AI는 캐릭터만
6. "캐릭터 추가" 버튼으로 대화에 참여할 캐릭터 추가
   - 캐릭터 이름 (예: "민수")
   - 캐릭터 설명 (예: "외향적이고 유머러스한 학생")
7. 여러 캐릭터를 추가 가능
8. **성인 콘텐츠 허용** (선택): 18+ 콘텐츠 활성화
9. "💾 컨텍스트 저장" 클릭

### 2. 대화하기

#### 일반 대화 모드
1. 중앙 채팅 입력창에 메시지 입력
2. "전송" 버튼 클릭 또는 Enter 키
3. AI가 자동으로 적절한 캐릭터를 선택하여 응답
4. 여러 캐릭터가 동시에 응답 가능

**응답 예시:**
```
[민수]: 오 그거 좋은데? 나도 갈래!
[지은]: 민수야, 너 숙제는 다 했어?
[민수]: 아... 그게... 나중에 할게ㅋㅋ
```

#### GM 모드 (AI 진행자)
AI가 상황 설명과 캐릭터 대사를 함께 제공합니다:

```
[진행자]: 갑자기 복도에서 큰 소리가 들린다. 학생들의 웅성거리는 소리가 점점 가까워진다.
[민수]: 어? 저거 뭐야? (호기심 가득한 표정으로)
[지은]: 나가서 확인해볼까? 뭔가 심상치 않은데...
```

#### 사용자 진행자 모드
사용자가 상황을 설명하면 AI는 캐릭터만 연기합니다:

```
사용자: "갑자기 복도에서 큰 소리가 들린다."

[민수]: 어? 저거 뭐야? (호기심 가득한 표정으로)
[지은]: 나가서 확인해볼까? 뭔가 심상치 않은데...
```

### 3. 서사 기록

1. **자동 기록**: 대화가 진행되면 우측 패널에 자동으로 서사 기록
2. **마크다운 포맷**: 읽기 쉬운 형식으로 표시
3. **다운로드**: "💾 저장" 버튼으로 `.md` 파일로 다운로드
4. **초기화**: 헤더의 "🗑️ 대화 초기화" 버튼으로 히스토리 및 서사 초기화

### 4. 대화 히스토리

- 시스템이 자동으로 최근 15턴의 대화를 기억
- AI가 이전 맥락을 이해하고 연속적인 대화 가능
- 대화 초기화 버튼으로 새로운 대화 시작 가능

## 프로젝트 구조

```
persona_chatbot/
├── server/
│   ├── websocket_server.py      # 메인 WebSocket 서버
│   └── handlers/
│       ├── file_handler.py      # 파일 관리 핸들러
│       ├── git_handler.py       # Git 작업 핸들러
│       ├── claude_handler.py    # Claude Code 통신 핸들러
│       ├── droid_handler.py     # Droid CLI 통신 핸들러 ⭐ NEW
│       ├── gemini_handler.py    # Gemini CLI 통신 핸들러 ⭐ NEW
│       ├── context_handler.py   # 컨텍스트 관리 핸들러
│       ├── history_handler.py   # 대화 히스토리 관리 핸들러
│       ├── workspace_handler.py # 워크스페이스 파일 관리
│       └── mode_handler.py      # 모드 상태 관리
├── web/
│   ├── index.html               # 메인 HTML (3단 레이아웃)
│   ├── app.js                   # 프론트엔드 로직 (효과음 줄바꿈 포함)
│   └── style.css                # 스타일시트
├── chatbot_workspace/
│   └── CLAUDE.md                # 챗봇 전용 지침 (성인 콘텐츠 규칙)
├── STORIES/                     # 서사 파일 저장 디렉토리
├── venv/                        # Python 가상환경
├── requirements.txt             # Python 의존성
├── Dockerfile.test              # Node + Python 통합 Docker 이미지 (선택)
├── docker-compose.yml           # 기본 Docker Compose 설정
├── test_auth.sh                 # Docker 인증 테스트 스크립트
├── test_websocket.py            # WebSocket 테스트 스크립트
├── CLAUDE.md                    # 개발용 지침 (한국어 사용 규칙)
├── AGENTS.md                    # 에이전트 설정
└── README.md                    # 프로젝트 문서
```

## 주요 컴포넌트 설명

### 1. WebSocket 서버 (`server/websocket_server.py`)

서버와 클라이언트 간 실시간 양방향 통신을 담당합니다.

**지원 액션:**
- `list_files`: 파일 목록 조회
- `read_file`: 파일 읽기
- `write_file`: 파일 쓰기
- `git_status`: Git 상태 확인
- `git_push`: Git 커밋 및 푸시
- `set_context`: 컨텍스트 설정
- `get_context`: 컨텍스트 조회
- `clear_history`: 대화 히스토리 초기화 ⭐ NEW
- `get_narrative`: 서사 마크다운 가져오기 ⭐ NEW
- `chat`: AI 대화 (스트리밍, 히스토리 포함)

### 2. History Handler (`server/handlers/history_handler.py`) ⭐ NEW

대화 히스토리를 관리하고 서사를 생성합니다.

**특징:**
- 슬라이딩 윈도우: 최근 15턴 자동 유지
- `deque` 자료구조로 자동 오래된 메시지 제거
- 히스토리를 System Prompt에 포함하여 맥락 유지
- 마크다운 형식 서사 생성

**주요 메서드:**
```python
add_user_message(content)           # 사용자 메시지 추가
add_assistant_message(content)      # AI 응답 추가
get_history_text()                  # System Prompt용 텍스트
get_narrative_markdown()            # 서사 마크다운 생성
clear()                             # 히스토리 초기화
```

### 3. Context Handler (`server/handlers/context_handler.py`)

대화 컨텍스트를 관리하고 System Prompt를 생성합니다.

**관리 항목:**
- 세계관 (world)
- 현재 상황 (situation)
- 사용자 캐릭터 (user_character)
- 캐릭터 목록 (characters)
- 진행자 설정 (narrator_enabled, narrator_mode, narrator_description) ⭐ NEW
- 사용자 진행자 (user_is_narrator) ⭐ NEW
- 성인 콘텐츠 모드 (adult_mode) ⭐ NEW

**System Prompt 생성:**

생성되는 System Prompt는 다음과 같은 구조를 가집니다:

```
[진행자 모드별 프롬프트]

=== 콘텐츠 제한 해제 === (성인 모드 활성화 시)
...

=== 세계관 ===
[세계관 설명]

=== 현재 상황 ===
[현재 상황 설명]

=== 대화 상대 (사용자) ===
[사용자 캐릭터 설명]

=== 진행자 (당신) === (진행자 모드 활성화 시)
[진행자 설명]
**진행자 모드: 적극적/보통/소극적**
[모드별 가이드라인]

=== 등장 캐릭터들 ===
[캐릭터1]
[캐릭터1 설명]

[캐릭터2]
[캐릭터2 설명]

=== 이전 대화 내역 === (히스토리)
사용자: ...
AI: ...

위 대화 내용을 참고하여 자연스럽게 대화를 이어가세요.

=== 대화 규칙 ===
1. 사용자의 메시지를 읽고 적절한 캐릭터가 자연스럽게 응답하세요
2. 여러 캐릭터가 동시에 대화할 수 있습니다
3. 각 대사는 반드시 "[캐릭터명]: 내용" 형식으로 작성하세요
4. 누가 응답할지는 상황과 캐릭터 성격에 맞게 자연스럽게 결정하세요
5. 실제 그룹 채팅처럼 자연스럽고 생동감 있게 대화하세요
6. 캐릭터의 성격, 말투, 관계를 정확히 반영하세요
```

### 4. Claude Handler (`server/handlers/claude_handler.py`)

Claude Code CLI와 subprocess를 통해 통신합니다.

**특징:**
- `--output-format stream-json` 사용으로 실시간 스트리밍
- `--system-prompt` 옵션으로 컨텍스트 주입
- stdin/stdout/stderr 비동기 처리
- 타임아웃 처리 (120초)

**통신 방식:**
```python
# Claude Code CLI 실행
claude --print --verbose --output-format stream-json --system-prompt "..."

# stdin으로 프롬프트 전송
# stdout에서 JSON 스트림 수신
# stderr 비동기 처리로 버퍼 블로킹 방지
```

**중요 참고사항:**
- 매 메시지마다 새로운 프로세스 시작 (세션 유지 안 됨)
- 대신 히스토리를 System Prompt에 포함하여 맥락 유지

### 5. 멀티 캐릭터 파싱 (`web/app.js`)

Claude의 응답을 파싱하여 캐릭터별로 분리합니다.

**파싱 로직:**
```javascript
function parseMultiCharacterResponse(text) {
    const messages = [];
    const lines = text.split('\n');

    for (const line of lines) {
        // [캐릭터명]: 대화내용 패턴 매칭
        const match = line.match(/^\[(.+?)\]:\s*(.*)$/);
        if (match) {
            messages.push({
                character: match[1],
                text: match[2]
            });
        }
    }

    return messages;
}
```

**캐릭터 색상:**
- character-0: 파란색 계열 (#1e3a5f)
- character-1: 보라색 계열 (#3a1e5f)
- character-2: 초록색 계열 (#1e5f3a)
- character-3: 주황색 계열 (#5f3a1e)
- character-4: 분홍색 계열 (#5f1e3a)
- 진행자: 황금색 테두리 + 이탤릭체 (#c9a227)

## WebSocket API

### 메시지 형식

모든 메시지는 JSON 형식입니다:

```json
{
  "action": "액션명",
  "data": { ... }
}
```

### 액션 상세

#### 1. set_context - 컨텍스트 설정

**요청:**
```json
{
  "action": "set_context",
  "world": "세계관 설명",
  "situation": "현재 상황",
  "user_character": "사용자 캐릭터 설명",
  "narrator_enabled": true,
  "narrator_mode": "moderate",
  "narrator_description": "진행자 성향",
  "user_is_narrator": false,
  "adult_mode": false,
  "characters": [
    {
      "name": "민수",
      "description": "외향적이고 유머러스한 학생"
    },
    {
      "name": "지은",
      "description": "차분하고 책임감 있는 반장"
    }
  ]
}
```

**응답:**
```json
{
  "action": "set_context",
  "data": {
    "success": true,
    "context": { ... }
  }
}
```

#### 2. get_context - 컨텍스트 조회

**요청:**
```json
{"action": "get_context"}
```

**응답:**
```json
{
  "action": "get_context",
  "data": {
    "success": true,
    "context": {
      "world": "...",
      "situation": "...",
      "user_character": "...",
      "narrator_enabled": true,
      "narrator_mode": "moderate",
      "narrator_description": "...",
      "user_is_narrator": false,
      "adult_mode": false,
      "characters": [...]
    }
  }
}
```

#### 3. clear_history - 대화 히스토리 초기화 ⭐ NEW

**요청:**
```json
{"action": "clear_history"}
```

**응답:**
```json
{
  "action": "clear_history",
  "data": {
    "success": true,
    "message": "대화 히스토리가 초기화되었습니다"
  }
}
```

#### 4. get_narrative - 서사 가져오기 ⭐ NEW

**요청:**
```json
{"action": "get_narrative"}
```

**응답:**
```json
{
  "action": "get_narrative",
  "data": {
    "success": true,
    "markdown": "# 서사 기록\n\n## 1. 사용자\n\n안녕?\n\n..."
  }
}
```

#### 5. chat - AI 대화

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
      "content": [
        {
          "type": "text",
          "text": "[민수]: 오 나는 게임하려고!"
        }
      ]
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
    "result": { ... }
  }
}
```

## 문제 해결

### 포트 충돌

기본 포트가 사용 중인 경우 `server/websocket_server.py`를 수정:

```python
# HTTP 포트 변경 (기본: 9000)
with TCPServer(("0.0.0.0", 9000), CustomHandler) as httpd:

# WebSocket 포트 변경 (기본: 8765)
async with websockets.serve(websocket_handler, "0.0.0.0", 8765):
```

### 서버 재시작

```bash
# 기존 서버 프로세스 종료
lsof -ti:8765 | xargs -r kill -9
lsof -ti:9000 | xargs -r kill -9

# 서버 재시작
cd /home/ginis/persona_chatbot/server
source ../venv/bin/activate
python websocket_server.py
```

### Claude Code 인증

Claude Code가 인증되지 않은 경우:

```bash
claude auth login
```

### WebSocket 연결 실패

1. 서버가 실행 중인지 확인:
   ```bash
   ps aux | grep websocket_server
   ```

2. 포트가 열려있는지 확인:
   ```bash
   lsof -i :9000
   lsof -i :8765
   ```

3. 로그 확인 (서버 터미널에서 확인)

### 대화가 끊기거나 맥락을 잊어버리는 경우

- 시스템이 자동으로 15턴을 유지하므로 이후 오래된 대화는 잊어버립니다
- 필요시 `history_handler.py`의 `max_turns` 값을 조정:
  ```python
  history_handler = HistoryHandler(max_turns=30)  # 30턴으로 증가
  ```

## UI 레이아웃

### 3단 구조

```
┌─────────────────────────────────────────────────────────┐
│  📖 Persona Chat         🗑️ 대화 초기화  ● 연결됨    │
├──────────┬──────────────────────────┬──────────────────┤
│          │                          │                  │
│ 컨텍스트  │     메인 채팅창          │   서사 기록       │
│ 설정     │                          │                  │
│ (접기/펼치기) │   [사용자 메시지]       │  # 서사 기록      │
│          │   [캐릭터 응답]          │                  │
│  세계관   │   [캐릭터 응답]          │  ## 1. 사용자    │
│  상황    │                          │  ...            │
│  캐릭터   │   ┌──────────────────┐  │                  │
│  진행자   │   │ 메시지 입력...    │  │  ## 2. AI 응답   │
│          │   │                  │  │  ...            │
│  💾 저장  │   └─────────── [전송] │  │  💾 저장         │
└──────────┴──────────────────────────┴──────────────────┘
```

### 반응형 디자인

- 1200px 이하: 패널 크기 축소
- 900px 이하: 수직 스택 레이아웃으로 전환

## 향후 개선 사항

- [x] 대화 히스토리 관리 (최근 15턴)
- [x] 서사 기록 자동 생성 및 다운로드
- [x] GM/진행자 모드
- [x] 성인 콘텐츠 모드
- [x] 3단 레이아웃 UI
- [x] Docker 지원 (볼륨 마운트 방식)
- [x] 효과음 자동 줄바꿈 처리
- [x] 멀티 AI 제공자 지원 (Claude, Droid, Gemini)
- [ ] Claude API 연동 (현재는 CLI만 지원)
- [ ] 대화 히스토리 영구 저장
- [ ] 캐릭터 프리셋 저장 및 관리
- [ ] 다중 컨텍스트 프로필 (세이브 슬롯)
- [ ] 캐릭터 아바타/이미지 지원
- [ ] 음성 출력 (TTS) 연동
- [ ] 다국어 지원
- [ ] 다크/라이트 테마 전환
- [ ] 파일 관리 기능 재통합 (선택사항)

## 기술적 제약사항

### Claude Code CLI 세션 관리

현재 구현에서는 매 메시지마다 새로운 Claude Code 프로세스를 시작합니다. 이는 다음과 같은 이유 때문입니다:

1. **stdin.close() 문제**: stdin을 닫으면 프로세스가 종료됨
2. **세션 유지 불가**: 단일 프로세스로 여러 턴 대화 불가능
3. **해결 방법**: 히스토리를 System Prompt에 포함하여 맥락 유지

향후 Claude API를 사용하면 이 문제가 해결될 수 있습니다.

## Docker 지원

Docker 컨테이너로 실행할 수 있습니다. 볼륨 마운트 방식으로 호스트의 AI CLI 인증 정보를 사용합니다.

### Docker 실행 방법

```bash
# 컨테이너 빌드 및 실행
docker compose up -d

# 로그 확인
docker compose logs -f

# 컨테이너 중지
docker compose down
```

> **기본 docker-compose.yml 사용 시 참고**  
> - 기본 Python 기반 이미지에도 Droid CLI가 포함되므로, `.env`에 `FACTORY_API_KEY=sk-...` 형식으로 키만 지정해도 컨테이너에서 바로 Droid 메시지를 보낼 수 있습니다.  
> - 커스텀 모델을 사용할 경우 호스트의 `~/.factory` 폴더를 그대로 마운트하도록 구성되어 있으니, `config.json` 안의 `custom_models` 항목이 컨테이너에서도 동일하게 적용됩니다.  
> - 비상호작용 환경에서 Droid CLI가 권한 승인을 못 받아 멈추는 문제를 막기 위해 `DROID_SKIP_PERMISSIONS_UNSAFE=1`을 기본값으로 설정했습니다 (컨테이너 내부 한정).  
> - `FACTORY_API_KEY` 값은 `~/.factory/config.json`의 `custom_models` 배열에 있는 `api_key`를 복사하면 됩니다. 예: `FACTORY_API_KEY=$(jq -r '.custom_models[0].api_key' ~/.factory/config.json)`.  
> - 컨테이너에서는 `FACTORY_AUTO_UPDATE=0`으로 자동 업데이트를 끄고, 대신 최신 Droid CLI를 설치하려면 `docker exec -u root persona_chatbot_server sh -c "curl -fsSL https://app.factory.ai/cli | sh && cp /root/.local/bin/droid /usr/local/bin/droid"` 명령을 한 번 실행해 주세요.  
> - 만약 포트 충돌 또는 네트워크 잔여물이 생기면 `docker compose down --remove-orphans && docker compose up -d`로 정리한 뒤 재실행하세요.
> - 기본 compose는 `Dockerfile.test`를 사용하므로 Node 22 + Python 3.11 + 3개 AI CLI가 모두 포함된 단일 컨테이너가 뜹니다.

### Docker 구성

- **Dockerfile.test**: Node.js 22 + Python 3.11 + 3개 AI CLI (수동 빌드용)
  - Claude Code CLI: `npm install -g @anthropic-ai/claude-code`
  - Droid CLI: `curl -fsSL https://app.factory.ai/cli | sh`
  - Gemini CLI: `npm install -g @google/gemini-cli`
- **docker-compose.yml**: Dockerfile.test 기반 WebSocket/HTTP 통합 서비스
  - 포트: 8765 (WebSocket), 9000 (HTTP) – 기본은 127.0.0.1 바인딩이므로 외부 노출이 필요하면 프록시/포트를 조정하세요
  - 볼륨 마운트: `./STORIES`, `./server`, `./web`, `./persona_data`, `./chatbot_workspace`, `${HOME}/.factory:/home/node/.factory`, `${HOME}/.claude:/home/node/.claude`, `${HOME}/.config/gemini:/home/node/.config/gemini`
  - 환경 변수:
    - `PYTHONUNBUFFERED=1`
    - `CLAUDE_PATH=claude`, `DROID_PATH=droid`, `GEMINI_PATH=gemini`
    - `FACTORY_API_KEY` (선택)
    - `DROID_SKIP_PERMISSIONS_UNSAFE=1`
    - `APP_LOGIN_PASSWORD`, `APP_JWT_SECRET`, `APP_JWT_TTL`, `APP_PUBLIC_WS_URL`
    - `FACTORY_AUTH_DIR`, `CLAUDE_AUTH_DIR`, `GEMINI_AUTH_DIR` (호스트 인증 폴더 위치)
  - 컨테이너 사용자: `${UID:-1000}:${GID:-1000}` (파일 권한 문제 방지), `stdin_open`/`tty` 활성화

### 주의사항

- **Claude**: 호스트에서 `claude auth login` 완료 후 필요 시 `docker-compose.yml`에 `~/.claude` 볼륨을 직접 추가
- **Gemini**: OAuth 인증만 지원 (`gemini auth login` 후 `~/.config/gemini` 공유 필요 시 직접 추가)
- **Droid**: `FACTORY_API_KEY` 환경 변수 또는 `~/.factory/config.json` 커스텀 모델 설정 마운트 필수
- **간단 로그인(선택)**: `.env`의 `APP_LOGIN_PASSWORD`에 값을 지정하면 접속 시 비밀번호 입력 모달이 표시됩니다. JWT 서명 키(`APP_JWT_SECRET`)와 만료 시간(`APP_JWT_TTL`, 초 단위)을 함께 설정하면 브라우저가 토큰을 저장하고 만료 1분 전에 자동 갱신해 세션을 유지합니다. 비밀번호를 비워두면 인증 없이 사용 가능합니다.
- 컨테이너는 `chatbot_workspace/CLAUDE.md`를 읽어서 성인 콘텐츠 지침 적용
- 사용하지 않는 AI CLI는 설치하지 않아도 됨 (최소 1개 이상 필요)

## Docker 아키텍처

이 프로젝트는 **하이브리드 Docker 전략**을 사용합니다: 실행 환경은 컨테이너에 포함하고, 데이터와 코드는 호스트에서 마운트합니다.

### 컨테이너에 포함된 것 (Docker Image)

다음 항목들은 Docker 이미지에 빌드되어 포함됩니다:

**시스템 및 런타임**
- Node.js 22 (Claude Code CLI, Gemini CLI 실행용)
- Python 3.11 (WebSocket 서버 실행용)
- 시스템 패키지 (`curl`, `git`, `procps` 등)

**AI CLI 도구**
- Claude Code CLI (`@anthropic-ai/claude-code`)
- Gemini CLI (`@google/gemini-cli`)
- Droid CLI (Factory.ai)

**Python 의존성**
- websockets 12.0
- aiofiles 23.2.1

**애플리케이션 코드** (초기 빌드 시)
- `server/` (WebSocket 서버 및 핸들러)
- `web/` (프론트엔드 HTML/CSS/JS)
- `chatbot_workspace/CLAUDE.md` (챗봇 전용 지침)

### 호스트에서 마운트되는 것 (Volume Mounts)

다음 항목들은 컨테이너 실행 시 호스트에서 마운트됩니다:

```yaml
volumes:
  # AI CLI 인증 정보
  - ${HOME}/.claude:/home/node/.claude              # Claude OAuth 인증
  - ${HOME}/.factory:/home/node/.factory            # Droid OAuth 인증 (선택)
  - ${HOME}/.config/gemini:/home/node/.config/gemini # Gemini OAuth 인증 (선택)

  # 개발 중 코드 변경 실시간 반영
  - ./server:/app/server                            # 서버 코드
  - ./web:/app/web                                  # 웹 프론트엔드

  # 챗봇 데이터 및 설정
  - ./chatbot_workspace:/app/chatbot_workspace      # 페르소나 데이터, CLAUDE.md
```

**마운트 이유**:
1. **인증 정보**: AI CLI 인증은 호스트에서 수행하고 컨테이너와 공유
2. **라이브 개발**: 코드 수정 시 컨테이너 재빌드 불필요
3. **데이터 영속성**: 페르소나 데이터가 컨테이너 삭제 시에도 보존됨

### Workspace 격리 (CLAUDE.md)

이 프로젝트는 **개발용 지침**과 **챗봇용 지침**을 분리합니다:

#### 개발용 지침 (레포 루트)
- **위치**: `/home/ginis/persona_chatbot/CLAUDE.md`
- **용도**: Claude Code가 코드 작업 시 참조
- **내용**: 프로젝트 아키텍처, 개발 가이드, 기술 스택
- **Docker에서**: ❌ **제외됨** (`.dockerignore`로 차단)

#### 챗봇용 지침 (chatbot_workspace)
- **위치**: `/home/ginis/persona_chatbot/chatbot_workspace/CLAUDE.md`
- **용도**: 챗봇 AI가 대화 시 참조
- **내용**: 성인 콘텐츠 규칙, 캐릭터 연기 원칙, 응답 형식
- **Docker에서**: ✅ **포함됨** (필수 파일)

#### 격리 메커니즘

```python
# server/handlers/claude_handler.py
self.chatbot_workspace = Path(__file__).parent.parent.parent / "chatbot_workspace"

args = [
    self.claude_path,
    "--setting-sources", "user,local",  # "project" 제외 (레포 루트 CLAUDE.md 무시)
    # ...
]

self.process = await asyncio.create_subprocess_exec(
    *args,
    cwd=str(self.chatbot_workspace)  # 작업 디렉토리를 chatbot_workspace로 설정
)
```

**동작 원리**:
1. `cwd=chatbot_workspace` → AI CLI가 `chatbot_workspace/` 에서 실행
2. `--setting-sources user,local` → `project` 레벨 설정 무시
3. 결과: `chatbot_workspace/CLAUDE.md`만 읽고, 레포 루트 `CLAUDE.md`는 무시

### .dockerignore를 통한 빌드 최적화

Docker 이미지 빌드 시 불필요한 파일을 제외하여 이미지 크기를 줄이고 보안을 강화합니다.

#### 제외되는 파일

```dockerignore
# 개발용 문서 (호스트에만 필요)
/CLAUDE.md                    # 개발용 지침 (챗봇용 아님!)
/AGENTS.md                    # 에이전트 설정
/.claude/                     # 개발 환경 설정
/README.md                    # 프로젝트 문서

# 소스 관리
.git                          # Git 히스토리 (불필요)
.gitignore

# 런타임 생성 파일
STORIES/                      # 대화 기록 (런타임 생성)
__pycache__/                  # Python 캐시
venv/                         # Python 가상환경
node_modules/                 # Node 의존성 (이미 설치됨)

# 개발 도구
.vscode/, .idea/              # IDE 설정
test_*.sh, test_*.py          # 테스트 스크립트
```

#### 포함되는 파일

```
✅ server/                     # WebSocket 서버 (필수)
✅ web/                        # 프론트엔드 (필수)
✅ chatbot_workspace/CLAUDE.md # 챗봇 지침 (필수)
✅ requirements.txt            # Python 의존성 목록
✅ docker-compose.yml          # Docker 설정
✅ Dockerfile.test             # Docker 빌드 스크립트
```

**효과**:
- 이미지 크기 감소 (수백 MB 절약)
- 빌드 속도 향상
- 개발용 지침이 프로덕션 컨테이너에 노출되지 않음

### 데이터 영속성 및 백업

#### 영속 데이터 위치

컨테이너가 삭제되어도 다음 데이터는 호스트에 보존됩니다:

1. **페르소나 데이터**: `./persona_data/` (git submodule)
   - 캐릭터, NPC, 세계관, 스토리 등

2. **챗봇 설정**: `./chatbot_workspace/`
   - CLAUDE.md (챗봇 지침)
   - 임시 작업 파일

3. **대화 기록**: `./STORIES/`
   - 마크다운 서사 파일

4. **AI 인증 정보**: `~/.claude/`, `~/.factory/`, `~/.config/gemini/`
   - OAuth 토큰 및 설정

#### 백업 전략

```bash
# 전체 페르소나 데이터 백업
cd persona_data
git add -A
git commit -m "Backup: $(date)"
git push

# 대화 기록 백업
tar -czf stories-backup-$(date +%Y%m%d).tar.gz STORIES/

# 챗봇 설정 백업
cp -r chatbot_workspace chatbot_workspace.backup
```

#### 컨테이너 재생성

컨테이너를 삭제하고 재생성해도 데이터는 유지됩니다:

```bash
# 컨테이너 삭제 (데이터는 호스트에 유지됨)
docker compose down

# 이미지 재빌드
docker compose build

# 컨테이너 재시작 (기존 데이터 자동 마운트)
docker compose up -d
```

### Docker vs 로컬 실행 비교

| 항목 | Docker | 로컬 실행 |
|------|--------|-----------|
| **환경 격리** | ✅ 완전 격리 | ❌ 호스트 환경 영향 받음 |
| **의존성 관리** | ✅ 이미지에 포함 | ❌ 수동 설치 필요 |
| **포트 충돌** | ✅ 컨테이너 내부 격리 | ⚠️ 호스트 포트 충돌 가능 |
| **배포** | ✅ 어디서나 동일 | ❌ 환경별 설정 필요 |
| **개발 속도** | ⚠️ 빌드 시간 필요 | ✅ 즉시 실행 |
| **디버깅** | ⚠️ 컨테이너 진입 필요 | ✅ 직접 디버깅 |
| **데이터 접근** | ✅ 볼륨 마운트로 동일 | ✅ 직접 접근 |

**권장 사용 시나리오**:
- **Docker**: 프로덕션 배포, 팀 협업, 환경 통일
- **로컬**: 빠른 개발, 디버깅, 프로토타이핑

## 기여

이슈 및 Pull Request를 환영합니다.

## 라이선스

MIT License

## 크레딧

- **AI 제공자**:
  - Claude Code CLI by Anthropic
  - Gemini CLI by Google
  - Droid CLI by Factory.ai
- WebSocket 라이브러리: websockets
- 비동기 파일 I/O: aiofiles

## 문의

이슈 트래커를 사용하거나 PR을 제출해주세요.

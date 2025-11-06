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
- Claude Code CLI (AI 대화 처리)

### Frontend
- HTML5 / CSS3 / Vanilla JavaScript
- WebSocket API (실시간 통신)
- VS Code 스타일 UI

## 설치 및 실행

### 1. 사전 요구사항
- Python 3.8 이상
- Claude Code CLI 설치 및 인증 완료
- Git (선택사항, Git 기능 사용 시)

```bash
# Claude Code 인증 확인
claude auth login
```

### 2. 설치

```bash
# 프로젝트 클론 또는 다운로드
cd persona_chatbot

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# STORIES 디렉토리 생성 (없는 경우)
mkdir -p STORIES
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
├── Dockerfile.test              # Docker 이미지 (테스트용)
├── docker-compose.test.yml      # Docker Compose 설정
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

Docker 컨테이너로 실행할 수 있습니다. 볼륨 마운트 방식으로 호스트의 Claude CLI 인증 정보를 사용합니다.

### Docker 실행 방법

```bash
# 컨테이너 빌드 및 실행
docker compose -f docker-compose.test.yml up -d

# 로그 확인
docker compose -f docker-compose.test.yml logs -f

# 컨테이너 중지
docker compose -f docker-compose.test.yml down
```

### Docker 구성

- **Dockerfile.test**: Node.js 22 + Python 3.11 + Claude Code CLI
- **docker-compose.test.yml**: 서비스 설정
  - 포트: 8765 (WebSocket), 9000 (HTTP)
  - 볼륨 마운트: `~/.claude` (인증 정보)
  - 사용자 권한: 호스트 UID/GID로 실행 (파일 권한 문제 방지)

### 주의사항

- 호스트에서 `claude auth login` 완료 필요
- `~/.claude` 디렉토리가 컨테이너와 공유됨
- 컨테이너는 `chatbot_workspace/CLAUDE.md`를 읽어서 성인 콘텐츠 지침 적용

## 기여

이슈 및 Pull Request를 환영합니다.

## 라이선스

MIT License

## 크레딧

- Claude Code by Anthropic
- WebSocket 라이브러리: websockets
- 비동기 파일 I/O: aiofiles

## 문의

이슈 트래커를 사용하거나 PR을 제출해주세요.

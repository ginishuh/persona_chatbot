# SQLite DB 마이그레이션 및 Export/Import 기능 설계서

**작성일**: 2025-11-12
**버전**: 1.2
**상태**: 적용 완료 (rooms/messages DB 전환, HTTP Export 활성)

---

## 📋 목차

1. [배경 및 문제점](#배경-및-문제점)
2. [목표](#목표)
3. [현재 구조 분석](#현재-구조-분석)
4. [새로운 구조 설계](#새로운-구조-설계)
5. [데이터베이스 스키마](#데이터베이스-스키마)
6. [Export/Import 기능](#exportimport-기능)
7. [구현 계획](#구현-계획)
8. [예상 작업량](#예상-작업량)
9. [고려사항 및 리스크](#고려사항-및-리스크)

---

## 배경 및 문제점

### 현재 문제점

#### 1. 데이터 휘발성
- **서버 재시작 시 모든 데이터 손실**
  - 채팅 히스토리가 메모리(`HistoryHandler`)에만 저장됨
  - 세션 정보가 `sessions` 딕셔너리(메모리)에만 존재
  - 서버 재시작하면 모든 대화 내역 사라짐

#### 2. 크로스 디바이스 동기화 불가
- localStorage는 브라우저별로 격리됨
- PC에서 시작한 대화를 모바일에서 이어갈 수 없음
- 다른 기기에서 접속하면 새로 시작해야 함

#### 3. 백업 및 복원 기능 부재
- 중요한 대화를 보관할 방법이 없음
- 데이터 이전/마이그레이션 불가
- 친구와 대화 공유 불가

---

## 목표

### 주요 목표

1. **데이터 영속성**: 서버 재시작해도 모든 데이터 유지
2. **크로스 디바이스**: 어떤 기기에서든 같은 대화 이어가기
3. **백업/복원**: Export/Import 기능으로 데이터 이식성 확보
4. **최소 변경**: 기존 코드 구조 최대한 유지

### 비목표 (Scope 외)

- 다중 사용자 지원 (현재는 단일 사용자 가정)
- 실시간 동기화 (WebSocket push)
- 클라우드 스토리지 연동

---

## 현재 구조 분석

### 데이터 저장 위치

| 데이터 | 현재 위치 | 휘발성 | 문제점 |
|--------|-----------|--------|--------|
| 채팅 히스토리 | `HistoryHandler` (메모리) | ✅ 휘발 | 서버 재시작 시 손실 |
| 세션 정보 | `sessions` dict (메모리) | ✅ 휘발 | 재연결 시 새 세션 |
| 채팅방 설정 | `sessions[key]['rooms']` (메모리) | ✅ 휘발 | 설정 유지 안 됨 |
| 토큰 사용량 | `TokenUsageHandler` (메모리) | ✅ 휘발 | 통계 추적 불가 |
| 세션 키 | localStorage (클라이언트) | ❌ 영구 | 브라우저별 격리 |
| 캐릭터/세계관 | `persona_data/` (파일) | ❌ 영구 | 템플릿만 저장 |

### 기존 흐름

```
1. 사용자 접속
   ↓
2. localStorage에서 session_key 로드
   ↓
3. 서버에 session_key 전송
   ↓
4. 서버: sessions[key]가 없으면 새로 생성 ⚠️ (재시작 시 항상 새로 생성)
   ↓
5. 채팅 → HistoryHandler에만 저장 (메모리)
   ↓
6. 서버 재시작 → 모든 데이터 손실
```

---

## 새로운 구조 설계

### 설계 원칙

1. **단일 진실 공급원 (Single Source of Truth)**: SQLite DB가 모든 데이터의 원본
2. **메모리 캐싱**: 성능을 위해 HistoryHandler는 캐시로 유지
3. **템플릿 분리**: persona_data는 재사용 가능한 템플릿만 보관
4. **명시적 백업**: 자동 저장 대신 사용자가 필요할 때 Export

### 데이터 계층 구조

```
┌─────────────────────────────────────┐
│        클라이언트 (Browser)          │
│  localStorage: session_key만         │
└─────────────────┬───────────────────┘
                  │ WebSocket
┌─────────────────▼───────────────────┐
│           서버 (Python)              │
│  ┌─────────────────────────────┐   │
│  │ HistoryHandler (메모리 캐시) │   │
│  └────────────┬────────────────┘   │
│               │ Read/Write          │
│  ┌────────────▼────────────────┐   │
│  │   SQLite DB (영구 저장소)   │   │
│  │  - messages                 │   │
│  │  - rooms                    │   │
│  │  - sessions                 │   │
│  │  - token_usage              │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      persona_data/ (파일)           │
│  - characters/ (템플릿)             │
│  - worlds/ (템플릿)                 │
│  - presets/ (템플릿)                │
└─────────────────────────────────────┘
         ▲
         │ Export (수동)
         │
    [JSON 파일]
```

### 디렉토리 구조 변경

#### 변경 전
```
persona_data/
├── characters/
├── worlds/
├── presets/
├── rooms/          ← 삭제 예정
└── stories/        ← 삭제 예정
```

#### 변경 후
```
persona_data/
├── characters/     ✅ 유지 (템플릿)
├── worlds/         ✅ 유지 (템플릿)
└── presets/        ✅ 유지 (템플릿)

data/
└── chatbot.db      🆕 SQLite DB (모든 실시간 데이터)
```

---

## 데이터베이스 스키마

### ERD

```
users (1) ──────< (N) sessions (1) ──────< (N) rooms
                                                   │
                                           (1) ────< (N) messages
sessions (1) ──────< (N) token_usage
```

### 테이블 정의

#### 1. users
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**용도**: 향후 다중 사용자 지원을 위한 확장성 (현재는 단일 사용자)

#### 2. sessions
```sql
CREATE TABLE sessions (
    session_key TEXT PRIMARY KEY,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**용도**:
- 클라이언트의 localStorage에 저장된 session_key와 매핑
- 서버 재시작 후에도 세션 복원 가능

#### 3. rooms
```sql
CREATE TABLE rooms (
    room_id TEXT PRIMARY KEY,
    session_key TEXT NOT NULL,
    title TEXT NOT NULL,
    context TEXT,  -- JSON: world, characters, narrator 등 전체 설정
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_key) REFERENCES sessions(session_key) ON DELETE CASCADE
);
```

**용도**:
- 채팅방 메타데이터 및 설정 저장
- context에 world, situation, characters, narrator 설정 등을 JSON으로 저장

**예시 context JSON**:
```json
{
  "world": "판타지 세계관...",
  "situation": "용사가 마왕성에 침입...",
  "user_character": "용사 히로...",
  "narrator_enabled": true,
  "narrator_mode": "active",
  "adult_level": "enhanced",
  "characters": [
    {"name": "성녀", "description": "..."},
    {"name": "엘프", "description": "..."}
  ]
}
```

-- 권장 제약/인덱스 보강
--   - CHECK(json_valid(context))
--   - INDEX rooms_session_key (session_key)

```

#### 4. messages
```sql
CREATE TABLE messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role in ('user','assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
);

CREATE INDEX idx_messages_room_id ON messages(room_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
```

**용도**:
- 모든 채팅 메시지 영구 저장
- 빠른 조회를 위한 인덱스

#### 5. token_usage
```sql
CREATE TABLE token_usage (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_key TEXT NOT NULL,
    room_id TEXT NOT NULL,
    provider TEXT NOT NULL,  -- 'claude', 'openai', 'gemini' 등
    token_info TEXT,  -- JSON: input_tokens, output_tokens, total_cost 등
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_key) REFERENCES sessions(session_key) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
);

CREATE INDEX idx_token_usage_session ON token_usage(session_key);
CREATE INDEX idx_token_usage_room ON token_usage(room_id);
```

**용도**:
- 토큰 사용량 추적 및 통계
- 비용 분석

---

## Export/Import 기능

### 전송 방식 결정(요약)
- 기본: HTTP 다운로드/업로드 엔드포인트 사용(대규모 안정성/브라우저 호환성). Export는 JSON 또는 ZIP.
- 폴백: 소용량은 WebSocket 단건 전송 허용.

### HTTP API(권장)

#### 1) Export 다운로드
- `GET /api/export`
- 인증: `Authorization: Bearer <access_token>` 또는 쿼리 `token`(임시 서명 토큰)
- 쿼리 파라미터(예시):
  - `scope=single|selected|full`
  - `room_id=...`(scope=single), `room_ids=room1,room2`(scope=selected)
  - `include=messages,context,token_usage`
  - `start=YYYY-MM-DD&end=YYYY-MM-DD`
  - `format=json|zip`(기본 `json`)
- 응답: `Content-Disposition: attachment; filename="backup_YYYYMMDD.json|zip"`

#### 2) Import 업로드(선택 단계)
- `POST /api/import`
- 인증: `Authorization: Bearer <access_token>`
- 본문: `application/json`(직접 JSON) 또는 `multipart/form-data`(파일 업로드)
- 옵션: `import_mode=new|merge`, `target_room_id`, `duplicate_policy=skip|add`

> 초기 단계에서는 Import는 WebSocket `import_data`로 유지하고, Export만 HTTP 다운로드를 제공해도 충분합니다.

### Export 레벨

#### 레벨 1: 단일 채팅방
- 현재 활성 채팅방만 내보내기
- 가장 빠르고 간단함

#### 레벨 2: 선택한 채팅방들
- 체크박스로 여러 채팅방 선택
- 선택적 백업

#### 레벨 3: 전체 데이터
- 모든 채팅방 + 세션 정보
- 완전한 백업

### Export 형식

#### 단일 채팅방 Export
```json
{
  "version": "1.0",
  "export_type": "single_room",
  "exported_at": "2025-11-12T10:30:00Z",
  "room": {
    "room_id": "fantasy_adventure_001",
    "title": "판타지 모험",
    "created_at": "2025-11-10T12:00:00Z",
    "context": {
      "world": "...",
      "situation": "...",
      "characters": [...]
    },
    "messages": [
      {
        "role": "user",
        "content": "안녕?",
        "timestamp": "2025-11-10T12:05:00Z"
      },
      {
        "role": "assistant",
        "content": "[김혜수]: 안녕하세요~",
        "timestamp": "2025-11-10T12:05:03Z"
      }
    ],
    "stats": {
      "message_count": 245,
      "token_usage": {
        "total_input": 12345,
        "total_output": 23456
      }
    }
  }
}
```

#### 전체 Export
```json
{
  "version": "1.0",
  "export_type": "full_backup",
  "exported_at": "2025-11-12T10:30:00Z",
  "user": {
    "session_key": "abc123...",
    "created_at": "2025-11-01T10:00:00Z"
  },
  "rooms": [
    { /* 채팅방 1 */ },
    { /* 채팅방 2 */ },
    { /* 채팅방 3 */ }
  ],
  "stats": {
    "total_rooms": 3,
    "total_messages": 1234,
    "total_tokens": 98765,
    "date_range": {
      "earliest": "2025-11-01",
      "latest": "2025-11-12"
    }
  }
}
```

### Export 옵션 UI

```
┌─────────────────────────────────────────┐
│          데이터 내보내기                │
├─────────────────────────────────────────┤
│ 내보낼 범위:                            │
│ ○ 현재 채팅방만                         │
│ ○ 선택한 채팅방들                       │
│   ☑ [판타지 모험] (245개 메시지)       │
│   ☐ [SF 스토리] (120개 메시지)         │
│   ☑ [로맨스] (89개 메시지)             │
│ ○ 전체 데이터 (모든 채팅방)            │
├─────────────────────────────────────────┤
│ 포함 항목:                              │
│ ☑ 메시지 내역                           │
│ ☑ 채팅방 설정 (context)                 │
│ ☑ 토큰 사용량 통계                      │
│ ☐ 세션 정보                             │
├─────────────────────────────────────────┤
│ 날짜 필터 (선택사항):                   │
│ [2025-11-01] ~ [2025-11-12]            │
│ ☐ 전체 기간                             │
├─────────────────────────────────────────┤
│ 파일명:                                 │
│ [backup_2025-11-12.json____________]    │
├─────────────────────────────────────────┤
│          [취소]       [내보내기]        │
└─────────────────────────────────────────┘
```

### Import 옵션 UI

```
┌─────────────────────────────────────────┐
│          데이터 가져오기                │
├─────────────────────────────────────────┤
│ 파일 선택:                              │
│ [fantasy_adventure.json          ] 찾기 │
│                                         │
│ 감지된 내용:                            │
│ • 형식: 단일 채팅방                     │
│ • 채팅방: "판타지 모험"                 │
│ • 메시지: 245개                         │
│ • 기간: 2025-11-10 ~ 2025-11-12        │
├─────────────────────────────────────────┤
│ 가져오기 방식:                          │
│ ○ 새 채팅방으로 생성                    │
│ ○ 기존 채팅방에 병합                    │
│   [판타지 모험 (기존)        ▼]        │
│                                         │
│ 중복 메시지 처리:                       │
│ ○ 건너뛰기 (중복 방지)                  │
│ ○ 모두 추가 (중복 허용)                 │
├─────────────────────────────────────────┤
│ 새 채팅방 이름 (새로 생성 시):          │
│ [판타지 모험 (imported)_____________]   │
├─────────────────────────────────────────┤
│          [취소]       [가져오기]        │
└─────────────────────────────────────────┘
```

### WebSocket API (소용량 폴백)

#### Export API
```javascript
// 요청
{
  "action": "export_data",
  "data": {
    "export_type": "single" | "selected" | "full",
    "room_ids": ["room1", "room2"],  // export_type이 "selected"일 때
    "include": {
      "messages": true,
      "context": true,
      "token_usage": true,
      "session_info": false
    },
    "date_range": {
      "start": "2025-11-01",
      "end": "2025-11-12"
    }
  }
}

// 응답
{
  "action": "export_data",
  "data": {
    "success": true,
    "json_data": { /* export된 JSON */ },
    "stats": {
      "rooms_exported": 3,
      "messages_exported": 1234,
      "file_size": "2.3MB"
    }
  }
}
```

#### Import API
```javascript
// 요청
{
  "action": "import_data",
  "data": {
    "import_mode": "new" | "merge",
    "target_room_id": "existing_room_id",  // merge일 때
    "duplicate_policy": "skip" | "add",
    "json_data": { /* import할 JSON */ }
  }
}

// 응답
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

---

## 구현 계획

### Phase 1: DB 기반 구조 구축 (완료)

#### 1.1 DB Handler 구현
- [ ] `server/handlers/db_handler.py` 생성
- [ ] aiosqlite 기반 비동기 DB 작업
- [ ] 스키마 초기화 및 마이그레이션(`PRAGMA foreign_keys=ON`, `PRAGMA user_version` 관리)
- [ ] CRUD 메서드 구현

#### 1.2 기존 Handler 연동
- [ ] `HistoryHandler` → DB 읽기/쓰기 추가
- [ ] `TokenUsageHandler` → DB 저장
- [ ] `websocket_server.py` → 세션/채팅방 DB 조회

#### 1.3 데이터 흐름 변경
```python
# 기존
user_message → HistoryHandler (메모리만)

# 변경 후
user_message → HistoryHandler (메모리 캐시)
             → DBHandler.save_message() (영구 저장)
```

#### 1.4 초기화 로직
```python
# 서버 시작 시
1. DB 연결
2. 스키마 확인/생성
3. 기존 세션 복원 (sessions 테이블에서 로드)
4. 각 채팅방의 최근 N개 메시지를 HistoryHandler로 로드
```

### Phase 2: Export/Import 기능 (진행 중)

#### 2.1 Export 구현(HTTP 기본)
- [ ] HTTP `GET /api/export` 추가(토큰 검증 포함)
- [ ] DB에서 데이터 조회 및 JSON/ZIP 스트리밍 응답
- [ ] 날짜 필터, 선택적 포함 옵션 처리
- [ ] 프론트엔드: Export UI에서 HTTP 다운로드 사용(WS 폴백 허용)

#### 2.2 Import 구현(WS 우선, HTTP 선택)
- [ ] WebSocket `import_data` 액션(초기)
- [ ] JSON 파싱 및 유효성 검사, 중복 검사/병합
- [ ] 프론트엔드: Import UI 추가(파일→JSON 읽어 WS로 전송)
- [ ] (선택) HTTP `POST /api/import` 추가 및 큰 파일 업로드 지원

#### 2.3 파일 다운로드/업로드
- [ ] 프론트엔드: JSON 파일 다운로드
- [ ] 프론트엔드: 파일 선택 및 업로드

### Phase 3: UI/UX 개선 + 라우팅 연계 (완료)
- [ ] History API 라우팅과 Export/Import 화면 연결(`/backup`)

#### 3.1 메뉴 추가
- [ ] 상단 메뉴바: "백업" 드롭다운
- [ ] 채팅방 목록: 우클릭 컨텍스트 메뉴

#### 3.2 피드백 및 진행상황
- [ ] Export/Import 진행률 표시
- [ ] 성공/실패 알림
- [ ] 에러 메시지 개선

### Phase 4: 테스트 및 문서화 (1일)

#### 4.1 테스트
- [ ] DB CRUD 단위 테스트
- [ ] Export/Import 통합 테스트
- [ ] 서버 재시작 후 복원 테스트
- [ ] 크로스 디바이스 시나리오 테스트

#### 4.2 문서화
- [ ] README 업데이트
- [ ] Export/Import 사용 가이드
- [ ] DB 스키마 문서
- [ ] 마이그레이션 가이드 (기존 사용자용)

### Phase 5: persona_data 정리(완료)

#### 5.1 디렉토리 정리
- [ ] `persona_data/rooms/` 제거(또는 아카이브)
- [ ] `persona_data/stories/` 제거(파일 기반 서사 폐기)
- [ ] `.gitignore` 업데이트(이미 `data/` 포함)

---

## DB 경로와 배치

- 기본 경로: `data/chatbot.db`
- 환경변수: `DB_PATH`(미설정 시 기본 경로 사용)
- 서버 시작 시 상위 디렉터리 자동 생성: `os.makedirs(Path(DB_PATH).parent, exist_ok=True)`
- Docker: `data/` 볼륨 마운트(백업/보존 용이)

#### 5.2 WorkspaceHandler 수정
- [ ] `list_rooms()`, `save_room()` 등 제거
- [ ] `list_stories()`, `save_story()` 등 제거 또는 Export로 대체

---

## 예상 작업량

| Phase | 작업 내용 | 상태 |
|-------|-----------|------|
| Phase 1 | DB 기반 구조 구축 | ✅ 완료 |
| Phase 2 | Export/Import 기능 | ⏳ Export 완료 / Import WS 유지(HTTP 예정) |
| Phase 3 | UI/UX 라우팅(History API) | ✅ 완료 |
| Phase 4 | 테스트 및 문서화 | ⏳ 진행 중 |
| Phase 5 | persona_data 정리(stories 제거) | ✅ 완료 |

---

## 고려사항 및 리스크

### 기술적 고려사항

#### 1. 성능
- **문제**: 메시지가 많아지면 DB 조회 느려질 수 있음
- **해결**:
  - 인덱스 추가 (room_id, timestamp)
  - HistoryHandler를 캐시로 활용 (최근 N개만 메모리에)
  - 페이지네이션 (무한 스크롤)

#### 2. 동시성
- **문제**: 같은 세션을 여러 디바이스에서 동시 사용 시 충돌
- **해결**:
  - SQLite의 WAL 모드 활성화
  - 낙관적 잠금 (timestamp 기반)
  - 충돌 발생 시 사용자에게 알림

#### 3. 마이그레이션
- **문제**: 기존 사용자의 메모리 데이터 손실
- **해결**:
  - 첫 DB 배포 시 마이그레이션 스크립트 제공
  - persona_data/stories/에서 과거 대화 Import 지원
  - 충분한 공지 기간

### 보안 고려사항

#### 1. SQL Injection
- **해결**: 모든 쿼리에 파라미터 바인딩 사용
```python
# 나쁜 예
cursor.execute(f"SELECT * FROM messages WHERE room_id = '{room_id}'")

# 좋은 예
cursor.execute("SELECT * FROM messages WHERE room_id = ?", (room_id,))
```

#### 2. Export 파일 보안
- **문제**: Export된 JSON에 민감한 대화 내용 포함
- **해결**:
  - 사용자에게 보안 경고 표시
  - 선택적 암호화 기능 (향후)
  - Export 파일 권한 설정 (600)

#### 3. 경로 탈출 (Path Traversal)
- **해결**:
  - room_id, filename 등 입력값 검증
  - 화이트리스트 기반 필터링

### 운영 고려사항

#### 1. DB 백업
- **방법**:
  - 정기적인 DB 파일 백업 (cron)
  - Export 기능으로 수동 백업
  - VPS 스냅샷 활용

#### 2. DB 크기 관리
- **문제**: 장기 사용 시 DB 크기 증가
- **해결**:
  - 오래된 메시지 아카이브 기능 (향후)
  - VACUUM 명령으로 DB 최적화
  - 모니터링 및 알림

#### 3. 버전 관리
- **문제**: DB 스키마 변경 시 호환성
- **해결**:
  - 스키마 버전 테이블 추가
  - 자동 마이그레이션 스크립트
  - 롤백 계획

---

## 의존성 추가

### requirements.txt
```
websockets==12.0
aiofiles==23.2.1
PyJWT==2.10.1
aiosqlite==0.19.0  # 🆕 추가
```

---

## 다음 단계

1. ✅ **이 문서 리뷰** (현재 단계)
2. ⬜ 리뷰 피드백 반영
3. ⬜ 브랜치 생성: `feat/sqlite-db-export-import`
4. ⬜ Phase 1 시작: DB Handler 구현
5. ⬜ 점진적 통합 및 테스트

---

## 참고 자료

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [aiosqlite GitHub](https://github.com/omnilib/aiosqlite)
- [현재 프로젝트 구조](../CLAUDE.md)
- [History Handler](../server/handlers/history_handler.py)
- [WebSocket Server](../server/websocket_server.py)

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.1 | 2025-11-12 | stories 제거, HTTP Export/Import 설계 및 DB 경로 명시 |
| 1.2 | 2025-11-12 | rooms/messages DB 전환 및 HTTP Export 적용 |
| 1.1 | 2025-11-12 | stories 제거, HTTP Export/Import 설계 및 DB 경로 명시 |
| 1.0 | 2025-11-12 | 초안 작성 |

---

**작성자**: Claude Code
**리뷰 요청**: @ginishuh

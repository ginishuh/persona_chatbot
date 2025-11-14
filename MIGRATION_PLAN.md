# 데이터베이스 마이그레이션 계획

## 목표
세션 격리를 완전하게 구현하여 데이터 유출 및 크로스 세션 삭제 문제 해결

## 현재 스키마 (v0)

```sql
-- rooms: PRIMARY KEY (session_key, room_id) ← 신규 복합 PK
-- messages: room_id만 있음 (session_key 없음) ← 문제!
-- token_usage: session_key, room_id 모두 있지만 FK 없음
```

## 마이그레이션 단계

### 버전 1: messages 테이블 세션 격리

**목표**: messages 테이블에 session_key 추가 및 복합 인덱스 생성

**작업:**
1. messages 테이블에 session_key 컬럼 추가 (NOT NULL)
2. 기존 데이터를 rooms와 조인하여 session_key 채우기
3. 고아 메시지(room이 없는)는 'legacy' session_key로 이동
4. 복합 인덱스 생성: `CREATE INDEX idx_messages_room_session ON messages(room_id, session_key)`

**마이그레이션 SQL:**
```sql
-- 1. 임시 새 테이블 생성
CREATE TABLE messages_new (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_key TEXT NOT NULL,
    room_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role in ('user','assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 기존 데이터 복사 (rooms와 조인하여 session_key 가져오기)
INSERT INTO messages_new (message_id, session_key, room_id, role, content, timestamp)
SELECT
    m.message_id,
    COALESCE(r.session_key, 'legacy') as session_key,
    m.room_id,
    m.role,
    m.content,
    m.timestamp
FROM messages m
LEFT JOIN rooms r ON m.room_id = r.room_id;

-- 3. 기존 테이블 삭제 및 새 테이블로 교체
DROP TABLE messages;
ALTER TABLE messages_new RENAME TO messages;

-- 4. 인덱스 재생성
CREATE INDEX idx_messages_room_session ON messages(room_id, session_key);
CREATE INDEX idx_messages_ts ON messages(timestamp);
```

**하위 호환성:**
- 기존 'legacy' session_key로 마이그레이션된 데이터는 계속 조회 가능
- 신규 데이터는 항상 session_key와 함께 저장

### 버전 2 (선택사항): token_usage 테이블 정규화

**목표**: token_usage에도 복합 FK 추가

**작업:**
1. room_id가 NULL인 경우도 있으므로 조건부 FK 적용
2. 복합 인덱스 최적화

## 롤백 계획

**v1 → v0 롤백 (긴급 복구):**
```sql
-- messages에서 session_key 컬럼만 제거
CREATE TABLE messages_rollback AS
SELECT message_id, room_id, role, content, timestamp
FROM messages;

DROP TABLE messages;
ALTER TABLE messages_rollback RENAME TO messages;

-- 인덱스 재생성
CREATE INDEX idx_messages_room ON messages(room_id);
CREATE INDEX idx_messages_ts ON messages(timestamp);
```

## 배포 전 체크리스트

- [ ] 프로덕션 DB 백업 (chatbot.db → chatbot.db.backup.YYYYMMDD)
- [ ] 마이그레이션 테스트 (빈 DB, 기존 데이터 있는 DB 각각)
- [ ] 롤백 스크립트 테스트
- [ ] 마이그레이션 후 CRUD 작동 확인
- [ ] Export API 세션 격리 확인 (다른 세션 데이터 조회 안 됨)
- [ ] delete_room 크로스 세션 삭제 안 됨 확인

## 코드 변경 사항

### db_handler.py
- `save_message()`: session_key 파라미터 추가
- `list_messages()`: session_key 필터링 추가
- `list_messages_range()`: session_key 필터링 추가
- `delete_room()`: messages 삭제 시 session_key 필터링

### chat.py
- `save_message()` 호출 시 session_key 전달

### server/http/server.py
- Export API에서 room 조회 시 session_key 전달
- JWT 토큰에서 session_key 추출하여 사용

## 테스트 시나리오

1. **세션 격리 테스트**: 두 세션에서 같은 room_id="default" 사용 시 메시지가 섞이지 않음
2. **Export API 보안 테스트**: 세션 A에서 세션 B의 room_id를 export 요청 시 접근 거부
3. **delete_room 격리 테스트**: 세션 A에서 "default" 삭제 시 세션 B의 "default"는 유지됨
4. **마이그레이션 테스트**: 기존 데이터가 'legacy' 세션으로 올바르게 이동되는지 확인

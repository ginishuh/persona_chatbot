# 통합 계획서 v2.1 (UI/라우팅 + DB/Export + 정리 작업)

**작성일**: 2025-11-13
**대상 브랜치/PR**: `feat/ui-redesign`
**상태 요약**: 문서와 구현 간 괴리를 해소하고, 남은 Blocker·후속 작업을 재정의합니다. 이미 추가 구현된 기능은 유지합니다.

---

## 1) 배경과 범위
- 기존 계획서(`docs/ui-redesign-plan.md`, `docs/db-migration-plan.md`)와 실제 구현 간 상태 불일치가 존재합니다.
- 본 문서는 현재 구현을 “사실상 기준선(Baseline)”으로 삼아 계획을 갱신합니다.
- 도커 구동 시 필요한 디렉토리는 컨테이너 시작 시 생성하는 방식을 채택합니다(레포에 빈 디렉토리 커밋하지 않음).

---

## 2) 현재 구현 기준선(Baseline)
- 레이아웃/라우팅
  - 데스크톱 3열 고정 + 모바일 패널 토글(History API 라우팅 + SPA fallback) 유지.
  - 라우팅은 "전용 화면" 전환이 아닌 모달/패널 제어 중심.
- 채팅방별 독립 설정
  - DB `rooms.context` JSON 컬럼 사용. 방 로드시 ContextHandler 자동 적용.
  - `set_context`/`get_context`는 `room_id`를 수용(호출 경로는 `room_load` 선행 + `get_context`).
- Export
  - HTTP `GET /api/export`(JSON/ZIP), `GET /api/export/stream`(NDJSON) 구현.
  - Markdown ZIP `/api/export/md` 구현(추가 기능 – 유지).
  - 프론트엔드 Export UI는 HTTP 다운로드로 연동.
- Import
  - WebSocket `import_data` 구현(HTTP Import 미구현 – 후속).
- 데이터/보안
  - DB 경로 기본값 `data/chatbot.db` (런타임 자동 생성). `.gitignore`에 `data/` 포함.
  - 로그인 환경에서 Export는 토큰 검증 수행.
- Stories
  - 기능 비활성화 플래그(`STORIES_ENABLED=false`) 적용. 버튼은 노출되나 동작은 막음.

---

## 3) 결정 사항(Design Decisions)
- "이미 구현된 추가 기능"(NDJSON 스트리밍, Markdown ZIP Export 등)은 유지합니다.
- 데이터 디렉토리(`data/` 또는 `DB_PATH`)는 “도커 컨테이너 시작 시” 및 서버 런타임에서 자동 생성합니다.
- 라우팅 계약은 현 구현을 기준으로 문서화합니다.
  - `room_load(room_id)`로 컨텍스트를 세팅한 후 `get_context()`는 현재 컨텍스트 스냅샷을 반환.
- Stories UI는 기능 비활성화 시 렌더 자체를 숨깁니다(알림 대신 비표시 – 접근성/혼란 방지).

---

## 4) 해야 할 일(우선순위 재정리)

### 🔴 Blocker (이번 PR 내 처리 권장)
- [ ] 레거시 디렉토리 제거 정리(레포)
  - [ ] `persona_data/rooms/` 제거(또는 아카이브 디렉토리로 이동 후 .gitignore)
  - [ ] `persona_data/stories/` 제거(파일 기반 서사 폐기)
  - [ ] 루트 `STORIES/` 제거
- [ ] Stories UI 숨김 처리
  - [ ] `STORIES_ENABLED === false`일 때 관련 버튼/섹션을 렌더하지 않음(알림 제거)
  - [ ] 문서/툴팁에서 Stories 기능 폐기 안내
- [ ] 계획서 상태 동기화(본 문서 기준 반영)
  - [ ] 기존 문서 상의 미완료 항목 중 실제 완료된 항목(채팅방별 설정, HTTP Export)을 완료로 표기

### 🟡 High (후속 PR 1순위)
- [ ] HTTP Import 엔드포인트 추가: `POST /api/import` (대용량 파일 고려, 스트리밍 파서)
- [ ] 테스트 커버리지 보강
  - [ ] DBHandler CRUD 단위 테스트
  - [ ] `/api/export` JSON/ZIP, `/api/export/stream` NDJSON 통합 테스트(로그인 On/Off)
  - [ ] WS `import_data` 최소 시나리오
  - [ ] 라우팅/SPA fallback 스모크
- [ ] 모바일 UX 개선(기획 그대로 유지)
  - [ ] 패널 전환 애니메이션 보강(부드러운 easing)
  - [ ] 스와이프 제스처(좌/우 패널 열고 닫기)
  - [ ] 터치 타겟 최소 44x44px 유지 점검

### 🟢 Medium (중기)
- [ ] A11y 보강(ARIA 라벨, 포커스 트랩 커버리지/테스트)
- [ ] UI 컴포넌트 리팩토링(템플릿/헬퍼로 분리)

### ⚪ Low (선택)
- [ ] 다크 모드 토글(localStorage)
- [ ] 토스트/스낵바 알림 체계

---

## 5) API/계약 정리(최신)

### 라우팅(History API)
- `/` → 채팅방 목록 모달 열기.
- `/rooms/:roomId` → 방 전환: `room_load(room_id)` → 컨텍스트/히스토리 반영.
- `/rooms/:roomId/settings` → 설정 모달 열기 후 `get_context()`로 스냅샷 로드.
- `/rooms/:roomId/history` → 모바일: 우측 패널 오버레이, 데스크톱: 3열 유지.
- `/backup` → 백업 모달/화면.

### WebSocket 액션(발췌)
- `room_load(room_id)` → DB에서 컨텍스트/메시지 로드, ContextHandler 반영.
- `set_context({... , room_id?})` → 주어진 room_id로 DB 저장(없으면 전역 유지).
- `get_context({room_id?})` → room_id 지정 시 DB→ContextHandler→스냅샷, 미지정 시 현재 컨텍스트 반환.
- `import_data({...})` → WS 기반 Import(초기 버전).

### HTTP Export
- `GET /api/export` → JSON 또는 `?format=zip`
- `GET /api/export/stream` → `application/x-ndjson`
- `GET /api/export/md` → Markdown ZIP(추가 기능)
- 공통 쿼리: `scope=single|selected|full`, `room_id`, `room_ids`, `include=messages,context,token_usage`, `start`, `end`, (로그인 시) `token`

---

## 6) 데이터/배포 전략
- DB 기본 경로: `data/chatbot.db`(서버 런타임에서 자동 생성).
- Docker
  - Compose에서 `data/`를 볼륨으로 마운트(호스트 보존).
  - 컨테이너 시작 시(ENTRYPOINT/CMD) 경로 존재 확인 및 생성(필요 시 `mkdir -p`).
  - `.env`의 `DB_PATH`로 외부 경로 지정 가능.

---

## 7) 마이그레이션/정리 가이드
- 레포 정리
  - `persona_data/rooms`, `persona_data/stories`, 루트 `STORIES` 제거.
- 사용자 환경
  - 기존 파일 기반 스토리 사용자는 Export(HTTP)로 백업 후 폐기 안내.
  - 향후 Import는 WS(현행) 또는 HTTP(추가 예정)로 대체.

---

## 8) 테스트 전략(제안)
- 단위: DBHandler CRUD, ContextHandler load_from_dict/프롬프트 영향, HTTP 핸들러 파라미터 파싱.
- 통합: Export(JSON/ZIP/NDJSON) 경로/인증/필터링, 라우팅 fallback, WS import_data round-trip.
- 스모크: `scripts/ws_chat_test.py`로 3 Provider 스트림 + 라우팅 스모크.

---

## 9) 완료 기준(AC)
- Blocker 항목 처리 후:
  - 레포에 `persona_data/rooms`, `persona_data/stories`, `STORIES`가 존재하지 않는다.
  - Stories UI가 비활성화 상태에서 렌더되지 않는다.
  - 기존 문서와 본 문서의 상태가 일치한다.
- 후속 PR:
  - HTTP Import 엔드포인트 동작 및 테스트 통과.
  - Export/Import/DB 테스트 추가로 기본 커버리지 목표 충족(예: 라인 40%+).

---

## 10) 변경 이력
- v2.1 (2025-11-13): 실제 구현 기준으로 통합 계획서 신규 작성. 추가 구현 기능 유지 방침 명시. Blocker/후속 작업 재정의.

**작성자**: 팀
**리뷰 요청**: @ginishuh

# UI/UX 재설계 계획서

**작성일**: 2025-11-12
**최종 수정**: 2025-11-13
**버전**: 2.0 (하이브리드 방식)
**상태**: 부분 완료 (데스크톱 3열 + 모바일 패널 토글 + History API 라우팅)

---

## ⚠️ 중요 변경사항 (v2.0)

**초기 계획(v1.x)**: 모바일 우선 단일 화면 흐름
**실제 구현(v2.0)**: **하이브리드 방식**
- **데스크톱 (>900px)**: 3열 고정 레이아웃 유지
- **태블릿/모바일 (≤900px)**: 패널 숨김/토글 + 모달 방식
- **라우팅**: History API 사용 (모달/패널 제어)

이 문서는 **실제 구현된 하이브리드 방식**을 반영하여 재작성되었습니다.

---

## 📋 목차

1. [구현 현황](#구현-현황)
2. [실제 UI 구조](#실제-ui-구조)
3. [라우팅 전략](#라우팅-전략)
4. [반응형 브레이크포인트](#반응형-브레이크포인트)
5. [화면별 동작](#화면별-동작)
6. [설정 구조](#설정-구조)
7. [Export/Import 전송 방식](#exportimport-전송-방식)
8. [남은 작업](#남은-작업)
9. [원래 계획 대비 변경사항](#원래-계획-대비-변경사항)

---

## 구현 현황

### ✅ 완료된 항목

1. **History API 라우팅**
   - `navigate()`, `renderCurrentScreenFrom()`, `popstate` 리스너 구현
   - URL 경로: `/`, `/rooms/:id`, `/rooms/:id/settings`, `/rooms/:id/history`, `/backup`
   - 브라우저 뒤로가기/앞으로가기 지원

2. **반응형 레이아웃**
   - 3개 브레이크포인트: 1200px, 900px, 600px
   - 데스크톱: 3열 고정 (캐릭터 + 채팅 + 서사/채팅방)
   - 모바일: 패널 토글 (햄버거 메뉴, 서사기록 버튼)

3. **모달 시스템**
   - 설정 모달 (`settingsModal`)
   - 참여자 관리 모달 (`participantsModal`)
   - 백업/Export 모달 (`backupModal`)
   - 채팅방 목록 모달 (`roomsModal`)
   - 캐릭터 편집 모달 (`characterEditorModal`)

4. **채팅방 시스템**
   - 다중 채팅방 지원 (우측 패널에서 목록/검색)
   - 채팅방별 히스토리 관리
   - 채팅방 추가/삭제/저장 기능

5. **Stories 기능 제거**
   - `STORIES_ENABLED = false`로 비활성화
   - 관련 UI 숨김 처리

### ⬜ 미완료/개선 필요

1. **채팅방별 독립 설정**
   - 현재: 전역 설정만 존재
   - 목표: 각 채팅방이 독립적인 world, characters, narrator 설정 보유
   - DB 스키마: `rooms.context` JSON 컬럼 활용 필요

2. **Export HTTP 엔드포인트**
   - 현재: WebSocket 기반 export만 존재
   - 목표: `/api/export` HTTP 엔드포인트 구현 (대용량 지원)

3. **모바일 UX 개선**
   - 패널 전환 애니메이션
   - 스와이프 제스처 지원
   - 터치 영역 최적화 (44x44px 최소)

4. **접근성 (A11y)**
   - ARIA 라벨 추가 (부분 완료)
   - 키보드 네비게이션 개선
   - 포커스 트랩 완성

---

## 실제 UI 구조

### 데스크톱 레이아웃 (>900px)

```
┌──────────────────────────────────────────────────────────────┐
│ ☰  [Logo] Persona Chat    [👥][⚙️][🗑️][♻️] [토큰] [상태]  │  ← 헤더
├──────────┬───────────────────────────┬──────────────────────┤
│          │                           │                      │
│ 👥 캐릭터│       💬 채팅 영역         │   💬 채팅방 목록     │
│          │                           │   📜 서사 기록       │
│ [나의    │  [진행자]: 상황 설명...   │                      │
│  캐릭터] │  [캐릭터A]: 대화...       │  ┌─────────────┐    │
│          │  [사용자]: 입력...        │  │ Room 1      │    │
│ [참여자] │                           │  │ Room 2      │    │
│ • 캐릭터A│  ─────────────────────    │  │ Room 3      │    │
│ • 캐릭터B│  [메시지 입력____] [전송] │  └─────────────┘    │
│          │                           │                      │
│ [+ 추가] │                           │  [서사 저장/불러오기]│
│          │                           │                      │
└──────────┴───────────────────────────┴──────────────────────┘
```

**특징**:
- 3열 고정 레이아웃
- 모든 패널 동시 표시
- 넓은 화면 활용

### 태블릿/모바일 레이아웃 (≤900px)

```
데스크톱 3열 → 패널 숨김/토글

┌────────────────────────────┐
│ ☰  Persona Chat  📜  ⋮     │  ← 헤더 (간소화)
├────────────────────────────┤
│                            │
│     💬 채팅 영역           │  ← 메인 (Center Panel만 표시)
│                            │
│  [진행자]: 상황 설명...    │
│  [캐릭터A]: 대화...        │
│  [사용자]: 입력...         │
│                            │
│  ────────────────────      │
│  [메시지 입력____] [전송]  │
│                            │
└────────────────────────────┘

☰ 클릭 → Left Panel 오버레이
📜 클릭 → Right Panel 오버레이
⋮ 클릭 → 더보기 메뉴 드롭다운
```

**특징**:
- 메인(채팅)만 표시, 좌우 패널 숨김
- 햄버거 메뉴/서사기록 버튼으로 패널 토글
- 오버레이 방식 (배경 어둡게)

---

## 라우팅 전략

### 실제 구현: History API + 모달/패널 제어

**핵심 개념**: 3열 메인 레이아웃은 유지하되, URL 변경 시 **모달/패널만 제어**

#### URL 매핑

| URL | 동작 | 구현 위치 |
|-----|------|-----------|
| `/` | 채팅방 목록 모달 열기 | `openRoomsModal()` |
| `/rooms/:roomId` | 채팅방 전환 (메인 레이아웃 유지) | `room_load` action |
| `/rooms/:roomId/settings` | 설정 모달 열기 | `settingsModal.classList.remove('hidden')` |
| `/rooms/:roomId/history` | 모바일: 우측 패널 열기 / 데스크톱: 유지 | `openMobilePanel('right')` |
| `/backup` | 백업/Export 모달 열기 | `openBackupModal()` |

#### 핵심 함수

```javascript
// app.js:236-296
function renderCurrentScreenFrom(pathname) {
    const { view, params } = parsePathname(pathname);
    hideScreen();  // 전용 화면 숨김 (3열 유지)

    if (view === 'room-list') {
        openRoomsModal();
    } else if (view === 'room-detail') {
        currentRoom = params[0];
        sendMessage({ action: 'room_load', room_id: currentRoom });
    } else if (view === 'room-settings') {
        openSettingsModal();
        sendMessage({ action: 'get_context' });
    }
    // ...
}

function navigate(path) {
    window.history.pushState({ path }, '', path);
    renderCurrentScreenFrom(location.pathname);
}

window.addEventListener('popstate', () => {
    renderCurrentScreenFrom(location.pathname);
});
```

#### 특징

✅ **장점**:
- 깔끔한 URL (`/rooms/fantasy_001`)
- 브라우저 뒤로가기/앞으로가기 지원
- 북마크/공유 가능
- 데스크톱 3열 레이아웃 유지 (기존 사용성)
- 모바일에서 패널 제어로 반응형 대응

⚠️ **주의사항**:
- SPA fallback 필요: `server/http/server.py`의 `CustomHandler.do_GET()`에서 `/api/*` 제외하고 `index.html` 반환
- 모달 상태와 URL 동기화 필요 (닫기 버튼 클릭 시 `navigate()` 호출)

---

## 반응형 브레이크포인트

### CSS 미디어 쿼리 (`style.css`)

```css
/* 기본: 데스크톱 (>1200px) */
.left-panel { width: 340px; }
.right-panel { width: 360px; }

/* 중형 데스크톱 (≤1200px) */
@media (max-width: 1200px) {
    .left-panel { width: 280px; }
    .right-panel { width: 320px; }
}

/* 태블릿/소형 데스크톱 (≤900px) */
@media (max-width: 900px) {
    .hamburger-btn { display: flex; }      /* 햄버거 메뉴 표시 */
    .narrative-menu-btn { display: block; } /* 서사기록 버튼 표시 */
    .more-menu-btn { display: block; }      /* 더보기 버튼 표시 */
    .header-actions { display: none; }      /* 헤더 액션 숨김 */

    .left-panel, .right-panel {
        /* 패널 숨김, JavaScript로 오버레이 토글 */
    }
}

/* 모바일 (≤600px) */
@media (max-width: 600px) {
    /* 추가 최적화 */
}
```

### 브레이크포인트 전략

| 화면 크기 | 레이아웃 | 네비게이션 |
|-----------|---------|-----------|
| **>1200px** | 3열 고정 (340 + auto + 360) | 헤더 전체 버튼 표시 |
| **901-1200px** | 3열 고정 (280 + auto + 320) | 헤더 전체 버튼 표시 |
| **601-900px** | 채팅만 (패널 오버레이) | 햄버거/서사/더보기 버튼 |
| **≤600px** | 채팅만 (패널 오버레이) | 햄버거/서사/더보기 버튼 |

---

## 화면별 동작

### 1. 채팅방 목록 (`/` 또는 채팅방 목록 모달)

**진입 방법**:
- URL: `/`
- 우측 패널의 채팅방 목록에서 검색/선택

**UI 구성**:
```
┌─────────────────────────────┐
│ 💬 채팅방 목록        [✕]   │  ← 모달 헤더
├─────────────────────────────┤
│ [검색____]                  │  ← 검색 입력
│                             │
│ ┌─────────────────────────┐ │
│ │ 🏰 판타지 모험           │ │
│ │ 마지막 메시지...         │ │
│ └─────────────────────────┘ │
│ ┌─────────────────────────┐ │
│ │ 💕 로맨스 스토리         │ │
│ │ 마지막 메시지...         │ │
│ └─────────────────────────┘ │
│                             │
│ [+ 새 채팅방]               │  ← 추가 버튼
└─────────────────────────────┘
```

**동작**:
- 채팅방 클릭 → `navigate('/rooms/:roomId')`
- `room_load` WebSocket 메시지 전송
- 모달 닫힘, 메인 화면에서 해당 채팅방 표시

---

### 2. 채팅방 화면 (`/rooms/:roomId`)

**진입 방법**:
- URL: `/rooms/:roomId`
- 채팅방 목록에서 선택
- `roomSelect` 드롭다운에서 선택

**UI 구성**:
- 데스크톱: 3열 모두 표시
- 모바일: 채팅(Center Panel)만 표시

**동작**:
- `currentRoom` 전역 변수 업데이트
- `room_load` 액션으로 서버에서 히스토리/컨텍스트 로드
- 세션 리셋 (`reset_sessions`)

---

### 3. 설정 화면 (`/rooms/:roomId/settings`)

**진입 방법**:
- URL: `/rooms/:roomId/settings`
- 헤더의 ⚙️ 설정 버튼
- 더보기 메뉴(⋮)의 "설정"

**UI 구성**:
- 모달 (`settingsModal`)
- 섹션: 세계관, 상황, 진행자, AI 제공자, 맥락 길이, 성인 수위 등

**동작**:
- 모달 열림
- `get_context` 액션으로 현재 설정 로드
- "설정 적용" 버튼 → `set_context` 액션

**⚠️ 현재 한계**:
- 전역 설정만 존재 (채팅방별 독립 설정 미구현)
- 채팅방 전환 시 설정 자동 로드 안 됨

---

### 4. 히스토리 화면 (`/rooms/:roomId/history`)

**진입 방법**:
- URL: `/rooms/:roomId/history`
- 우측 패널의 서사 기록 영역

**UI 구성**:
- 데스크톱: 우측 패널 항상 표시
- 모바일: 📜 버튼으로 우측 패널 오버레이

**동작**:
- 마크다운 렌더링된 대화 내역 표시
- 서사 저장/불러오기 버튼

---

### 5. 백업/Export 화면 (`/backup`)

**진입 방법**:
- URL: `/backup`
- 더보기 메뉴의 "백업" 항목

**UI 구성**:
- 모달 (`backupModal`)
- 옵션: 범위(현재 방/선택한 방/전체), 포함 항목, 기간, 형식

**동작**:
- 다운로드 버튼 → `/api/export` HTTP 엔드포인트 호출 (TODO)
- 현재는 WebSocket 기반 export (소규모만 지원)

---

## 설정 구조

### 현재 상태: 전역 설정

```javascript
// app.js - 전역 변수
const contextHandler = {
    world: "",
    situation: "",
    user_character: "",
    characters: [],
    narrator_enabled: true,
    narrator_mode: "moderate",
    // ...
};
```

**문제점**:
- 모든 채팅방이 동일한 설정 공유
- 채팅방 전환 시 설정이 자동으로 변경되지 않음
- 채팅방마다 다른 세계관/캐릭터를 사용하려면 매번 수동 변경 필요

---

### 목표: 채팅방별 독립 설정

#### DB 스키마 (이미 존재)

```sql
-- server/handlers/db_handler.py
CREATE TABLE rooms (
    room_id TEXT PRIMARY KEY,
    session_key TEXT NOT NULL,
    title TEXT NOT NULL,
    context TEXT,  -- ← JSON으로 채팅방별 설정 저장
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### Context JSON 구조

```json
{
  "world": "판타지 세계관...",
  "situation": "용사가 마왕성에 침입...",
  "user_character": "용사 히로, 17세...",
  "narrator_enabled": true,
  "narrator_mode": "active",
  "narrator_description": "상황을 생생하게 묘사하는 진행자",
  "narrator_drive": "direct",
  "adult_level": "enhanced",
  "output_level": "more",
  "narrative_separation": true,
  "choice_policy": "off",
  "ai_provider": "claude",
  "characters": [
    { "name": "성녀", "gender": "여성", "age": "20대", "description": "..." },
    { "name": "엘프", "gender": "여성", "age": "외형 20대", "description": "..." }
  ]
}
```

#### 구현 필요 사항

1. **서버 측** (`server/ws/actions/context.py`):
   - `set_context` → `set_room_context` (room_id 파라미터 추가)
   - `get_context` → `get_room_context` (room_id별 로드)
   - DB `rooms.context` 컬럼에 JSON 저장/로드

2. **클라이언트 측** (`web/app.js`):
   - 채팅방 전환 시 자동으로 해당 채팅방 설정 로드
   - 설정 모달: 현재 채팅방 설정만 표시/수정
   - `roomContextCache` 객체로 클라이언트 측 캐싱

---

## Export/Import 전송 방식

### 현재 구현: WebSocket 기반

```javascript
// app.js
ws.send(JSON.stringify({
    action: "export_data",
    scope: "single",  // single, selected, full
    room_ids: [currentRoom],
    include: { messages: true, context: true },
    format: "json"
}));
```

**장점**: 구현 단순, 실시간 피드백
**단점**: 대용량 데이터 처리 어려움 (프록시 타임아웃, 메모리 제한)

---

### 목표: HTTP 다운로드 엔드포인트

#### 엔드포인트 설계

```
GET /api/export?
    scope=single|selected|full
    &room_ids=room1,room2
    &include=messages,context,token_usage
    &start=2025-01-01T00:00:00Z
    &end=2025-12-31T23:59:59Z
    &format=json|zip|ndjson
    &token=<session_token>
```

#### 응답 타입

| Format | Content-Type | 설명 |
|--------|-------------|------|
| `json` | `application/json` | 단일 JSON 객체 |
| `zip` | `application/zip` | ZIP 압축 (rooms/*.json) |
| `ndjson` | `application/x-ndjson` | 스트리밍 (큰 데이터) |

#### 구현 위치

- 서버: `server/http/server.py` → `do_GET()`에 `/api/export` 핸들러 추가
- 클라이언트: `web/app.js` → 백업 모달에서 다운로드 링크 생성

```javascript
// 예시
const url = `/api/export?scope=single&room_ids=${currentRoom}&format=json&token=${sessionToken}`;
window.open(url, '_blank');  // 또는 fetch + Blob 다운로드
```

---

## 남은 작업

### 우선순위 높음 🔴

1. **채팅방별 독립 설정 구현**
   - [ ] 서버: `set_room_context`, `get_room_context` 액션 추가
   - [ ] 서버: DB `rooms.context` 컬럼 활용
   - [ ] 클라이언트: 채팅방 전환 시 설정 자동 로드
   - [ ] 예상 작업량: 1-2일

2. **Export HTTP 엔드포인트**
   - [ ] 서버: `/api/export` GET 핸들러 구현
   - [ ] 서버: ZIP 압축 지원 (optional)
   - [ ] 클라이언트: 백업 모달에서 HTTP 다운로드 사용
   - [ ] 예상 작업량: 1일

### 우선순위 중간 🟡

3. **모바일 UX 개선**
   - [ ] 패널 전환 애니메이션 (CSS transition)
   - [ ] 스와이프 제스처 (Hammer.js 또는 순수 JS)
   - [ ] 터치 영역 검증 (최소 44x44px)
   - [ ] 예상 작업량: 1-2일

4. **접근성 (A11y) 완성**
   - [ ] 모든 버튼/입력에 ARIA 라벨
   - [ ] 키보드 네비게이션 (Tab, Enter, Esc)
   - [ ] 모달 포커스 트랩 완성
   - [ ] 스크린 리더 테스트
   - [ ] 예상 작업량: 1일

### 우선순위 낮음 🟢

5. **UI 컴포넌트 리팩토링**
   - [ ] 재사용 가능한 컴포넌트 함수 분리 (`RoomCard`, `MessageBubble` 등)
   - [ ] 템플릿 리터럴 → 별도 템플릿 파일 (optional)
   - [ ] 예상 작업량: 1-2일

6. **기타 개선사항**
   - [ ] 다크 모드 토글 (CSS 변수 + localStorage)
   - [ ] 알림 시스템 (toast 또는 snackbar)
   - [ ] 오류 처리 개선 (재연결, 타임아웃 표시)
   - [ ] 예상 작업량: 1-2일

---

## 원래 계획 대비 변경사항

### v1.x 계획 (모바일 우선 단일 화면)

```
채팅방 목록 → 채팅방 → 설정/히스토리
      ↓           ↓           ↓
   전체 화면   전체 화면   전체 화면
```

**특징**:
- ChatGPT/Claude 웹 앱과 유사한 UX
- 모바일 친화적
- 한 번에 하나의 화면만 표시

**문제점**:
- 데스크톱에서 화면 공간 낭비
- 기존 3열 레이아웃 사용자의 반발 가능성
- 대규모 리팩토링 필요 (6-9일)

---

### v2.0 구현 (하이브리드)

```
데스크톱: 캐릭터 | 채팅 | 서사/방목록  (3열 고정)
모바일:          채팅          (패널 토글)
```

**특징**:
- 데스크톱: 기존 사용성 유지
- 모바일: 패널 숨김/토글로 대응
- History API 라우팅으로 URL 지원

**장점**:
- ✅ 점진적 개선 (큰 리팩토링 불필요)
- ✅ 기존 사용자 경험 유지
- ✅ 모바일/태블릿 대응
- ✅ URL 북마크/공유 지원

**단점**:
- ⚠️ 모바일 UX가 완전히 최적화되지 않음
- ⚠️ 코드 복잡도 증가 (모달 + 패널 + 라우팅)

---

### 결정 이유

1. **사용자 기반**: 현재 주 사용자가 데스크톱 환경
2. **개발 속도**: 하이브리드 방식이 더 빠름 (부분 완료 상태)
3. **위험 감소**: 기존 기능 유지하며 점진적 개선
4. **유연성**: 향후 모바일 전용 뷰 추가 가능

---

## 다음 단계

### 즉시 착수 가능

1. ✅ **계획서 업데이트** (현재 작업)
2. ⬜ **채팅방별 독립 설정 구현** (우선순위 🔴)
   - 서버: `set_room_context`, `get_room_context`
   - 클라이언트: 자동 로드 로직
3. ⬜ **Export HTTP 엔드포인트** (우선순위 🔴)
   - `/api/export` 핸들러
   - 백업 모달 연동

### 중기 계획

4. ⬜ 모바일 UX 개선 (애니메이션, 제스처)
5. ⬜ 접근성 완성 (ARIA, 키보드)

### 장기 계획

6. ⬜ UI 컴포넌트 리팩토링
7. ⬜ 다크 모드, 알림 시스템 등

---

## 참고 자료

### 기술 문서

- [History API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/History_API)
- [Responsive Web Design Breakpoints](https://www.freecodecamp.org/news/css-media-queries-breakpoints-media-types-standard-resolutions-and-more/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### 참고 UI

- [ChatGPT](https://chat.openai.com) - 모바일 우선 접근
- [Claude](https://claude.ai) - 단일 화면 흐름
- [Discord](https://discord.com) - 하이브리드 (데스크톱 3열 + 모바일 패널)

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2025-11-12 | 초안 작성 (모바일 우선 단일 화면 계획) |
| 1.2 | 2025-11-12 | History API 라우팅, stories 제거, Export HTTP 추가 |
| 2.0 | 2025-11-13 | **하이브리드 방식**으로 전면 재작성 (실제 구현 반영) |

---

**작성자**: Claude Code
**리뷰 요청**: @ginishuh

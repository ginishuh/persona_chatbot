# web/modules - ES6 모듈 구조

## 개요

이 디렉토리는 `web/app.js` (4,624줄)의 모듈화 작업의 일환으로 생성되었습니다.
Issue #20의 계획에 따라 단일 파일을 23개의 ES6 모듈로 분리하는 작업을 진행 중입니다.

## 현재 진행 상황

### ✅ Phase 0: 준비 (완료)
- 브랜치 생성: `refactor/app-js-modularization`
- 디렉토리 구조 생성

### ✅ Phase 1: 핵심 인프라 (완료)
다음 모듈이 생성되었습니다:

#### `core/constants.js`
- 전역 상수 정의 (로컬스토리지 키, 설정 상수, 기능 플래그)
- **Export:** `AUTH_TOKEN_KEY`, `ROOMS_KEY`, `RETRY_ACTIONS`, `HISTORY_LIMIT_DEFAULT` 등

#### `core/state.js`
- 전역 상태 관리 및 접근자 함수
- **Export:** `ws`, `appConfig`, `authToken`, `rooms`, `currentRoom` 등
- **Getter/Setter:** `setAuthTokenState()`, `setRooms()`, `setCurrentRoom()` 등

#### `utils/utils.js`
- 순수 함수 유틸리티
- **Export:** `isTouchDevice()`, `escapeHtml()`, `slugify()`

### ✅ Phase 2: WebSocket 및 인증 (완료)

#### `websocket/connection.js`
- WebSocket 연결 관리
- **Export:** `buildWebSocketUrl()`, `loadAppConfig()`, `connect()`, `sendMessage()`
- **의존성:** `core/state.js`, `core/constants.js`

#### `auth/auth.js`
- 인증 및 토큰 관리
- **Export:** `setAuthToken()`, `clearAuthToken()`, `login()`, `register()`, `logout()`
- **의존성:** `core/state.js`, `core/constants.js`

### ✅ Phase 3: 라우팅 및 화면 관리 (완료)

#### `routing/router.js`
- History API 기반 SPA 라우팅
- **Export:** `parsePathname()`, `rememberPendingRoute()`, `resumePendingRoute()`, `renderCurrentScreenFrom()`, `navigate()`, `initRouter()`
- **의존성:** `core/state.js`, `websocket/connection.js`

#### `ui/screens.js`
- 전용 화면 컨테이너 관리
- **Export:** `showScreen()`, `hideScreen()`
- **의존성:** 없음 (DOM만 사용)

#### `ui/modals.js`
- 모달 관리 공통 유틸리티
- **Export:** `openModal()`, `closeModal()`, `toggleModal()`, `isModalOpen()`, `closeAllModals()`
- **의존성:** 없음 (DOM만 사용)

## 모듈 구조

```
web/modules/
├── core/
│   ├── constants.js    ✅ 완료
│   └── state.js        ✅ 완료
├── auth/
│   └── auth.js         ✅ 완료
├── websocket/
│   └── connection.js   ✅ 완료
├── routing/
│   └── router.js       ✅ 완료 (Phase 3)
├── ui/
│   ├── screens.js      ✅ 완료 (Phase 3)
│   └── modals.js       ✅ 완료 (Phase 3)
├── utils/
│   └── utils.js        ✅ 완료
├── rooms/              ⏳ 예정 (Phase 4)
├── chat/               ⏳ 예정 (Phase 4)
├── context/            ⏳ 예정 (Phase 5)
├── settings/           ⏳ 예정 (Phase 5)
├── files/              ⏳ 예정 (Phase 5)
├── admin/              ⏳ 예정 (Phase 6)
└── export/             ⏳ 예정 (Phase 6)
```

## 사용 예시

```javascript
// main.js에서 사용
import { AUTH_TOKEN_KEY, ROOMS_KEY } from './core/constants.js';
import { authToken, setRooms } from './core/state.js';
import { login, logout } from './auth/auth.js';
import { connect, sendMessage } from './websocket/connection.js';
import { isTouchDevice } from './utils/utils.js';

// 앱 초기화
async function initApp() {
    // 인증 확인
    if (authToken) {
        // 로그인 상태
    }

    // WebSocket 연결
    connect({
        onConnected: () => console.log('Connected!'),
        onMessage: (msg) => console.log('Message:', msg)
    });
}
```

## 다음 단계

### Phase 3: 라우팅 및 화면 관리
- `routing/router.js` - History API 기반 라우팅
- `ui/screens.js` - 화면 전환
- `ui/modals.js` - 모달 관리

### Phase 4: 채팅 기능
- `chat/chat.js` - 채팅 메시지 송수신
- `chat/characters.js` - 멀티 캐릭터 파싱
- `rooms/rooms.js` - 채팅방 관리

### Phase 5-7
자세한 계획은 [Issue #20 코멘트](https://github.com/ginishuh/persona_chatbot/issues/20#issuecomment-3544782509)를 참조하세요.

## 주의사항

⚠️ **현재 이 모듈들은 아직 `index.html`에 통합되지 않았습니다.**
기존 `web/app.js`가 계속 사용되고 있으며, 모듈화는 점진적으로 진행됩니다.

## 기여 가이드

1. 각 모듈은 단일 책임 원칙을 따릅니다
2. 순환 참조를 피하기 위해 의존성 방향을 명확히 합니다
3. JSDoc 주석을 추가하여 함수 시그니처를 문서화합니다
4. 순수 함수는 `utils/`에, 상태 관련 로직은 각 도메인 모듈에 배치합니다

## 참고 자료

- [Issue #20 - web/app.js 모듈화](https://github.com/ginishuh/persona_chatbot/issues/20)
- [상세 실행 계획](https://github.com/ginishuh/persona_chatbot/issues/20#issuecomment-3544782509)

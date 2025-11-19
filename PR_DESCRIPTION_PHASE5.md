Phase 5: 모듈 통합 (Module Integration)

이 PR은 `web/app.js`의 거대한 코드를 여러 모듈로 분리하고 통합하는 작업을 수행합니다.

### 주요 변경 사항
- `web/app.js`에서 인라인으로 정의된 함수들을 제거하고 모듈에서 import 하도록 변경했습니다.
- `auth`, `routing`, `ui`, `websocket`, `core`, `chat`, `rooms`, `utils` 모듈을 통합했습니다.
- `app.js`의 크기를 대폭 줄이고 유지보수성을 향상시켰습니다.

### 통합된 모듈
- `modules/auth/auth.js`: 인증 로직
- `modules/routing/router.js`: 라우팅 로직
- `modules/ui/screens.js`: 화면 전환 로직
- `modules/websocket/connection.js`: 웹소켓 연결 로직
- `modules/core/state.js`: 전역 상태 관리
- `modules/chat/chat.js`: 채팅 기능
- `modules/rooms/rooms.js`: 방 관리 기능
- `modules/utils/logger.js`: 로깅 유틸리티

### 테스트 방법
1. `web/app.js`가 정상적으로 로드되는지 확인합니다.
2. 로그인, 채팅방 생성, 메시지 전송, 설정 변경 등 주요 기능이 정상 작동하는지 확인합니다.

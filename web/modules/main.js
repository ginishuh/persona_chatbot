// modules/main.js
// Phase7 진입점: 기존 `app.js`를 모듈 방식으로 초기화하도록 래핑합니다.
// 이 파일은 `index.html`에서 로드되는 새로운 모듈 진입점입니다.

// 기존의 `app.js`는 이미 ES 모듈로 변환되어 있으므로 임포트하면
// 모듈 수준에서 초기화 코드가 실행됩니다.
// 모듈 진입점: 기존 `app.js`의 핵심 API를 중앙에서 전역에 할당합니다.
import '../app.js';
import {
	navigate,
	sendMessage,
    persistRooms,
    renderRoomsUI,
    sanitizeRoomName,
    collectRoomConfig
} from '../app.js';
// UI helpers는 직접 모듈에서 import
import { openModal, closeModal, toggleModal, isModalOpen } from './ui/modals.js';
import { showScreen, hideScreen } from './ui/screens.js';

// 기존에 `window.*`로 노출하던 함수들은 이제 ES 모듈을 통해 직접 임포트해서 사용하세요.
// 예: `import { navigate } from \'/modules/routing/router.js\'` 또는 필요한 모듈에서 직접 가져옵니다.
// 레거시 호환용 전역 바인딩은 제거했습니다.
console.debug('[modules/main] loaded (no global bindings)');

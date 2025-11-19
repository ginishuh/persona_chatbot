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
	downloadRoomMd,
	collectRoomConfig,
	openModal,
	closeModal,
	toggleModal,
	isModalOpen,
	showScreen,
	hideScreen
} from '../app.js';

// 중앙에서 한 곳에만 전역을 할당하도록 하여 `web/app.js`의 전역 노출을 줄입니다.
try {
	window.navigate = navigate;
	window.sendMessage = sendMessage;
	window.persistRooms = persistRooms;
	window.renderRoomsUI = renderRoomsUI;
	window.sanitizeRoomName = sanitizeRoomName;
	window.downloadRoomMd = downloadRoomMd;
	window.collectRoomConfig = collectRoomConfig;
	window.openModal = openModal;
	window.closeModal = closeModal;
	window.toggleModal = toggleModal;
	window.isModalOpen = isModalOpen;
	window.showScreen = showScreen;
	window.hideScreen = hideScreen;
} catch (e) {
	// 안전: 브라우저 환경이 아닐 경우 조용히 실패
	console.debug('[modules/main] global assignment skipped', e?.message || e);
}

console.debug('[modules/main] loaded');

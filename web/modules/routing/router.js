/**
 * History API 기반 SPA 라우팅
 * @module routing/router
 */

import { setPendingRoutePath, setCurrentRoom } from '../core/state.js';

// 상태를 app.js의 실제 값에서 읽도록 window 참조 사용
// app.js가 이미 isAuthenticated, appConfig를 관리하고 있으며,
// core/state.js와 동기화되지 않으므로 window를 통해 직접 접근
const getAppConfig = () => window.__appConfig || {};
const getIsAuthenticated = () => window.__isAuthenticated || false;
const getPendingRoutePath = () => window.__pendingRoutePath || null;
const getCurrentRoom = () => window.currentRoom;

/**
 * 라우트 테이블
 * 간단한 경로 → 화면 매핑
 */
const routeTable = [
    // 루트 경로는 매핑하지 않음 - ChatGPT 스타일 환영 화면만 표시
    { pattern: /^\/rooms$/, view: 'room-list' },
    { pattern: /^\/rooms\/([^\/]+)$/, view: 'room-detail' },
    { pattern: /^\/rooms\/([^\/]+)\/settings$/, view: 'room-settings' },
    { pattern: /^\/rooms\/([^\/]+)\/history$/, view: 'room-history' },
    { pattern: /^\/backup$/, view: 'backup' },
];

/**
 * 경로 문자열 파싱
 * @param {string} pathname
 * @returns {{view: string|null, params: string[]}}
 */
export function parsePathname(pathname) {
    for (const r of routeTable) {
        const m = pathname.match(r.pattern);
        if (m) {
            return { view: r.view, params: m.slice(1) };
        }
    }
    return { view: null, params: [] }; // 매치되지 않으면 아무 모달도 열지 않음
}

/**
 * 로그인 후 복원할 경로 저장
 * @param {string} pathname
 */
export function rememberPendingRoute(pathname) {
    const path = pathname || '/';
    setPendingRoutePath(path);
    window.__pendingRoutePath = path;
}

/**
 * 저장된 경로로 복원
 * @param {Function} renderFn - renderCurrentScreenFrom 함수
 */
export function resumePendingRoute(renderFn) {
    const pendingPath = getPendingRoutePath();
    if (!pendingPath) return;
    if (getAppConfig().login_required && !getIsAuthenticated()) {
        return;
    }
    setPendingRoutePath(null);
    window.__pendingRoutePath = null;
    try {
        renderFn(pendingPath);
    } catch (_) {}
}

/**
 * 현재 경로에 맞는 화면 렌더링
 * 외부 의존성을 콜백으로 받음
 *
 * @param {string} pathname
 * @param {object} handlers - 외부 핸들러들
 * @param {Function} handlers.showLoginModal
 * @param {Function} handlers.hideScreen
 * @param {Function} handlers.openRoomsModal
 * @param {Function} handlers.openBackupModal
 * @param {Function} handlers.renderBackupScreenView
 * @param {Function} handlers.persistRooms
 * @param {Function} handlers.renderRoomsUI
 * @param {Function} handlers.refreshRoomViews
 * @param {Function} handlers.enableFocusTrap
 * @param {Function} handlers.openMobilePanel
 * @param {Function} handlers.focusMainAfterRoute
 */
export function renderCurrentScreenFrom(pathname, handlers = {}) {
    const {
        showLoginModal = () => {},
        hideScreen = () => {},
        openRoomsModal = () => {},
        openBackupModal = () => {},
        renderBackupScreenView = () => {},
        persistRooms = () => {},
        renderRoomsUI = () => {},
        refreshRoomViews = () => {},
        enableFocusTrap = () => {},
        openMobilePanel = () => {},
        focusMainAfterRoute = () => {},
        sendMessage = () => {}
    } = handlers;

    // 인증 필요 시 로그인 모달 표시
    if (getAppConfig().login_required && !getIsAuthenticated()) {
        rememberPendingRoute(pathname);
        showLoginModal();
        hideScreen();
        return;
    }

    const { view, params } = parsePathname(pathname);

    // 3열 메인 레이아웃 유지: 전용 화면 숨기고 라우트에 맞게 모달/패널만 제어
    hideScreen();

    // 방 목록
    if (view === 'room-list') {
        openRoomsModal();
        focusMainAfterRoute();
        return;
    }

    // 방 상세
    if (view === 'room-detail' && params[0]) {
        const rid = decodeURIComponent(params[0]);
        if (getCurrentRoom() !== rid) {
            setCurrentRoom(rid);
            persistRooms();
            renderRoomsUI();
            sendMessage({ action: 'room_load', room_id: getCurrentRoom() });
            sendMessage({ action: 'reset_sessions', room_id: getCurrentRoom() });
            refreshRoomViews();
        }
        focusMainAfterRoute();
        return;
    }

    // 방 설정
    if (view === 'room-settings' && params[0]) {
        const rid = decodeURIComponent(params[0]);
        if (getCurrentRoom() !== rid) {
            setCurrentRoom(rid);
            persistRooms();
            renderRoomsUI();
            sendMessage({ action: 'room_load', room_id: getCurrentRoom() });
        }
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.classList.remove('hidden');
            enableFocusTrap(modal);
        }
        // 최신 컨텍스트 불러와 반영
        sendMessage({ action: 'get_context' });
        return;
    }

    // 방 히스토리
    if (view === 'room-history' && params[0]) {
        const rid = decodeURIComponent(params[0]);
        if (getCurrentRoom() !== rid) {
            setCurrentRoom(rid);
            persistRooms();
            renderRoomsUI();
            refreshRoomViews();
        }
        // 모바일에선 우측 패널 열기
        try { openMobilePanel('right'); } catch (_) {}
        focusMainAfterRoute();
        return;
    }

    // 백업
    if (view === 'backup') {
        renderBackupScreenView();
        focusMainAfterRoute();
        return;
    }

    focusMainAfterRoute();
}

/**
 * 새 경로로 네비게이션
 * @param {string} path
 * @param {object} handlers - renderCurrentScreenFrom에 전달할 핸들러들
 */
export function navigate(path, handlers = {}) {
    window.history.pushState({ path }, '', path);
    renderCurrentScreenFrom(location.pathname, handlers);
}

/**
 * popstate 이벤트 리스너 등록
 * @param {object} handlers - renderCurrentScreenFrom에 전달할 핸들러들
 */
export function initRouter(handlers = {}) {
    window.addEventListener('popstate', () => {
        renderCurrentScreenFrom(location.pathname, handlers);
    });
}

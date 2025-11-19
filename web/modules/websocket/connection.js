/**
 * WebSocket 연결 관리
 * @module websocket/connection
 */

import {
    appConfig,
    ws,
    setWs,
    sessionKey,
    setSessionKey,
    setRooms,
    currentRoom,
    setCurrentRoom,
    authToken,
    setLastRequest,
    setAuthRequired,
    setIsAuthenticated,
    setIsReconnecting,
    setAutoLoginRequested,
    isReconnecting,
    setTokenRefreshTimeout,
    tokenRefreshTimeout
} from '../core/state.js';
import { SESSION_KEY_KEY, ROOMS_KEY, CURRENT_ROOM_KEY, RETRY_ACTIONS } from '../core/constants.js';

/**
 * WebSocket URL 생성
 * @returns {string}
 */
export function buildWebSocketUrl() {
    if (appConfig.ws_url) {
        return appConfig.ws_url;
    }
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.hostname;
    const port = appConfig.ws_port || 8765;
    return `${protocol}://${host}:${port}`;
}

/**
 * 앱 설정 로드
 */
export async function loadAppConfig() {
    try {
        const response = await fetch('/app-config.json', { cache: 'no-store' });
        if (!response.ok) {
            throw new Error(`status ${response.status}`);
        }
        const config = await response.json();
        Object.assign(appConfig, config);
    } catch (error) {
        console.error('앱 설정을 불러오지 못해 기본값을 사용합니다.', error);
    }
}

/**
 * WebSocket 연결
 * 이 함수는 외부 의존성(UI, routing 등)을 콜백으로 받아야 합니다.
 * 현재는 전역 함수를 사용하도록 임시 구현
 */
export function connect(callbacks = {}) {
    const {
        onConnected,
        onMessage,
        onDisconnected,
        log = console.log,
        updateStatus = () => {}
    } = callbacks;

    const wsUrl = buildWebSocketUrl();
    log(`연결 시도: ${wsUrl}`);

    const newWs = new WebSocket(wsUrl);
    setWs(newWs);

    newWs.onopen = () => {
        updateStatus('connected', '연결됨');
        log('WebSocket 연결 성공', 'success');

        // 저장된 세션키/채팅방 불러오기
        try {
            const savedSessionKey = localStorage.getItem(SESSION_KEY_KEY) || '';
            setSessionKey(savedSessionKey);

            const savedRooms = JSON.parse(localStorage.getItem(ROOMS_KEY) || '[]');
            if (Array.isArray(savedRooms) && savedRooms.length) {
                setRooms(savedRooms);
            }

            const savedCurrent = localStorage.getItem(CURRENT_ROOM_KEY);
            if (savedCurrent) setCurrentRoom(savedCurrent);

        } catch (err) {
            console.error('Failed to load session data:', err);
        }

        if (onConnected) onConnected();
    };

    newWs.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (onMessage) onMessage(message);
    };

    newWs.onerror = (error) => {
        log('WebSocket 에러 발생', 'error');
        console.error('WebSocket error:', error);
    };

    newWs.onclose = () => {
        updateStatus('disconnected', '연결 끊김');
        log('연결이 끊어졌습니다. 5초 후 재연결...', 'error');

        // 인증 및 재연결 상태 리셋
        setAuthRequired(false);

        // 의도적인 재연결(로그인 후 등)이 아닐 때만 인증 상태 초기화
        if (!isReconnecting) {
            setIsAuthenticated(false);
        }

        // 재연결 플래그 초기화
        setIsReconnecting(false);
        setAutoLoginRequested(false);

        // 토큰 갱신 타이머 취소
        if (tokenRefreshTimeout) {
            clearTimeout(tokenRefreshTimeout);
            setTokenRefreshTimeout(null);
        }

        // 콜백 실행 (로그인 모달 숨김 등 UI 처리)
        if (onDisconnected) onDisconnected();

        setTimeout(() => connect(callbacks), 5000);
    };
}

/**
 * 메시지 전송
 * @param {object} payload
 * @param {object} options
 * @param {boolean} options.skipToken - 토큰 주입 건너뛰기
 * @param {boolean} options.skipRetry - 재시도 대상에서 제외
 */
export function sendMessage(payload, options = {}) {
    // ws는 state에서 가져옴
    const currentWs = ws;

    if (!currentWs || currentWs.readyState !== WebSocket.OPEN) {
        console.error('WebSocket 연결이 끊어졌습니다');
        return false;
    }

    const message = { ...payload };

    // 인증 토큰 주입 (options.skipToken이 true가 아닌 경우)
    if (!options.skipToken && authToken) {
        message.token = authToken;
    }

    // 세션 키 추가
    if (sessionKey) {
        message.session_key = sessionKey;
    }

    // 방 ID가 필요한 액션들
    const ACTIONS_WITH_ROOM = new Set([
        'chat', 'get_history_snapshot', 'clear_history',
        'get_history_settings', 'set_history_limit', 'get_narrative'
    ]);

    if (ACTIONS_WITH_ROOM.has(String(payload.action))) {
        if (currentRoom) {
            message.room_id = currentRoom;
        }
    }

    // 재시도 대상 액션인 경우 lastRequest에 저장
    if (!options.skipRetry && RETRY_ACTIONS.has(payload.action)) {
        setLastRequest(message);
    }

    currentWs.send(JSON.stringify(message));
    return true;
}

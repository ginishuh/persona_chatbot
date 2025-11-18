/**
 * WebSocket 연결 관리
 * @module websocket/connection
 */

import { appConfig, ws, setWs, sessionKey, setSessionKey, setRooms, currentRoom, setCurrentRoom } from '../core/state.js';
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

        if (onDisconnected) onDisconnected();

        setTimeout(() => connect(callbacks), 5000);
    };
}

/**
 * 메시지 전송
 * @param {object} payload
 * @param {object} options
 */
export function sendMessage(payload, options = {}) {
    // ws는 state에서 가져옴
    const currentWs = ws;

    if (!currentWs || currentWs.readyState !== WebSocket.OPEN) {
        console.error('WebSocket 연결이 끊어졌습니다');
        return;
    }

    const message = { ...payload };

    // 토큰 추가는 auth 모듈에서 처리하도록 분리 필요
    // 현재는 임시로 전역 상태 사용

    if (sessionKey) {
        message.session_key = sessionKey;
    }

    const ACTIONS_WITH_ROOM = new Set([
        'chat', 'get_history_snapshot', 'clear_history',
        'get_history_settings', 'set_history_limit', 'get_narrative'
    ]);

    if (ACTIONS_WITH_ROOM.has(String(payload.action))) {
        if (currentRoom) {
            message.room_id = currentRoom;
        }
    }

    currentWs.send(JSON.stringify(message));
}

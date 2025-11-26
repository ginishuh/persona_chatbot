/**
 * 전역 상태 관리
 * @module core/state
 */

import {
    AUTH_TOKEN_KEY,
    AUTH_EXP_KEY,
    REFRESH_TOKEN_KEY,
    REFRESH_EXP_KEY,
    HISTORY_LIMIT_DEFAULT
} from './constants.js';

// ===== WebSocket 연결 상태 =====
export let ws = null;
export let appConfig = {
    ws_url: '',
    ws_port: 8765,
    login_required: true,
    show_token_usage: true
};

export function setWs(newWs) {
    ws = newWs;
}

export function setAppConfig(config) {
    appConfig = { ...appConfig, ...config };
}

// ===== 인증 상태 =====
export let authToken = '';
export let authTokenExpiresAt = '';
export let refreshToken = '';
export let refreshTokenExpiresAt = '';
export let tokenRefreshTimeout = null;
export let refreshRetryCount = 0;
export let refreshInProgress = false;
export let authRequired = false;
export let isAuthenticated = false;
export let userRole = 'user'; // 'user' | 'admin'

// 로컬스토리지에서 토큰 복원 시도
try {
    authToken = localStorage.getItem(AUTH_TOKEN_KEY) || '';
    authTokenExpiresAt = localStorage.getItem(AUTH_EXP_KEY) || '';
    refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY) || '';
    refreshTokenExpiresAt = localStorage.getItem(REFRESH_EXP_KEY) || '';
} catch (error) {
    authToken = '';
    authTokenExpiresAt = '';
    refreshToken = '';
    refreshTokenExpiresAt = '';
}

export function setAuthTokenState(token, expiresAt) {
    authToken = token || '';
    authTokenExpiresAt = expiresAt || '';
}

export function setRefreshTokenState(token, expiresAt) {
    refreshToken = token || '';
    refreshTokenExpiresAt = expiresAt || '';
}

export function setTokenRefreshTimeout(timeout) {
    tokenRefreshTimeout = timeout;
}

export function setRefreshRetryCount(count) {
    refreshRetryCount = count;
}

export function setRefreshInProgress(inProgress) {
    refreshInProgress = inProgress;
}

export function setAuthRequired(required) {
    authRequired = required;
}

export function setIsAuthenticated(authenticated) {
    isAuthenticated = authenticated;
}

export function setUserRole(role) {
    userRole = role;
}

// Note: do not write authentication state to `window` here; use module exports instead.

// ===== 재연결 및 요청 상태 =====
export let isReconnecting = false;
export let lastRequest = null; // 재전송용 마지막 사용자 액션
export let autoLoginRequested = false;

export function setIsReconnecting(reconnecting) {
    isReconnecting = reconnecting;
}

export function setLastRequest(request) {
    lastRequest = request;
}

export function setAutoLoginRequested(requested) {
    autoLoginRequested = requested;
}

// ===== 채팅 및 캐릭터 상태 =====
export let participants = [];
export let characterColors = {};

export function setParticipants(newParticipants, { silent = false } = {}) {
    participants = Array.isArray(newParticipants) ? newParticipants : [];
    if (silent) return;
    try {
        window.dispatchEvent(new CustomEvent('participants:updated', { detail: participants }));
    } catch (_) {
        /* no-op: 이벤트 알림 실패는 무시 */
    }
}

export function setCharacterColors(colors) {
    characterColors = colors || {};
}

export function getCharacterColor(characterName) {
    if (!characterColors[characterName]) {
        const colors = [
            'character-0',
            'character-1',
            'character-2',
            'character-3',
            'character-4',
            'character-5',
            'character-6',
            'character-7',
            'character-8',
            'character-9'
        ];
        const index = Object.keys(characterColors).length % colors.length;
        characterColors[characterName] = colors[index];
    }
    return characterColors[characterName];
}

// ===== 방 상태 =====
export let rooms = [];
export let currentRoom = null;
export let sessionKey = '';
export let pendingRoutePath = null;

export function setSessionKey(key) {
    sessionKey = key;
}

export function setRooms(newRooms) {
    rooms = newRooms;
}

export function setCurrentRoom(room) {
    currentRoom = room;
    // 헤더 배지 업데이트
    const badge = document.getElementById('currentRoomBadge');
    if (badge) {
        badge.textContent = room ? `📁 ${room}` : '';
    }
}

export function setPendingRoutePath(path) {
    pendingRoutePath = path;
}

// ===== 히스토리 상태 =====
export let currentHistoryLimit = HISTORY_LIMIT_DEFAULT;
export let sessionSettingsLoaded = false;

export function setCurrentHistoryLimit(limit) {
    currentHistoryLimit = limit;
}

export function setSessionSettingsLoaded(loaded) {
    sessionSettingsLoaded = loaded;
}

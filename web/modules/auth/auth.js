/**
 * 인증 및 토큰 관리
 * @module auth/auth
 */

import {
    AUTH_TOKEN_KEY,
    AUTH_EXP_KEY,
    REFRESH_TOKEN_KEY,
    REFRESH_EXP_KEY,
    USER_ROLE_KEY
} from '../core/constants.js';

import {
    setAuthTokenState,
    setRefreshTokenState,
    setRefreshRetryCount,
    setUserRole,
    setIsAuthenticated
} from '../core/state.js';

/**
 * 인증 토큰 설정
 * @param {string} token
 * @param {string} expiresAt
 */
export function setAuthToken(token, expiresAt) {
    setAuthTokenState(token, expiresAt);

    try {
        if (token) {
            localStorage.setItem(AUTH_TOKEN_KEY, token);
            if (expiresAt) {
                localStorage.setItem(AUTH_EXP_KEY, expiresAt);
            } else {
                localStorage.removeItem(AUTH_EXP_KEY);
            }
        } else {
            localStorage.removeItem(AUTH_TOKEN_KEY);
            localStorage.removeItem(AUTH_EXP_KEY);
        }
    } catch (error) {
        console.error('Failed to save auth token:', error);
    }

    // scheduleTokenRefresh() 호출은 별도 처리 필요
}

/**
 * 인증 토큰 삭제
 */
export function clearAuthToken() {
    setRefreshRetryCount(0);
    setAuthToken('', '');
}

/**
 * 리프레시 토큰 설정
 * @param {string} token
 * @param {string} expiresAt
 */
export function setRefreshToken(token, expiresAt) {
    setRefreshTokenState(token, expiresAt);

    try {
        if (token) {
            localStorage.setItem(REFRESH_TOKEN_KEY, token);
            if (expiresAt) {
                localStorage.setItem(REFRESH_EXP_KEY, expiresAt);
            } else {
                localStorage.removeItem(REFRESH_EXP_KEY);
            }
        } else {
            localStorage.removeItem(REFRESH_TOKEN_KEY);
            localStorage.removeItem(REFRESH_EXP_KEY);
        }
    } catch (error) {
        console.error('Failed to save refresh token:', error);
    }
}

/**
 * 로그인 처리
 * @param {string} username
 * @param {string} password
 * @returns {Promise<{success: boolean, data?: object, error?: string}>}
 */
export async function login(username, password) {
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            setAuthToken(data.access_token, data.access_exp);
            setRefreshToken(data.refresh_token, data.refresh_exp);
            setUserRole(data.role || 'user');
            setIsAuthenticated(true);

            localStorage.setItem(USER_ROLE_KEY, data.role || 'user');

            return { success: true, data };
        } else {
            return { success: false, error: data.error || '로그인 실패' };
        }
    } catch (error) {
        console.error('Login error:', error);
        return { success: false, error: '서버 오류가 발생했습니다.' };
    }
}

/**
 * 회원가입 처리
 * @param {string} username
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{success: boolean, error?: string}>}
 */
export async function register(username, email, password) {
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            return { success: true };
        } else {
            return { success: false, error: data.error || '회원가입 실패' };
        }
    } catch (error) {
        console.error('Register error:', error);
        return { success: false, error: '서버 오류가 발생했습니다.' };
    }
}

/**
 * 로그아웃 처리
 */
export function logout() {
    clearAuthToken();
    setRefreshToken('', '');
    setIsAuthenticated(false);
    setUserRole('user');
    localStorage.removeItem(USER_ROLE_KEY);
}

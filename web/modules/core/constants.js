/**
 * 전역 상수 정의
 * @module core/constants
 */

// ===== 로컬스토리지 키 =====
export const AUTH_TOKEN_KEY = 'persona_auth_token';
export const AUTH_EXP_KEY = 'persona_auth_exp';
export const REFRESH_TOKEN_KEY = 'persona_refresh_token';
export const REFRESH_EXP_KEY = 'persona_refresh_exp';
export const USER_ROLE_KEY = 'persona_user_role';

// 세션/채팅방 로컬키
export const SESSION_KEY_KEY = 'persona_session_key';
export const ROOMS_KEY = 'persona_rooms';
export const CURRENT_ROOM_KEY = 'persona_current_room';

// 로그인 저장 키
export const LOGIN_USER_KEY = 'persona_login_user';
export const LOGIN_AUTOLOGIN_KEY = 'persona_login_auto';
export const LOGIN_SAVED_PW_KEY = 'persona_login_pw';
export const LOGIN_ADULT_KEY = 'persona_login_adult';

// ===== 설정 상수 =====
export const RETRY_ACTIONS = new Set([
    'set_context', 'chat',
    'save_workspace_file', 'delete_workspace_file',
    'save_preset', 'delete_preset', 'load_preset',
    'set_history_limit',
    'clear_history', 'reset_sessions'
]);

export const MAX_REFRESH_RETRIES = 3;
export const HISTORY_LIMIT_DEFAULT = 30;

// ===== 기능 플래그 =====
export const STORIES_ENABLED = false;

// WebSocket 연결
let ws = null;
let appConfig = {
    ws_url: '',
    ws_port: 8765,
    login_required: true,
    show_token_usage: true
};

// DOM 요소
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const logArea = document.getElementById('logArea');

// 채팅 관련 요소(동적 화면 대응)
let chatMessages = document.getElementById('chatMessages');
let chatInput = document.getElementById('chatInput');
let sendChatBtn = document.getElementById('sendChatBtn');
function refreshChatRefs() {
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    sendChatBtn = document.getElementById('sendChatBtn');
}

// 컨텍스트 패널 요소
const contextContent = document.getElementById('contextContent');
const worldInput = document.getElementById('worldInput');
const situationInput = document.getElementById('situationInput');
const userCharacterInput = document.getElementById('userCharacterInput');
const narratorEnabled = document.getElementById('narratorEnabled');
const userIsNarrator = document.getElementById('userIsNarrator');
const narratorSettings = document.getElementById('narratorSettings');
const narratorMode = document.getElementById('narratorMode');
const narratorDescription = document.getElementById('narratorDescription');
const charactersList = document.getElementById('charactersList');
const addCharacterBtn = document.getElementById('addCharacterBtn');
const applyCharactersBtn = document.getElementById('applyCharactersBtn');
const aiProvider = document.getElementById('aiProvider');
const modelSelect = document.getElementById('modelSelect');
const adultLevel = document.getElementById('adultLevel');
const adultConsent = document.getElementById('adultConsent');
const narrativeSeparation = document.getElementById('narrativeSeparation');
const narratorDrive = document.getElementById('narratorDrive');
const outputLevel = document.getElementById('outputLevel');
const forceChoices = document.getElementById('forceChoices');
const choiceCount = document.getElementById('choiceCount');
const saveContextBtn = document.getElementById('saveContextBtn');
const historyLengthSlider = document.getElementById('historyLengthSlider');
const historyLengthValue = document.getElementById('historyLengthValue');
const historyUnlimitedToggle = document.getElementById('historyUnlimitedToggle');

// 파일 관리 요소
const worldSelect = document.getElementById('worldSelect');
const saveWorldBtn = document.getElementById('saveWorldBtn');
const deleteWorldBtn = document.getElementById('deleteWorldBtn');
const situationSelect = document.getElementById('situationSelect');
const saveSituationBtn = document.getElementById('saveSituationBtn');
const deleteSituationBtn = document.getElementById('deleteSituationBtn');
const myCharacterSelect = document.getElementById('myCharacterSelect');
const saveMyCharacterBtn = document.getElementById('saveMyCharacterBtn');
const deleteMyCharacterBtn = document.getElementById('deleteMyCharacterBtn');
const userCharacterAgeInput = document.getElementById('userCharacterAge');
const loadProfileJsonBtn = document.getElementById('loadProfileJsonBtn');
const saveProfileJsonBtn = document.getElementById('saveProfileJsonBtn');

// 프리셋 관리 요소
const presetSelect = document.getElementById('presetSelect');
const savePresetBtn = document.getElementById('savePresetBtn');
const loadPresetBtn = document.getElementById('loadPresetBtn');
const deletePresetBtn = document.getElementById('deletePresetBtn');

// 헤더 버튼
// 모드 전환 UI 제거됨: 잔여 참조 방지를 위해 버튼 조회 삭제
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const resetSessionsBtn = document.getElementById('resetSessionsBtn');
const tokenText = document.getElementById('tokenText');
const sessionRetentionToggle = document.getElementById('sessionRetentionToggle');
const sessionStatusBadge = document.getElementById('sessionStatusBadge');

// 서사 패널 요소
const narrativeContent = document.getElementById('narrativeContent');
const saveNarrativeBtn = document.getElementById('saveNarrativeBtn');
const injectStoryBtn = document.getElementById('injectStoryBtn');
const storySelect = document.getElementById('storySelect');
const loadStoryBtn = document.getElementById('loadStoryBtn');
const deleteStoryBtn = document.getElementById('deleteStoryBtn');
const resumeStoryBtn = document.getElementById('resumeStoryBtn');
const STORIES_ENABLED = false;
// 채팅방 UI
const roomSelect = document.getElementById('roomSelect');
const roomAddBtn = document.getElementById('roomAddBtn');
// const roomDelBtn = document.getElementById('roomDelBtn'); // 제거됨 - 개별 삭제 버튼으로 대체
const roomSaveBtn = document.getElementById('roomSaveBtn');

// 로그인 요소
const loginModal = document.getElementById('loginModal');
const loginTab = document.getElementById('loginTab');
const registerTab = document.getElementById('registerTab');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const loginUsernameInput = document.getElementById('loginUsername');
const loginPasswordInput = document.getElementById('loginPassword');
const rememberIdCheckbox = document.getElementById('rememberId');
const autoLoginCheckbox = document.getElementById('autoLogin');
const loginButton = document.getElementById('loginButton');
const loginError = document.getElementById('loginError');
const registerUsernameInput = document.getElementById('registerUsername');
const registerEmailInput = document.getElementById('registerEmail');
const registerPasswordInput = document.getElementById('registerPassword');
const registerPasswordConfirmInput = document.getElementById('registerPasswordConfirm');
const registerButton = document.getElementById('registerButton');
const registerError = document.getElementById('registerError');
// 로그인/로그아웃 버튼
const loginBtn = document.getElementById('loginBtn');
const logoutBtn = document.getElementById('logoutBtn');

// 모바일 더보기 메뉴의 로그인/로그아웃/관리 버튼
const moreLoginBtn = document.getElementById('moreLoginBtn');
const moreLogoutBtn = document.getElementById('moreLogoutBtn');
const moreAdminBtn = document.getElementById('moreAdminBtn');

// 관리자 요소
const adminBtn = document.getElementById('adminBtn');
const adminModal = document.getElementById('adminModal');
const adminCloseBtn = document.getElementById('adminCloseBtn');
const pendingUsersList = document.getElementById('pendingUsersList');
const noPendingUsers = document.getElementById('noPendingUsers');

// 채팅방 이름 입력 모달 요소
const roomNameModal = document.getElementById('roomNameModal');
const roomNameInput = document.getElementById('roomNameInput');
const roomNameCloseBtn = document.getElementById('roomNameCloseBtn');
const roomNameCancelBtn = document.getElementById('roomNameCancelBtn');
const roomNameConfirmBtn = document.getElementById('roomNameConfirmBtn');

let currentAssistantMessage = null;
let characterColors = {}; // 캐릭터별 색상 매핑
let authRequired = false;
let isAuthenticated = false;
let isReconnecting = false; // 의도적인 재연결 여부
let currentProvider = 'claude'; // 최근 전송에 사용한 프로바이더
let participants = []; // 현재 대화 참여자 목록
let pendingConsentResend = false; // 성인 동의 직후 직전 요청 재전송

const AUTH_TOKEN_KEY = 'persona_auth_token';
const AUTH_EXP_KEY = 'persona_auth_exp';
const REFRESH_TOKEN_KEY = 'persona_refresh_token';
const REFRESH_EXP_KEY = 'persona_refresh_exp';
const USER_ROLE_KEY = 'persona_user_role';
// 세션/채팅방 로컬키
const SESSION_KEY_KEY = 'persona_session_key';
const ROOMS_KEY = 'persona_rooms';
const CURRENT_ROOM_KEY = 'persona_current_room';
let authToken = '';
let authTokenExpiresAt = '';
let refreshToken = '';
let refreshTokenExpiresAt = '';
let tokenRefreshTimeout = null;
let refreshRetryCount = 0;
let refreshInProgress = false;
let lastRequest = null; // 재전송용 마지막 사용자 액션
let sessionKey = '';
let userRole = 'user'; // 사용자 역할 ('user' | 'admin')
let rooms = []; // 초기에는 빈 배열 (사용자가 명시적으로 생성해야 함)
let currentRoom = null; // 초기에는 채팅방 없음 (ChatGPT/Claude.ai 스타일)
let pendingRoutePath = null; // 로그인 이후 복원할 경로
let autoLoginRequested = false; // 비로그인 환경 자동 로그인 시도 여부
const RETRY_ACTIONS = new Set([
    'set_context', 'chat',
    'save_workspace_file', 'delete_workspace_file',
    'save_preset', 'delete_preset', 'load_preset',
    'set_history_limit',
    // 모드 전환 액션 제거됨
    'clear_history', 'reset_sessions'
]);
const MAX_REFRESH_RETRIES = 3;
const HISTORY_LIMIT_DEFAULT = 30;
let currentHistoryLimit = HISTORY_LIMIT_DEFAULT;
let sessionSettingsLoaded = false;
// 로그인 저장 키
const LOGIN_USER_KEY = 'persona_login_user';
const LOGIN_AUTOLOGIN_KEY = 'persona_login_auto';
const LOGIN_SAVED_PW_KEY = 'persona_login_pw';
const LOGIN_ADULT_KEY = 'persona_login_adult';
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

function buildWebSocketUrl() {
    if (appConfig.ws_url) {
        return appConfig.ws_url;
    }
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.hostname;
    const port = appConfig.ws_port || 8765;
    return `${protocol}://${host}:${port}`;
}

function setAuthToken(token, expiresAt) {
    authToken = token || '';
    authTokenExpiresAt = expiresAt || '';
    try {
        if (authToken) {
            localStorage.setItem(AUTH_TOKEN_KEY, authToken);
            if (authTokenExpiresAt) {
                localStorage.setItem(AUTH_EXP_KEY, authTokenExpiresAt);
            } else {
                localStorage.removeItem(AUTH_EXP_KEY);
            }
        } else {
            localStorage.removeItem(AUTH_TOKEN_KEY);
            localStorage.removeItem(AUTH_EXP_KEY);
        }
    } catch (error) {
        // ignore storage errors
    }
    scheduleTokenRefresh();
}

function clearAuthToken() {
    refreshRetryCount = 0;
    setAuthToken('', '');
}

function setRefreshToken(token, expiresAt) {
    refreshToken = token || '';
    refreshTokenExpiresAt = expiresAt || '';
    try {
        if (refreshToken) {
            localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
            if (refreshTokenExpiresAt) {
                localStorage.setItem(REFRESH_EXP_KEY, refreshTokenExpiresAt);
            } else {
                localStorage.removeItem(REFRESH_EXP_KEY);
            }
        } else {
            localStorage.removeItem(REFRESH_TOKEN_KEY);
            localStorage.removeItem(REFRESH_EXP_KEY);
        }
    } catch (_) { /* ignore */ }
}

// ===== History API Router (스켈레톤) =====
// 간단한 경로 → 화면 매핑. 현재 단계에서는 기존 화면 구조를 유지하면서 URL만 관리합니다.
const routeTable = [
    // 루트 경로는 매핑하지 않음 - ChatGPT 스타일 환영 화면만 표시
    { pattern: /^\/rooms\/([^\/]+)$/, view: 'room-detail' },
    { pattern: /^\/rooms\/([^\/]+)\/settings$/, view: 'room-settings' },
    { pattern: /^\/rooms\/([^\/]+)\/history$/, view: 'room-history' },
    { pattern: /^\/backup$/, view: 'backup' },
];

function parsePathname(pathname) {
    for (const r of routeTable) {
        const m = pathname.match(r.pattern);
        if (m) {
            return { view: r.view, params: m.slice(1) };
        }
    }
    return { view: null, params: [] }; // 매치되지 않으면 아무 모달도 열지 않음
}

function rememberPendingRoute(pathname) {
    pendingRoutePath = pathname || '/';
}

function resumePendingRoute() {
    if (!pendingRoutePath) return;
    if (appConfig.login_required && !isAuthenticated) {
        return;
    }
    const target = pendingRoutePath;
    pendingRoutePath = null;
    try {
        renderCurrentScreenFrom(target);
    } catch (_) {}
}

function renderCurrentScreenFrom(pathname) {
    if (appConfig.login_required && !isAuthenticated) {
        rememberPendingRoute(pathname);
        showLoginModal();
        hideScreen();
        return;
    }
    const { view, params } = parsePathname(pathname);
    // 3열 메인 레이아웃 유지: 전용 화면 숨기고(main-content 표시), 라우트에 맞게 모달/패널만 제어
    hideScreen();

    if (view === 'room-list') {
        openRoomsModal();
        focusMainAfterRoute();
        return;
    }

    if (view === 'room-detail' && params[0]) {
        const rid = decodeURIComponent(params[0]);
        if (currentRoom !== rid) {
            currentRoom = rid;
            persistRooms();
            renderRoomsUI();
            sendMessage({ action: 'room_load', room_id: currentRoom });
            sendMessage({ action: 'reset_sessions', room_id: currentRoom });
            refreshRoomViews();
        }
        focusMainAfterRoute();
        return;
    }

    if (view === 'room-settings' && params[0]) {
        const rid = decodeURIComponent(params[0]);
        if (currentRoom !== rid) {
            currentRoom = rid;
            persistRooms();
            renderRoomsUI();
            sendMessage({ action: 'room_load', room_id: currentRoom });
        }
        const modal = document.getElementById('settingsModal');
        if (modal) { modal.classList.remove('hidden'); enableFocusTrap(modal); }
        // 최신 컨텍스트 불러와 반영
        sendMessage({ action: 'get_context' });
        return;
    }

    if (view === 'room-history' && params[0]) {
        const rid = decodeURIComponent(params[0]);
        if (currentRoom !== rid) {
            currentRoom = rid;
            persistRooms();
            renderRoomsUI();
            refreshRoomViews();
        }
        // 모바일에선 우측 패널 열기
        try { openMobilePanel('right'); } catch (_) {}
        focusMainAfterRoute();
        return;
    }

    if (view === 'backup') {
        openBackupModal();
        return;
    }

    focusMainAfterRoute();
}

function navigate(path) {
    window.history.pushState({ path }, '', path);
    renderCurrentScreenFrom(location.pathname);
}

window.addEventListener('popstate', () => renderCurrentScreenFrom(location.pathname));

// ===== 접근성(A11y) 보완 =====
function focusMainAfterRoute() {
    // 채팅 입력으로 포커스 이동, 없으면 첫 번째 헤더로
    try {
        if (chatInput && !chatInput.disabled) {
            chatInput.focus();
            return;
        }
        const h1 = document.querySelector('main h1, header h1');
        if (h1) h1.tabIndex = -1, h1.focus();
    } catch (_) {}
}

function applyARIA() {
    const pairs = [
        [sendChatBtn, '메시지 전송'],
        [clearHistoryBtn, '대화 히스토리 초기화'],
        [resetSessionsBtn, '세션 초기화'],
        [roomAddBtn, '채팅방 추가'],
        // [roomDelBtn, '채팅방 삭제'], // 제거됨 - 개별 삭제 버튼으로 대체
        [roomSaveBtn, '채팅방 설정 저장'],
        [saveContextBtn, '컨텍스트 저장'],
        [document.getElementById('narrativeMenuBtn'), '히스토리 패널 열기'],
        [document.getElementById('moreMenuBtn'), '더보기 메뉴 열기'],
        [document.getElementById('participantsBtn'), '참여자 관리'],
        [document.getElementById('settingsBtn'), '설정 열기'],
        [document.getElementById('hamburgerBtn'), '좌측 패널 토글'],
        [document.getElementById('narrativeMenuBtn'), '우측 패널 토글'],
        [document.getElementById('loginButton'), '로그인 제출'],
        [document.getElementById('autoLoginButton'), '자동 로그인']
    ];
    pairs.forEach(([el, label]) => { try { el?.setAttribute('aria-label', label); } catch (_) {} });
    try { narrativeContent?.setAttribute('aria-live', 'polite'); } catch (_) {}
}

function injectSkipLink() {
    try {
        const a = document.createElement('a');
        a.href = '#';
        a.className = 'skip-link';
        a.textContent = '본문으로 건너뛰기';
        a.style.position = 'absolute';
        a.style.left = '-9999px';
        a.style.top = '0';
        a.style.zIndex = '10000';
        a.addEventListener('focus', () => { a.style.left = '8px'; a.style.top = '8px'; });
        a.addEventListener('blur', () => { a.style.left = '-9999px'; });
        a.addEventListener('click', (e) => { e.preventDefault(); focusMainAfterRoute(); });
        document.body.prepend(a);
    } catch (_) {}
}

// 초기 접근성 적용
applyARIA();
injectSkipLink();

// ===== A11y: 포커스 트랩 =====
const __focusTrap = new Map();

function getFocusable(el) {
    return el.querySelectorAll('a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])');
}

function enableFocusTrap(modalEl) {
    try {
        if (!modalEl) return;
        const handler = (e) => {
            if (e.key !== 'Tab') return;
            const nodes = Array.from(getFocusable(modalEl)).filter(n => !n.disabled && n.tabIndex !== -1);
            if (!nodes.length) return;
            const first = nodes[0];
            const last = nodes[nodes.length - 1];
            if (e.shiftKey) {
                if (document.activeElement === first || !modalEl.contains(document.activeElement)) {
                    e.preventDefault();
                    last.focus();
                }
            } else {
                if (document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
        };
        modalEl.addEventListener('keydown', handler);
        __focusTrap.set(modalEl, handler);
        // 초점 진입
        setTimeout(() => {
            const nodes = Array.from(getFocusable(modalEl)).filter(n => !n.disabled && n.tabIndex !== -1);
            (nodes[0] || modalEl).focus();
        }, 0);
    } catch (_) {}
}

function disableFocusTrap(modalEl) {
    try {
        const handler = __focusTrap.get(modalEl);
        if (handler) modalEl.removeEventListener('keydown', handler);
        __focusTrap.delete(modalEl);
    } catch (_) {}
}

// ===== A11y: 상태 안내 =====
function announce(message) {
    try {
        const live = document.getElementById('ariaLive');
        if (!live) return;
        live.textContent = '';
        // SR이 같은 문장을 무시하지 않도록 미세 지연
        setTimeout(() => { live.textContent = message; }, 10);
    } catch (_) {}
}

// ESC로 닫기(로그인 모달 제외)
document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    const login = document.getElementById('loginModal');
    const settings = document.getElementById('settingsModal');
    const participants = document.getElementById('participantsModal');
    const editor = document.getElementById('characterEditorModal');
    const tryClose = (el) => {
        if (el && !el.classList.contains('hidden')) {
            el.classList.add('hidden');
            disableFocusTrap(el);
            return true;
        }
        return false;
    };
    // 로그인 모달은 ESC로 닫지 않음(정책상 로그인 필요 환경 고려)
    if (tryClose(editor)) return;
    if (tryClose(participants)) return;
    if (tryClose(settings)) return;
});

// ===== 백업(Export) 모달 =====
function buildExportUrl() {
    const scope = document.getElementById('bkScopeFull').checked ? 'full'
        : (document.getElementById('bkScopeSelected').checked ? 'selected' : 'single');
    const inc = [];
    if (document.getElementById('bkIncMessages').checked) inc.push('messages');
    if (document.getElementById('bkIncContext').checked) inc.push('context');
    if (document.getElementById('bkIncToken').checked) inc.push('token_usage');
    const start = document.getElementById('bkStart').value;
    const end = document.getElementById('bkEnd').value;
    const ndjson = document.getElementById('bkFmtNdjson').checked;
    const zip = document.getElementById('bkFmtZip').checked;

    const base = ndjson ? '/api/export/stream' : '/api/export';
    const params = new URLSearchParams();
    params.set('scope', scope);
    if (scope === 'single') {
        if (!currentRoom) {
            alert('내보낼 채팅방을 선택해주세요.');
            return null;
        }
        params.set('room_id', currentRoom);
    }
    if (scope === 'selected') {
        const sel = Array.from(document.querySelectorAll('#bkRoomsWrap input[type="checkbox"]:checked')).map(x => x.value);
        if (sel.length) {
            params.set('room_ids', sel.join(','));
        } else if (currentRoom) {
            params.set('room_ids', currentRoom);
        } else {
            alert('내보낼 채팅방을 선택해주세요.');
            return null;
        }
    }
    if (inc.length) params.set('include', inc.join(','));
    if (start) params.set('start', start.replace('T','T')); // 그대로 전달
    if (end) params.set('end', end.replace('T','T'));
    if (!ndjson && zip) params.set('format','zip');
    if (appConfig.login_required && authToken) {
        params.set('token', authToken);
    } else if (sessionKey) {
        // 비로그인 모드: session_key를 쿼리 파라미터로 전달
        params.set('session_key', sessionKey);
    }
    return `${base}?${params.toString()}`;
}

function populateBackupRooms() {
    const wrap = document.getElementById('bkRoomsWrap');
    if (!wrap) return;
    wrap.innerHTML = '';
    const items = Array.isArray(rooms) ? rooms : [];
    if (!items.length) { wrap.innerHTML = '<p class="hint">저장된 방이 없습니다.</p>'; return; }
    items.forEach(r => {
        const rid = typeof r === 'string' ? r : (r.room_id || r.title || 'default');
        const title = (typeof r === 'object' && r.title) ? r.title : rid;
        const id = `bk-room-${rid}`;
        const row = document.createElement('label');
        row.className = 'checkbox-label';
        row.innerHTML = `<input type="checkbox" value="${rid}" id="${id}"> <span>${title}</span>`;
        wrap.appendChild(row);
        if (rid === currentRoom) {
            row.querySelector('input').checked = true;
        }
    });
}

function openBackupModal() {
    const modal = document.getElementById('backupModal');
    if (!modal) return;
    populateBackupRooms();
    modal.classList.remove('hidden');
    enableFocusTrap(modal);
}

function closeBackupModal() {
    const modal = document.getElementById('backupModal');
    if (!modal) return;
    modal.classList.add('hidden');
    disableFocusTrap(modal);
}

document.getElementById('bkCloseBtn')?.addEventListener('click', closeBackupModal);
document.querySelector('#backupModal .settings-modal-overlay')?.addEventListener('click', closeBackupModal);
document.getElementById('bkDownloadBtn')?.addEventListener('click', () => {
    const url = buildExportUrl();
    if (!url) return; // 검증 실패 시 리턴
    try { window.open(url, '_blank'); } catch (_) { location.href = url; }
});

// scope 라디오 변경 시 방 목록 표시/숨김
['bkScopeSingle','bkScopeSelected','bkScopeFull'].forEach(id => {
    const el = document.getElementById(id);
    el?.addEventListener('change', () => {
        const show = document.getElementById('bkScopeSelected').checked;
        const wrap = document.getElementById('bkRoomsWrap');
        if (wrap) wrap.style.display = show ? 'block' : 'none';
        if (show) populateBackupRooms();
    });
});

// Backup 전용 화면
function buildExportUrlFrom(prefix) {
    const byId = (id) => document.getElementById(prefix + id);
    const scope = byId('ScopeFull')?.checked ? 'full' : (byId('ScopeSelected')?.checked ? 'selected' : 'single');
    const inc = [];
    if (byId('IncMessages')?.checked) inc.push('messages');
    if (byId('IncContext')?.checked) inc.push('context');
    if (byId('IncToken')?.checked) inc.push('token_usage');
    const start = byId('Start')?.value;
    const end = byId('End')?.value;
    const ndjson = byId('FmtNdjson')?.checked;
    const zip = byId('FmtZip')?.checked;
    const base = ndjson ? '/api/export/stream' : '/api/export';
    const params = new URLSearchParams();
    params.set('scope', scope);
    if (scope === 'single') {
        if (!currentRoom) {
            alert('내보낼 채팅방을 선택해주세요.');
            return null;
        }
        params.set('room_id', currentRoom);
    }
    if (scope === 'selected') {
        const sel = Array.from(document.querySelectorAll('#sbkRoomsWrap input[type="checkbox"]:checked')).map(x => x.value);
        if (sel.length) {
            params.set('room_ids', sel.join(','));
        } else if (currentRoom) {
            params.set('room_ids', currentRoom);
        } else {
            alert('내보낼 채팅방을 선택해주세요.');
            return null;
        }
    }
    if (inc.length) params.set('include', inc.join(','));
    if (start) params.set('start', start);
    if (end) params.set('end', end);
    if (!ndjson && zip) params.set('format','zip');
    if (appConfig.login_required && authToken) {
        params.set('token', authToken);
    } else if (sessionKey) {
        // 비로그인 모드: session_key를 쿼리 파라미터로 전달
        params.set('session_key', sessionKey);
    }
    return `${base}?${params.toString()}`;
}

function populateBackupRoomsScreen() {
    const wrap = document.getElementById('sbkRoomsWrap');
    if (!wrap) return;
    wrap.innerHTML = '';
    const items = Array.isArray(rooms) ? rooms : [];
    items.forEach(r => {
        const rid = typeof r === 'string' ? r : (r.room_id || r.title || 'default');
        const title = (typeof r === 'object' && r.title) ? r.title : rid;
        const id = `sbk-room-${rid}`;
        const row = document.createElement('label');
        row.className = 'checkbox-label';
        row.innerHTML = `<input type="checkbox" value="${rid}" id="${id}"> <span>${title}</span>`;
        wrap.appendChild(row);
        if (rid === currentRoom) row.querySelector('input').checked = true;
    });
}

function renderBackupScreenView() {
    const html = `
    <section aria-labelledby="backupScreenTitle">
      <h1 id="backupScreenTitle">백업 내보내기</h1>
      <div class="context-section">
        <label>범위(scope)</label>
        <div style="display:flex; gap:0.75rem; flex-wrap:wrap; align-items:center;">
          <label class="checkbox-label"><input type="radio" name="sbkScope" id="sbkScopeSingle" checked> <span>현재 방</span></label>
          <label class="checkbox-label"><input type="radio" name="sbkScope" id="sbkScopeSelected"> <span>선택한 방</span></label>
          <label class="checkbox-label"><input type="radio" name="sbkScope" id="sbkScopeFull"> <span>전체</span></label>
        </div>
        <div id="sbkRoomsWrap" style="margin-top:0.5rem; display:none; border:1px solid #e8ecef; border-radius:6px; padding:0.5rem; max-height:160px; overflow:auto;"></div>
      </div>
      <div class="context-section">
        <label>포함 항목(include)</label>
        <div style="display:flex; gap:0.75rem; flex-wrap:wrap; align-items:center;">
          <label class="checkbox-label"><input type="checkbox" id="sbkIncMessages" checked> <span>messages</span></label>
          <label class="checkbox-label"><input type="checkbox" id="sbkIncContext" checked> <span>context</span></label>
          <label class="checkbox-label"><input type="checkbox" id="sbkIncToken"> <span>token_usage</span></label>
        </div>
      </div>
      <div class="context-section">
        <label>기간(start/end)</label>
        <div style="display:flex; gap:0.75rem; flex-wrap:wrap; align-items:center;">
          <input type="datetime-local" id="sbkStart" class="input" style="min-width:220px;">
          <input type="datetime-local" id="sbkEnd" class="input" style="min-width:220px;">
        </div>
      </div>
      <div class="context-section">
        <label>형식(format)</label>
        <div style="display:flex; gap:0.75rem; flex-wrap:wrap; align-items:center;">
          <label class="checkbox-label"><input type="radio" name="sbkFormat" id="sbkFmtJson" checked> <span>JSON</span></label>
          <label class="checkbox-label"><input type="radio" name="sbkFormat" id="sbkFmtZip"> <span>ZIP(JSON)</span></label>
          <label class="checkbox-label"><input type="radio" name="sbkFormat" id="sbkFmtNdjson"> <span>Stream(NDJSON)</span></label>
        </div>
      </div>
      <div class="context-section" style="display:flex; gap:0.5rem;">
        <button class="btn" onclick="navigate(currentRoom ? '/rooms/${encodeURIComponent(currentRoom)}' : '/')">← 돌아가기</button>
        <button id="sbkDownloadBtn" class="btn btn-primary">⬇️ 다운로드</button>
      </div>
    </section>`;
    showScreen(html);
    // events
    document.getElementById('sbkDownloadBtn')?.addEventListener('click', () => {
        const idmap = {
          ScopeFull: 'sbkScopeFull', ScopeSelected: 'sbkScopeSelected', IncMessages:'sbkIncMessages', IncContext:'sbkIncContext', IncToken:'sbkIncToken', Start:'sbkStart', End:'sbkEnd', FmtNdjson:'sbkFmtNdjson', FmtZip:'sbkFmtZip'
        };
        // helper expects prefix mapping; we alias by setting IDs; simpler: temporarily map
        const url = buildExportUrlFrom('sbk');
        if (!url) return; // 검증 실패 시 리턴
        try { window.open(url, '_blank'); } catch (_) { location.href = url; }
    });
    // scope radio
    ['sbkScopeSingle','sbkScopeSelected','sbkScopeFull'].forEach(id => {
        document.getElementById(id)?.addEventListener('change', () => {
            const show = document.getElementById('sbkScopeSelected').checked;
            const wrap = document.getElementById('sbkRoomsWrap');
            if (wrap) wrap.style.display = show ? 'block' : 'none';
            if (show) populateBackupRoomsScreen();
        });
    });
}

// ===== 전용 화면 컨테이너 토글 =====
function showScreen(html) {
    const root = document.getElementById('screenRoot');
    const main = document.querySelector('.main-content');
    if (root && main) {
        root.innerHTML = html || '';
        root.classList.add('active');
        root.classList.remove('hidden');
        main.classList.add('hidden');
    }
}

function hideScreen() {
    const root = document.getElementById('screenRoot');
    const main = document.querySelector('.main-content');
    if (root && main) {
        root.classList.remove('active');
        root.classList.add('hidden');
        root.innerHTML = '';
        main.classList.remove('hidden');
    }
}

// Rooms 화면
function renderRoomsScreen() {
    const items = (Array.isArray(rooms) ? rooms : []).map(r => {
        const rid = typeof r === 'string' ? r : (r.room_id || r.title || 'default');
        const title = (typeof r === 'object' && r.title) ? r.title : rid;
        return { rid, title };
    });
    const cards = items.map(it => `
      <button class="btn" style="width:100%; text-align:left; margin-bottom:8px;" onclick="navigate('/rooms/${encodeURIComponent(it.rid)}')">${it.title}</button>
    `).join('');
    const html = `
      <section aria-labelledby="roomsScreenTitle">
        <h1 id="roomsScreenTitle">채팅방</h1>
        <div style="max-width:720px; margin-top:0.5rem;">${cards || '<div class="empty">채팅방이 없습니다.</div>'}</div>
        <div style="margin-top:0.75rem; display:flex; gap:0.5rem;">
          <button class="btn" onclick="navigate(currentRoom ? '/rooms/${encodeURIComponent(currentRoom)}' : '/')">← 돌아가기</button>
          <button class="btn btn-primary" onclick="(function(){ const name=prompt('새 채팅방 이름','room_'+Math.random().toString(36).slice(2,6)); if(!name) return; const r=sanitizeRoomName(name); if(!rooms.find(x => (typeof x==='string'?x:x.room_id)===r)) rooms.push(r); currentRoom=r; persistRooms(); renderRoomsUI(); const cfg=collectRoomConfig(r); sendMessage({action:'room_save', room_id:r, config:cfg}); setTimeout(()=>sendMessage({action:'room_list'}),300); navigate('/rooms/'+encodeURIComponent(r)); })()">+ 새 채팅방</button>
        </div>
      </section>`;
    showScreen(html);
}

// Chat 전용 화면
function renderRoomScreenView(roomId) {
    const html = `
      <section aria-labelledby="roomScreenTitle" style="max-width:900px;">
        <h1 id="roomScreenTitle">대화 — ${roomId}</h1>
        <div id="chatMessages" class="chat-messages" style="height:60vh; overflow:auto; border:1px solid #e8ecef; border-radius:6px; padding:0.75rem; background:#fff; margin-top:0.5rem;">
          <div class="chat-message system"><p>대화를 시작하세요</p></div>
        </div>
        <div class="chat-input-container" style="display:flex; gap:0.5rem; margin-top:0.5rem;">
          <textarea id="chatInput" rows="3" class="input" placeholder="메시지를 입력하세요..." style="flex:1;"></textarea>
          <button id="sendChatBtn" class="btn btn-primary">전송</button>
        </div>
        <div style="margin-top:0.75rem; display:flex; gap:0.5rem; flex-wrap:wrap;">
          <button class="btn" onclick="navigate('/')">← 방 목록</button>
          <button class="btn" onclick="navigate('/rooms/${encodeURIComponent(roomId)}/settings')">⚙️ 설정</button>
          <button class="btn" onclick="navigate('/rooms/${encodeURIComponent(roomId)}/history')">📜 히스토리</button>
        </div>
      </section>`;
    showScreen(html);
    bindChatEvents();
}

// History 화면
function renderHistoryScreenView(id) {
    // Export URL에 token 또는 session_key 추가
    const params = new URLSearchParams({ scope: 'single', room_id: id });
    if (appConfig.login_required && authToken) {
        params.set('token', authToken);
    } else if (sessionKey) {
        params.set('session_key', sessionKey);
    }
    const jsonUrl = `/api/export?${params.toString()}`;
    const ndjsonUrl = `/api/export/stream?${params.toString()}`;

    const html = `
      <section aria-labelledby="historyScreenTitle">
        <h1 id="historyScreenTitle">히스토리</h1>
        <div id="historyScreenBody">로딩...</div>
        <div style="display:flex; gap:0.5rem; margin-top:0.5rem; flex-wrap:wrap;">
          <button class="btn" onclick="navigate('/rooms/${encodeURIComponent(id)}')">← 돌아가기</button>
          <button class="btn" onclick="downloadRoomMd('${id}')">MD 다운로드</button>
          <a class="btn" href="${jsonUrl}" target="_blank">JSON</a>
          <a class="btn" href="${ndjsonUrl}" target="_blank">NDJSON</a>
        </div>
      </section>`;
    showScreen(html);
    // 데이터 로드
    sendMessage({ action: 'get_history_snapshot', room_id: id });
}

// 히스토리 스냅샷 수신 시 전용 화면도 갱신
function renderHistorySnapshotScreen(history) {
    const el = document.getElementById('historyScreenBody');
    if (!el) return;
    if (!Array.isArray(history) || history.length === 0) {
        el.innerHTML = '<div class="empty">대화가 없습니다.</div>';
        return;
    }
    el.innerHTML = history.map(m => {
        const role = m.role === 'user' ? '사용자' : 'AI 응답';
        return `<h3>${role}</h3><pre style="white-space:pre-wrap">${(m.content||'').replace(/</g,'&lt;')}</pre>`;
    }).join('');
}

function downloadRoomMd(rid) {
    const params = new URLSearchParams({ room_id: rid });
    if (appConfig.login_required && authToken) {
        params.set('token', authToken);
    } else if (sessionKey) {
        // 비로그인 모드: session_key를 쿼리 파라미터로 전달
        params.set('session_key', sessionKey);
    }
    const url = `/api/export/md?${params.toString()}`;
    try { window.open(url, '_blank'); } catch (_) { location.href = url; }
}

// ===== 방 목록(Home) 모달 =====
function populateRoomsModal() {
    const wrap = document.getElementById('rmList');
    const q = (document.getElementById('rmSearch')?.value || '').trim().toLowerCase();
    if (!wrap) return;
    wrap.innerHTML = '';
    const items = (Array.isArray(rooms) ? rooms : []).map(r => {
        const rid = typeof r === 'string' ? r : (r.room_id || r.title || 'default');
        const title = (typeof r === 'object' && r.title) ? r.title : rid;
        return { rid, title };
    }).filter(x => !q || x.title.toLowerCase().includes(q) || x.rid.toLowerCase().includes(q));
    if (!items.length) {
        wrap.innerHTML = '<div class="empty">채팅방이 없습니다.</div>';
        return;
    }
    items.forEach(it => {
        const container = document.createElement('div');
        container.style = 'display:flex; gap:0.25rem; margin-bottom:6px; align-items:stretch;';

        const btn = document.createElement('button');
        btn.className = 'btn btn-sm';
        btn.style = 'flex:1; text-align:left;';
        btn.textContent = it.title;
        btn.addEventListener('click', () => {
            closeRoomsModal();
            navigate(`/rooms/${encodeURIComponent(it.rid)}`);
        });

        const delBtn = document.createElement('button');
        delBtn.className = 'btn btn-sm btn-remove';
        delBtn.textContent = '🗑️';
        delBtn.title = '삭제';
        delBtn.style = 'padding: 0.25rem 0.5rem;';
        delBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (!confirm(`채팅방 '${it.title}' 을(를) 삭제하시겠습니까?`)) return;
            sendMessage({ action: 'room_delete', room_id: it.rid });
            // DB 삭제 후 목록 재동기화
            setTimeout(() => sendMessage({ action: 'room_list' }), 300);
            // 로컬 상태는 즉시 업데이트 (UX)
            rooms = rooms.filter(r => (typeof r === 'string' ? r : r.room_id) !== it.rid);
            if (currentRoom === it.rid) {
                currentRoom = rooms.length > 0 ? (typeof rooms[0] === 'string' ? rooms[0] : rooms[0].room_id) : null;
            }
            persistRooms();
            populateRoomsModal();
            renderRoomsUI();
            renderRoomsRightPanelList();
            log('채팅방 삭제 완료', 'success');
        });

        container.appendChild(btn);
        container.appendChild(delBtn);
        wrap.appendChild(container);
    });
}

function openRoomsModal() {
    if (appConfig.login_required && !isAuthenticated) {
        showLoginModal();
        return;
    }
    const modal = document.getElementById('roomsModal');
    if (!modal) return;
    populateRoomsModal();
    modal.classList.remove('hidden');
    enableFocusTrap(modal);
}

function closeRoomsModal() {
    const modal = document.getElementById('roomsModal');
    if (!modal) return;
    modal.classList.add('hidden');
    disableFocusTrap(modal);
}

document.getElementById('rmCloseBtn')?.addEventListener('click', closeRoomsModal);
document.querySelector('#roomsModal .settings-modal-overlay')?.addEventListener('click', closeRoomsModal);
document.getElementById('rmSearch')?.addEventListener('input', populateRoomsModal);
document.getElementById('rmNewBtn')?.addEventListener('click', () => {
    // roomNameModal 사용 (한글 입력 지원)
    roomNameInput.value = ''; // 입력 초기화
    roomNameModal.classList.remove('hidden');
    setTimeout(() => roomNameInput.focus(), 100); // 포커스
    closeRoomsModal(); // 기존 모달 닫기
});

// ===== 3열 우측 패널: 방 목록 렌더 =====
function renderRoomsRightPanelList() {
    const list = document.getElementById('roomList');
    const search = document.getElementById('roomSearch');
    if (!list) return;
    const q = (search?.value || '').trim().toLowerCase();
    list.innerHTML = '';
    const items = (Array.isArray(rooms) ? rooms : []).map(r => {
        const rid = typeof r === 'string' ? r : (r.room_id || r.title || 'default');
        const title = (typeof r === 'object' && r.title) ? r.title : rid;
        return { rid, title };
    }).filter(x => !q || x.title.toLowerCase().includes(q) || x.rid.toLowerCase().includes(q));
    if (!items.length) {
        list.innerHTML = '<div class="empty">저장된 채팅방이 없습니다.</div>';
        return;
    }
    items.forEach(it => {
        const container = document.createElement('div');
        container.style = 'display:flex; gap:0.25rem; margin-bottom:4px; align-items:stretch;';

        const btn = document.createElement('button');
        btn.className = 'btn btn-sm';
        btn.style = 'flex:1; text-align:left;';
        btn.textContent = it.title;
        btn.addEventListener('click', () => {
            navigate(`/rooms/${encodeURIComponent(it.rid)}`);
        });

        const delBtn = document.createElement('button');
        delBtn.className = 'btn btn-sm btn-remove';
        delBtn.textContent = '🗑️';
        delBtn.title = '삭제';
        delBtn.style = 'padding: 0.25rem 0.5rem;';
        delBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (!confirm(`채팅방 '${it.title}' 을(를) 삭제하시겠습니까?`)) return;
            sendMessage({ action: 'room_delete', room_id: it.rid });
            // DB 삭제 후 목록 재동기화
            setTimeout(() => sendMessage({ action: 'room_list' }), 300);
            // 로컬 상태는 즉시 업데이트 (UX)
            rooms = rooms.filter(r => (typeof r === 'string' ? r : r.room_id) !== it.rid);
            if (currentRoom === it.rid) {
                currentRoom = rooms.length > 0 ? (typeof rooms[0] === 'string' ? rooms[0] : rooms[0].room_id) : null;
            }
            persistRooms();
            renderRoomsUI();
            renderRoomsRightPanelList();
            refreshRoomViews();
            log('채팅방 삭제 완료', 'success');
        });

        container.appendChild(btn);
        container.appendChild(delBtn);
        list.appendChild(container);
    });
}

document.getElementById('roomSearch')?.addEventListener('input', renderRoomsRightPanelList);

// ===== WebSocket 연결 =====

async function loadAppConfig() {
    try {
        const response = await fetch('/app-config.json', { cache: 'no-store' });
        if (!response.ok) {
            throw new Error(`status ${response.status}`);
        }
        const config = await response.json();
        appConfig = {
            ...appConfig,
            ...config
        };
    } catch (error) {
        log('앱 설정을 불러오지 못해 기본값을 사용합니다.', 'error');
    }
}

function connect() {
    const wsUrl = buildWebSocketUrl();
    log(`연결 시도: ${wsUrl}`);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        updateStatus('connected', '연결됨');
        log('WebSocket 연결 성공', 'success');
        // 저장된 세션키/채팅방 불러오기
        try {
            sessionKey = localStorage.getItem(SESSION_KEY_KEY) || '';
            const savedRooms = JSON.parse(localStorage.getItem(ROOMS_KEY) || '[]');
            if (Array.isArray(savedRooms) && savedRooms.length) {
                rooms = savedRooms;
            }
            const savedCurrent = localStorage.getItem(CURRENT_ROOM_KEY);
            if (savedCurrent) currentRoom = savedCurrent;
            renderRoomsUI();
        } catch (_) {}
        // 초기 라우트 반영
        try { renderCurrentScreenFrom(location.pathname); } catch (_) {}
    };

    ws.onmessage = (event) => {
        handleMessage(JSON.parse(event.data));
    };

    ws.onerror = (error) => {
        log('WebSocket 에러 발생', 'error');
        console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
        updateStatus('disconnected', '연결 끊김');
        log('연결이 끊어졌습니다. 5초 후 재연결...', 'error');
        authRequired = false;
        // 의도적인 재연결(로그인 후 등)이 아닐 때만 인증 상태 초기화
        if (!isReconnecting) {
            isAuthenticated = false;
        }
        isReconnecting = false; // 플래그 초기화
        autoLoginRequested = false;
        hideLoginModal();
        clearTimeout(tokenRefreshTimeout);
        tokenRefreshTimeout = null;
        setTimeout(connect, 5000);
    };
}

// 모델 옵션 갱신
function updateModelOptions(provider) {
    if (!modelSelect) return;
    const prev = modelSelect.value;
    modelSelect.innerHTML = '';
    const add = (label, value) => {
        const opt = document.createElement('option');
        opt.value = value;
        opt.textContent = label;
        modelSelect.appendChild(opt);
    };
    if (provider === 'gemini') {
        add('gemini-2.5-flash', 'gemini-2.5-flash');
        add('gemini-2.5-pro', 'gemini-2.5-pro');
    } else if (provider === 'claude') {
        add('기본(권장)', '');
        // Anthropic CLI는 alias를 지원: sonnet | haiku | opus
        add('Sonnet (alias: sonnet)', 'sonnet');
        add('Haiku (alias: haiku)', 'haiku');
    } else if (provider === 'droid') {
        add('서버 기본(커스텀)', '');
    }
    // 이전 선택 복원
    const found = [...modelSelect.options].some(o => o.value === prev);
    modelSelect.value = found ? prev : '';
    // Droid는 혼선 방지를 위해 모델 선택 비활성화 (서버 기본 사용)
    if (provider === 'droid') {
        modelSelect.disabled = true;
        modelSelect.title = 'Droid는 서버 기본(DROID_MODEL)만 사용합니다';
    } else {
        modelSelect.disabled = false;
        modelSelect.title = '';
    }
}

if (aiProvider) {
    updateModelOptions(aiProvider.value || 'claude');
    aiProvider.addEventListener('change', () => updateModelOptions(aiProvider.value));
}

// 주도권 ↔ 선택지 연동: describe=선택지X, guide=선택지ON, direct=선택지X(강제)
if (narratorDrive) {
    const syncChoiceControls = () => {
        const mode = narratorDrive.value;
        if (!forceChoices || !choiceCount) return;
        if (mode === 'guide') {
            // 자동 체크하지 않음: 진행자 방식과 혼선 방지
            forceChoices.disabled = false;
            choiceCount.disabled = !forceChoices.checked;
        } else if (mode === 'direct') {
            forceChoices.checked = false;
            forceChoices.disabled = true;
            choiceCount.disabled = true;
        } else { // describe
            forceChoices.checked = false;
            forceChoices.disabled = false; // 사용자가 원하면 켤 수는 있게 둠
            choiceCount.disabled = !forceChoices.checked;
        }
    };
    narratorDrive.addEventListener('change', syncChoiceControls);
    syncChoiceControls();
}

// 선택지 토글이 바뀌면 개수 입력 사용 가능 여부 동기화
if (forceChoices && choiceCount) {
    forceChoices.addEventListener('change', () => {
        choiceCount.disabled = !forceChoices.checked;
    });
}

// 상태 업데이트
function updateStatus(status, text) {
    statusIndicator.className = `status-indicator ${status}`;
    statusText.textContent = text;
}

// 로그 출력
function log(message, type = 'info') {
    const p = document.createElement('p');
    p.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    if (type !== 'info') {
        p.className = `log-${type}`;
    }
    logArea.appendChild(p);
    logArea.scrollTop = logArea.scrollHeight;

    // 로그 개수 제한 (최근 50개)
    while (logArea.children.length > 50) {
        logArea.removeChild(logArea.firstChild);
    }
}

function sendMessage(payload, options = {}) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        log('WebSocket 연결이 끊어졌습니다', 'error');
        return;
    }
    const message = { ...payload };
    if (!options.skipToken && authToken) {
        message.token = authToken;
    }
    if (sessionKey) {
        message.session_key = sessionKey;
    }
    const ACTIONS_WITH_ROOM = new Set([
        // 채팅/세션/히스토리 관련만 방 개념 적용
        'chat', 'get_history_snapshot', 'clear_history', 'get_history_settings', 'set_history_limit', 'get_narrative'
    ]);
    if (ACTIONS_WITH_ROOM.has(String(payload.action))) {
        if (currentRoom) {
            message.room_id = currentRoom;
        }
        // currentRoom이 없으면 room_id를 설정하지 않음 (서버가 처리)
    }
    if (!options.skipRetry && RETRY_ACTIONS.has(payload.action)) {
        lastRequest = message;
    }
    ws.send(JSON.stringify(message));
}

function initializeAppData() {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    sendMessage({ action: 'get_context' });
    sendMessage({ action: 'get_narrative' });
    sendMessage({ action: 'get_history_settings' });
    sendMessage({ action: 'get_session_settings' });
    // 서버에 저장된 방 목록 조회
    sendMessage({ action: 'room_list' });

    loadFileList('world', worldSelect);
    loadFileList('situation', situationSelect);
    loadFileList('my_character', myCharacterSelect);
    loadPresetList();
}

// ===== 채팅방 관리 =====
function sanitizeRoomName(name) {
    // 한글, 영문, 숫자, 공백, 밑줄, 하이픈 허용
    const sanitized = (name || '').trim().replace(/[^\uAC00-\uD7A3A-Za-z0-9_\-\s]/g, '_');
    return sanitized || 'room_untitled';
}

function persistRooms() {
    try {
        localStorage.setItem(ROOMS_KEY, JSON.stringify(rooms));
        localStorage.setItem(CURRENT_ROOM_KEY, currentRoom);
    } catch (_) {}
}

function renderRoomsUI() {
    if (!roomSelect) return;
    // 방 목록 반영
    roomSelect.innerHTML = '';

    // 빈 옵션 추가 (채팅방 선택 안내)
    const emptyOpt = document.createElement('option');
    emptyOpt.value = '';
    emptyOpt.textContent = '← 채팅방 선택 또는 추가';
    emptyOpt.disabled = true;
    roomSelect.appendChild(emptyOpt);

    (rooms || []).forEach(r => {
        const roomId = typeof r === 'string' ? r : (r.room_id || r.title || 'default');
        const title = (typeof r === 'object' && r.title) ? r.title : roomId;
        const opt = document.createElement('option');
        opt.value = roomId;
        opt.textContent = title;
        roomSelect.appendChild(opt);
    });

    const hasCurrent = currentRoom && (rooms || []).some(x => (typeof x === 'string' ? x : x.room_id) === currentRoom);
    if (!hasCurrent && rooms && rooms.length > 0) {
        // 방이 있지만 currentRoom이 없거나 유효하지 않으면 첫 번째 방 선택
        const firstRoom = rooms[0];
        const extractedId = typeof firstRoom === 'string' ? firstRoom : (firstRoom.room_id || null);
        if (extractedId) {
            currentRoom = extractedId;
        }
        // room_id가 없으면 currentRoom을 null로 유지
    }

    roomSelect.value = currentRoom || '';
    if (currentRoom) {
        announce(`채팅방 전환: ${currentRoom}`);
    }

    // 채팅 입력 상태 업데이트
    updateChatInputState();
}

function updateChatInputState() {
    refreshChatRefs(); // DOM 참조 갱신

    if (!currentRoom) {
        // 채팅방 미선택 - 입력 비활성화
        if (chatInput) {
            chatInput.disabled = true;
            chatInput.placeholder = '← 먼저 채팅방을 선택하거나 생성하세요';
        }
        if (sendChatBtn) {
            sendChatBtn.disabled = true;
        }

        // 환영 메시지 표시
        if (chatMessages) {
            chatMessages.innerHTML = `
                <div class="welcome-message" style="text-align: center; padding: 4rem 2rem; color: var(--text-muted, #888);">
                    <h2 style="margin-bottom: 1rem; color: var(--text-primary, #000);">Persona Chat에 오신 것을 환영합니다</h2>
                    <p style="margin-bottom: 2rem;">왼쪽 상단의 <strong>채팅</strong> 탭에서 새 채팅방을 만들어보세요.</p>
                    <div style="max-width: 500px; margin: 0 auto; text-align: left; line-height: 1.8;">
                        <p><strong>📌 시작 방법:</strong></p>
                        <ol style="padding-left: 1.5rem;">
                            <li>왼쪽 패널의 <strong>채팅</strong> 탭 클릭</li>
                            <li><strong>[+]</strong> 버튼으로 새 채팅방 생성</li>
                            <li><strong>캐릭터</strong> 탭에서 대화 상대 추가</li>
                            <li>대화 시작!</li>
                        </ol>
                    </div>
                </div>
            `;
        }
    } else {
        // 채팅방 선택됨 - 입력 활성화
        if (chatInput) {
            chatInput.disabled = false;
            chatInput.placeholder = '메시지를 입력하세요...';
        }
        if (sendChatBtn) {
            sendChatBtn.disabled = false;
        }
    }
}

function refreshRoomViews() {
    sendMessage({ action: 'get_narrative' });
    sendMessage({ action: 'get_history_settings' });
    sendMessage({ action: 'get_history_snapshot' });
}

if (roomSelect) {
    roomSelect.addEventListener('change', () => {
        const selectedValue = roomSelect.value;
        if (!selectedValue) {
            // 빈 옵션 선택됨 - 무시
            return;
        }
        currentRoom = selectedValue;
        persistRooms();
        // 방 설정 로드 시도
        sendMessage({ action: 'room_load', room_id: currentRoom });
        // 방 전환 시 해당 방의 프로바이더 세션 초기화(신규 프롬프트 적용)
        sendMessage({ action: 'reset_sessions', room_id: currentRoom });
        // 서사/히스토리 뷰 갱신
        refreshRoomViews();
        updateChatInputState(); // 입력 상태 업데이트
        log(`채팅방 전환: ${currentRoom}`, 'info');
        announce(`채팅방 전환: ${currentRoom}`);
    });
}
if (roomAddBtn) {
    roomAddBtn.addEventListener('click', () => {
        // 모달 열기
        roomNameInput.value = ''; // 입력 초기화
        roomNameModal.classList.remove('hidden');
        setTimeout(() => roomNameInput.focus(), 100); // 포커스
    });
}

// 채팅방 이름 모달 - 확인 버튼
if (roomNameConfirmBtn) {
    roomNameConfirmBtn.addEventListener('click', () => {
        const name = roomNameInput.value.trim();
        if (!name) {
            alert('채팅방 이름을 입력하세요.');
            return;
        }
        const r = sanitizeRoomName(name);
        if (!rooms.find(x => (typeof x === 'string' ? x : x.room_id) === r)) rooms.push(r);
        currentRoom = r;
        persistRooms();
        renderRoomsUI();
        // 현재 설정으로 방 저장
        const config = collectRoomConfig(r);
        console.log('[ROOM_SAVE] session_key:', sessionKey, 'room_id:', r, 'config:', config);
        sendMessage({ action: 'room_save', room_id: r, config });
        setTimeout(() => { sendMessage({ action: 'room_list' }); renderRoomsRightPanelList(); }, 300);
        refreshRoomViews();
        log(`채팅방 추가: ${r}`, 'success');
        announce(`채팅방 추가: ${r}`);

        // 새 채팅방으로 이동
        navigate(`/rooms/${encodeURIComponent(r)}`);

        // 모달 닫기
        roomNameModal.classList.add('hidden');
    });
}

// 채팅방 이름 모달 - 닫기 버튼들
if (roomNameCloseBtn) {
    roomNameCloseBtn.addEventListener('click', () => {
        roomNameModal.classList.add('hidden');
    });
}
if (roomNameCancelBtn) {
    roomNameCancelBtn.addEventListener('click', () => {
        roomNameModal.classList.add('hidden');
    });
}

// 채팅방 이름 모달 - Enter 키로 확인
if (roomNameInput) {
    roomNameInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.isComposing) {
            roomNameConfirmBtn?.click();
        }
    });
}
// roomDelBtn 제거됨 - 각 채팅방 옆에 개별 삭제 버튼으로 대체
if (roomSaveBtn) {
    roomSaveBtn.addEventListener('click', () => {
        if (!currentRoom) {
            alert('저장할 채팅방을 선택해주세요.');
            return;
        }
        const config = collectRoomConfig(currentRoom);
        sendMessage({ action: 'room_save', room_id: currentRoom, config });
        setTimeout(() => { sendMessage({ action: 'room_list' }); renderRoomsRightPanelList(); }, 300);
        log('채팅방 설정 저장 완료', 'success');
    });
}

// 방 설정 수집
function collectRoomConfig(roomId) {
    const userName = document.getElementById('userCharacterName').value.trim();
    const userGender = document.getElementById('userCharacterGender').value.trim();
    const userAge = (userCharacterAgeInput ? userCharacterAgeInput.value.trim() : '');
    const userDesc = userCharacterInput.value.trim();
    let userCharacterData = '';
    if (userName) {
        userCharacterData = `이름: ${userName}`;
        if (userGender) userCharacterData += `, 성별: ${userGender}`;
        if (userAge) userCharacterData += `, 나이: ${userAge}`;
        if (userDesc) userCharacterData += `\n${userDesc}`;
    } else if (userDesc) {
        userCharacterData = userDesc;
    }
    return {
        room_id: roomId,
        title: roomId,
        context: {
            world: worldInput.value.trim(),
            situation: situationInput.value.trim(),
            user_character: userCharacterData,
            narrator_enabled: !!narratorEnabled.checked,
            narrator_mode: narratorMode.value,
            narrator_description: narratorDescription.value.trim(),
            user_is_narrator: !!userIsNarrator.checked,
            ai_provider: aiProvider.value,
            adult_level: adultLevel.value,
            narrative_separation: !!narrativeSeparation.checked,
            narrator_drive: narratorDrive ? narratorDrive.value : 'guide',
            output_level: outputLevel ? outputLevel.value : 'normal',
            // 모델 및 세션 유지 설정을 방 컨텍스트에 포함
            model: (typeof modelSelect !== 'undefined' && modelSelect) ? modelSelect.value : '',
            session_retention: !!(typeof sessionRetentionToggle !== 'undefined' && sessionRetentionToggle && sessionRetentionToggle.checked),
            choice_policy: (forceChoices && forceChoices.checked) ? 'require' : 'off',
            choice_count: choiceCount ? parseInt(choiceCount.value, 10) || 3 : 3,
            characters: Array.isArray(participants) ? participants : []
        },
        user_profile: {
            name: userName,
            gender: userGender,
            age: userAge,
            description: userDesc
        }
    };
}

// ===== 맥락 길이 슬라이더 =====

function formatHistoryLimitLabel(limit) {
    return (limit === null || limit === undefined) ? '무제한' : `${limit}턴`;
}

function applyHistoryLimitUI(limit) {
    const unlimited = limit === null || limit === undefined;
    currentHistoryLimit = unlimited ? null : limit;

    if (historyLengthSlider) {
        if (!unlimited && typeof limit === 'number') {
            historyLengthSlider.value = limit;
        }
        historyLengthSlider.disabled = unlimited;
    }

    if (historyUnlimitedToggle) {
        historyUnlimitedToggle.checked = unlimited;
    }

    if (historyLengthValue) {
        historyLengthValue.textContent = formatHistoryLimitLabel(limit);
    }
}

function sendHistoryLimit(limit) {
    sendMessage({
        action: 'set_history_limit',
        max_turns: limit
    });
}

function setupHistoryControls() {
    if (historyLengthValue && historyLengthSlider) {
        historyLengthValue.textContent = formatHistoryLimitLabel(parseInt(historyLengthSlider.value, 10) || HISTORY_LIMIT_DEFAULT);
    }

    if (historyLengthSlider) {
        historyLengthSlider.addEventListener('input', () => {
            if (historyLengthValue && (!historyUnlimitedToggle || !historyUnlimitedToggle.checked)) {
                const value = parseInt(historyLengthSlider.value, 10) || HISTORY_LIMIT_DEFAULT;
                historyLengthValue.textContent = formatHistoryLimitLabel(value);
            }
        });

        historyLengthSlider.addEventListener('change', () => {
            if (historyUnlimitedToggle && historyUnlimitedToggle.checked) {
                return;
            }
            const value = parseInt(historyLengthSlider.value, 10) || HISTORY_LIMIT_DEFAULT;
            currentHistoryLimit = value;
            sendHistoryLimit(value);
        });
    }

    if (historyUnlimitedToggle) {
        historyUnlimitedToggle.addEventListener('change', () => {
            if (historyUnlimitedToggle.checked) {
                applyHistoryLimitUI(null);
                sendHistoryLimit(null);
            } else {
                const value = parseInt(historyLengthSlider?.value, 10) || HISTORY_LIMIT_DEFAULT;
                applyHistoryLimitUI(value);
                sendHistoryLimit(value);
            }
        });
    }
}

setupHistoryControls();

function applySessionRetentionUI(enabled) {
    if (sessionRetentionToggle) {
        sessionRetentionToggle.checked = !!enabled;
        sessionRetentionToggle.disabled = false;
        sessionRetentionToggle.parentElement?.classList.remove('disabled');
    }
    if (sessionStatusBadge) {
        const isOn = !!enabled;
        sessionStatusBadge.textContent = isOn ? 'ON' : 'OFF';
        sessionStatusBadge.classList.toggle('on', isOn);
    }
}

function setupSessionRetentionControls() {
    if (!sessionRetentionToggle) return;
    sessionRetentionToggle.addEventListener('change', () => {
        if (!sessionSettingsLoaded) return;
        sendMessage({
            action: 'set_session_retention',
            enabled: sessionRetentionToggle.checked
        });
    });
}

setupSessionRetentionControls();

function scheduleTokenRefresh() {
    if (tokenRefreshTimeout) {
        clearTimeout(tokenRefreshTimeout);
        tokenRefreshTimeout = null;
    }
    if (!authToken || !authTokenExpiresAt) {
        return;
    }
    const expiresAt = new Date(authTokenExpiresAt).getTime();
    if (Number.isNaN(expiresAt)) {
        return;
    }
    const now = Date.now();
    const safetyMs = 60 * 1000; // 60초 전에 갱신
    const delay = Math.max(expiresAt - now - safetyMs, 0);
    if (delay <= 0) {
        attemptTokenRefresh();
        return;
    }
    tokenRefreshTimeout = setTimeout(() => {
        attemptTokenRefresh();
    }, delay);
}

function attemptTokenRefresh() {
    if (!authToken || !authTokenExpiresAt) {
        return;
    }
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        if (refreshRetryCount >= MAX_REFRESH_RETRIES) {
            log('토큰 갱신 실패: 서버에 연결할 수 없습니다.', 'error');
            clearAuthToken();
            showLoginModal();
            return;
        }
        refreshRetryCount++;
        tokenRefreshTimeout = setTimeout(attemptTokenRefresh, 5000);
        return;
    }
    refreshRetryCount = 0;
    if (refreshToken) {
        sendMessage({ action: 'token_refresh', refresh_token: refreshToken }, { skipToken: true, skipRetry: true });
    } else {
        // HTTP API로 로그인 필요
        showLoginModal();
    }
}

// 오류 코드 → 사용자 메시지 매핑
function mapAuthError(code) {
    switch (code) {
        case 'invalid_username':
            return '아이디가 일치하지 않습니다.';
        case 'invalid_password':
            return '비밀번호가 일치하지 않습니다.';
        case 'rate_limited':
            return '로그인 시도가 너무 많습니다. 잠시 후 다시 시도하세요.';
        case 'missing_token':
        case 'token_expired':
            return '세션이 만료되었습니다. 다시 로그인하세요.';
        case 'invalid_token':
        case 'invalid_token_type':
            return '인증 정보가 유효하지 않습니다. 다시 로그인하세요.';
        case 'jwt_disabled':
            return '서버가 로그인 없이 동작 중입니다. 페이지를 새로 고침하세요.';
        default:
            return '';
    }
}

function showLoginModal() {
    if (!loginModal) return;
    loginModal.classList.remove('hidden');
    try {
        loginModal.setAttribute('role', 'dialog');
        loginModal.setAttribute('aria-modal', 'true');
        loginModal.setAttribute('aria-label', '로그인 대화상자');
    } catch (_) {}
    enableFocusTrap(loginModal);
    // 아이디/체크박스 초기화
    try {
        const savedUser = localStorage.getItem(LOGIN_USER_KEY) || '';
        if (loginUsernameInput) loginUsernameInput.value = savedUser;
        const auto = localStorage.getItem(LOGIN_AUTOLOGIN_KEY) === '1';
        if (rememberIdCheckbox) rememberIdCheckbox.checked = !!savedUser;
        if (autoLoginCheckbox) autoLoginCheckbox.checked = auto;
        if (adultConsent) adultConsent.checked = (localStorage.getItem(LOGIN_ADULT_KEY) === '1');
    } catch (_) {}
    if (loginPasswordInput) loginPasswordInput.value = '';
    loginError.textContent = '';
    chatInput.disabled = true;
    sendChatBtn.disabled = true;
    setTimeout(() => (loginUsernameInput?.value ? loginPasswordInput?.focus() : loginUsernameInput?.focus()), 100);
}

function hideLoginModal() {
    if (!loginModal) return;
    loginModal.classList.add('hidden');
    loginError.textContent = '';
    chatInput.disabled = false;
    sendChatBtn.disabled = false;
    disableFocusTrap(loginModal);
}

// 탭 전환
if (loginTab && registerTab && loginForm && registerForm) {
    loginTab.addEventListener('click', () => {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginTab.style.borderBottom = '3px solid #007bff';
        loginTab.style.color = '#007bff';
        registerTab.style.borderBottom = '3px solid transparent';
        registerTab.style.color = '#666';
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        loginError.textContent = '';
        registerError.textContent = '';
    });

    registerTab.addEventListener('click', () => {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        registerTab.style.borderBottom = '3px solid #007bff';
        registerTab.style.color = '#007bff';
        loginTab.style.borderBottom = '3px solid transparent';
        loginTab.style.color = '#666';
        registerForm.style.display = 'block';
        loginForm.style.display = 'none';
        loginError.textContent = '';
        registerError.textContent = '';
    });
}

// 회원가입
async function submitRegister() {
    const username = (registerUsernameInput?.value || '').trim();
    const email = (registerEmailInput?.value || '').trim();
    const password = registerPasswordInput?.value || '';
    const passwordConfirm = registerPasswordConfirmInput?.value || '';

    if (!username || !email || !password) {
        registerError.textContent = '모든 필드를 입력하세요.';
        return;
    }

    if (password.length < 8) {
        registerError.textContent = '비밀번호는 8자 이상이어야 합니다.';
        return;
    }

    if (password !== passwordConfirm) {
        registerError.textContent = '비밀번호가 일치하지 않습니다.';
        return;
    }

    try {
        registerButton.disabled = true;
        registerButton.textContent = '처리 중...';

        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            alert(`회원가입 성공! ${username}님, 환영합니다.`);
            // 로그인 탭으로 전환
            loginTab.click();
            loginUsernameInput.value = username;
            loginPasswordInput.value = password;
            registerUsernameInput.value = '';
            registerEmailInput.value = '';
            registerPasswordInput.value = '';
            registerPasswordConfirmInput.value = '';
        } else {
            registerError.textContent = data.error || '회원가입 실패';
        }
    } catch (error) {
        console.error('Register error:', error);
        registerError.textContent = '서버 오류가 발생했습니다.';
    } finally {
        registerButton.disabled = false;
        registerButton.textContent = '회원가입';
    }
}

// 로그인
async function submitLogin() {
    const username = (loginUsernameInput?.value || '').trim();
    const password = loginPasswordInput?.value || '';

    if (!username || !password) {
        loginError.textContent = '아이디와 비밀번호를 입력하세요.';
        return;
    }

    try {
        loginButton.disabled = true;
        loginButton.textContent = '로그인 중...';

        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // JWT 토큰 저장
            authToken = data.access_token;
            authTokenExpiresAt = data.access_exp;
            refreshToken = data.refresh_token;
            refreshTokenExpiresAt = data.refresh_exp;

            localStorage.setItem(AUTH_TOKEN_KEY, authToken);
            localStorage.setItem(AUTH_EXP_KEY, authTokenExpiresAt);
            localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
            localStorage.setItem(REFRESH_EXP_KEY, refreshTokenExpiresAt);

            // 사용자 역할 저장
            userRole = data.role || 'user';
            localStorage.setItem(USER_ROLE_KEY, userRole);

            // 관리자 버튼 표시/숨김
            if (adminBtn) {
                adminBtn.style.display = (userRole === 'admin') ? 'block' : 'none';
            }

            // 아이디 저장
            if (rememberIdCheckbox?.checked) {
                localStorage.setItem(LOGIN_USER_KEY, username);
            } else {
                localStorage.removeItem(LOGIN_USER_KEY);
            }

            // 자동 로그인 설정
            if (autoLoginCheckbox?.checked) {
                localStorage.setItem(LOGIN_AUTOLOGIN_KEY, '1');
                localStorage.setItem(LOGIN_SAVED_PW_KEY, password);
            } else {
                localStorage.removeItem(LOGIN_AUTOLOGIN_KEY);
                localStorage.removeItem(LOGIN_SAVED_PW_KEY);
            }

            isAuthenticated = true;
            hideLoginModal();
            log(`${username}님 로그인 성공`, 'success');

            // 버튼 가시성 업데이트 (헤더 + 더보기 메뉴)
            loginBtn.style.display = 'none';
            moreLoginBtn.style.display = 'none';
            logoutBtn.style.display = 'block';
            moreLogoutBtn.style.display = 'block';
            if (userRole === 'admin') {
                adminBtn.style.display = 'block';
                moreAdminBtn.style.display = 'block';
            }
            console.log('[LOGIN] 버튼 가시성:', { loginBtn: loginBtn.style.display, logoutBtn: logoutBtn.style.display, adminBtn: adminBtn.style.display, userRole });

            // WebSocket 재연결 (토큰 포함)
            if (ws && ws.readyState === WebSocket.OPEN) {
                isReconnecting = true; // 의도적인 재연결 표시
                ws.close();
            }
            connect();
        } else {
            loginError.textContent = data.error || '로그인 실패';
        }
    } catch (error) {
        console.error('Login error:', error);
        loginError.textContent = '서버 오류가 발생했습니다.';
    } finally {
        loginButton.disabled = false;
        loginButton.textContent = '로그인';
    }
}

if (registerButton) {
    registerButton.addEventListener('click', submitRegister);
}
if (registerPasswordConfirmInput) {
    registerPasswordConfirmInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            submitRegister();
        }
    });
}
if (loginButton) {
    loginButton.addEventListener('click', submitLogin);
}
if (loginPasswordInput) {
    loginPasswordInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            submitLogin();
        }
    });
}

// 메시지 처리
function handleMessage(msg) {
    const { action, data } = msg;

    switch (action) {
        case 'connected': {
            log('서버 연결 완료', 'success');
            const requiresLogin = Boolean(data && data.login_required);
            appConfig.login_required = requiresLogin;
            if (requiresLogin) {
                authRequired = true;
                if (authToken) {
                    isAuthenticated = true;
                    hideLoginModal();
                    resumePendingRoute();
                    initializeAppData();
                } else {
                    isAuthenticated = false;
                    showLoginModal();
                }
            } else {
                authRequired = false;
                isAuthenticated = true;
                hideLoginModal();
                resumePendingRoute();
                initializeAppData();
            }
            break;
        }

        case 'auth_required':
            authRequired = true;
            isAuthenticated = false;
            if (appConfig.login_required) {
                rememberPendingRoute(location.pathname);
            }
            // refresh 토큰으로 자동 갱신 시도
            if (!refreshInProgress && refreshToken) {
                refreshInProgress = true;
                sendMessage({ action: 'token_refresh', refresh_token: refreshToken }, { skipToken: true, skipRetry: true });
                log('토큰 갱신 시도 중...', 'info');
            } else {
                clearAuthToken();
                setRefreshToken('', '');
                showLoginModal();
                const reason = (data && data.reason) ? String(data.reason) : '';
                const msg = mapAuthError(reason) || '로그인이 필요합니다';
                if (loginError) loginError.textContent = msg;
                log(msg, 'warning');
            }
            break;

        case 'login':
            if (data.success) {
                authRequired = false;
                isAuthenticated = true;
                hideLoginModal();
                refreshRetryCount = 0;
                if (data.token) {
                    setAuthToken(data.token, data.expires_at);
                }
                if (data.refresh_token) {
                    setRefreshToken(data.refresh_token, data.refresh_expires_at);
                }
                if (data.session_key) {
                    sessionKey = data.session_key;
                    try { localStorage.setItem(SESSION_KEY_KEY, sessionKey); } catch (_) {}
                }
                const handshakeOnly = !appConfig.login_required && !data.token && !data.refresh_token;
                log(handshakeOnly ? '세션 키 동기화 완료' : '로그인 성공', 'success');
                // 아이디/자동로그인 저장
                try {
                    const user = (loginUsernameInput?.value || '').trim();
                    if (rememberIdCheckbox?.checked && user) {
                        localStorage.setItem(LOGIN_USER_KEY, user);
                    } else {
                        localStorage.removeItem(LOGIN_USER_KEY);
                    }
                    if (autoLoginCheckbox?.checked) {
                        localStorage.setItem(LOGIN_AUTOLOGIN_KEY, '1');
                        const pw = (loginPasswordInput?.value || '').trim();
                        if (pw) localStorage.setItem(LOGIN_SAVED_PW_KEY, pw);
                    } else {
                        localStorage.removeItem(LOGIN_AUTOLOGIN_KEY);
                        localStorage.removeItem(LOGIN_SAVED_PW_KEY);
                    }
                    // 성인 동의 저장(선택)
                    if (adultConsent && adultConsent.checked) {
                        localStorage.setItem(LOGIN_ADULT_KEY, '1');
                    }
                } catch (_) {}
                // 직전 사용자 액션이 있었다면 우선 재전송
                if (lastRequest) {
                    const payload = { ...lastRequest };
                    sendMessage(payload, { skipRetry: true });
                    lastRequest = null;
                }
                if (appConfig.login_required || data.token || data.refresh_token) {
                    initializeAppData();
                }
                resumePendingRoute();
            } else {
                const errorMsg = mapAuthError(data.code) || data.error || '로그인에 실패했습니다.';
                clearAuthToken();
                setRefreshToken('', '');
                showLoginModal();
                loginError.textContent = errorMsg;
                log(`로그인 실패: ${errorMsg}`, 'error');
            }
            break;

        case 'token_refresh':
            refreshInProgress = false;
            if (data.success) {
                if (data.token) setAuthToken(data.token, data.expires_at);
                if (data.refresh_token) setRefreshToken(data.refresh_token, data.refresh_expires_at);
                log('토큰 갱신 완료', 'success');
                if (lastRequest) {
                    const payload = { ...lastRequest };
                    sendMessage(payload, { skipRetry: true });
                    lastRequest = null;
                } else {
                    initializeAppData();
                }
            } else {
                clearAuthToken();
                setRefreshToken('', '');
                showLoginModal();
                log(`토큰 갱신 실패: ${data.error || '오류'}`, 'error');
            }
            break;

        case 'get_context':
            if (data.success) {
                loadContext(data.context);
                applyContextToSettingsScreen(data.context);
            }
            break;

        case 'set_context':
            if (data.success) {
                log('컨텍스트 저장 완료', 'success');
                if (saveContextBtn) saveContextBtn.disabled = false;
                if (pendingConsentResend && lastRequest) {
                    const payload = { ...lastRequest };
                    pendingConsentResend = false;
                    sendMessage(payload, { skipRetry: true });
                }
            }
            break;

        case 'clear_history':
            if (data.success) {
                log('대화 히스토리 초기화 완료', 'success');
                // 채팅 메시지 지우기
                chatMessages.innerHTML = '<div class="chat-message system"><p>대화를 시작하세요</p></div>';
                // 서사 초기화
                narrativeContent.innerHTML = '<p class="placeholder">대화가 진행되면 여기에 서사가 기록됩니다.</p>';
            }
            break;

        case 'get_narrative':
            if (data.success) {
                updateNarrative(data.markdown);
            }
            break;

        case 'get_history_settings':
            if (data.success) {
                applyHistoryLimitUI(data.max_turns);
            }
            break;

        case 'set_history_limit':
            if (data.success) {
                applyHistoryLimitUI(data.max_turns);
                log(`맥락 길이가 ${formatHistoryLimitLabel(data.max_turns)}로 설정되었습니다.`, 'success');
            } else {
                const errorMsg = data.error || '맥락 길이 설정에 실패했습니다.';
                log(errorMsg, 'error');
                sendMessage({ action: 'get_history_settings' });
            }
            break;

        case 'get_session_settings':
            if (data.success) {
                applySessionRetentionUI(data.retention_enabled);
                sessionSettingsLoaded = true;
            }
            break;

        case 'set_session_retention':
            if (data.success) {
                sessionSettingsLoaded = true;
                applySessionRetentionUI(data.retention_enabled);
                const stateText = data.retention_enabled ? 'ON' : 'OFF';
                log(`세션 유지가 ${stateText} 상태로 설정되었습니다.`, 'success');
            } else {
                log(data.error || '세션 유지 설정에 실패했습니다.', 'error');
                sendMessage({ action: 'get_session_settings' });
            }
            break;

        case 'consent_required': {
            // 정책 변경: 로그인 시 자동 동의로 처리 → 즉시 동의 설정
            pendingConsentResend = true;
            sendMessage({ action: 'set_context', adult_consent: true });
            break;
        }

        case 'reset_sessions':
            if (data.success) {
                log(data.message || 'AI 세션이 초기화되었습니다.', 'success');
            } else {
                log(data.error || '세션 초기화에 실패했습니다.', 'error');
            }
            break;

        case 'chat_stream':
            handleChatStream(data);
            break;

        case 'chat_complete':
            handleChatComplete(data);
            break;

        case 'list_workspace_files':
            if (data.success) {
                handleFileList(data);
            } else {
                log(`파일 목록 로드 실패: ${data.error}`, 'error');
            }
            break;

        case 'room_list':
            if (data.success) {
                rooms = data.rooms || [];
                try { localStorage.setItem(ROOMS_KEY, JSON.stringify(rooms)); } catch (_) {}
                renderRoomsUI();
                renderRoomsRightPanelList();
            } else {
                log(`방 목록 로드 실패: ${data.error}`, 'error');
            }
            break;

        case 'room_save':
            if (data.success) {
                log('방 설정 저장 완료', 'success');
                sendMessage({ action: 'room_list' });
            } else {
                log(`방 저장 실패: ${data.error}`, 'error');
            }
            break;

        case 'room_load':
            if (data.success) {
                const room = data.room || {};
                const ctx = room.context || {};
                // UI 반영
                loadContext(ctx);
                // 서버에서 전달한 히스토리가 있으면 메시지 화면에 즉시 렌더
                try {
                    if (Array.isArray(room.history) && room.history.length > 0) {
                        renderHistorySnapshot(room.history);
                    }
                } catch (_) {}
                // 사용자 프로필 필드 채움
                try {
                    const prof = room.user_profile || {};
                    const nameEl = document.getElementById('userCharacterName');
                    const genderEl = document.getElementById('userCharacterGender');
                    const ageEl = document.getElementById('userCharacterAge');
                    if (nameEl) nameEl.value = prof.name || '';
                    if (genderEl) genderEl.value = prof.gender || '';
                    if (ageEl) ageEl.value = prof.age || '';
                    if (prof.description && (!ctx.user_character || !ctx.user_character.includes(prof.description))) {
                        userCharacterInput.value = prof.description;
                    }
                } catch (_) {}
                // 서버 컨텍스트에 적용 (서버에서 이미 ContextHandler에 적용했지만, 일관성을 위해 호출)
                // 주의: room_id 포함하여 해당 채팅방 설정으로 저장되도록 함
                // sendMessage({ action: 'set_context', room_id: room.room_id, ...ctx });
                // → 서버에서 이미 적용했으므로 생략 (중복 호출 방지)
                log('방 설정 로드 완료', 'success');
            } else {
                log(`방 로드 실패: ${data.error}`, 'error');
            }
            break;

        case 'room_delete':
            if (data.success) {
                sendMessage({ action: 'room_list' });
                log('방 삭제 완료(설정)', 'success');
            } else {
                log(`방 삭제 실패: ${data.error}`, 'error');
            }
            break;

        case 'save_workspace_file':
            if (data.success) {
                log(`파일 저장 완료: ${data.filename}`, 'success');
                // 목록 새로고침은 handleFileList에서 처리
            } else {
                log(`파일 저장 실패: ${data.error}`, 'error');
            }
            break;

        case 'load_workspace_file':
            if (data.success) {
                handleFileLoad(data);
                log(`파일 로드 완료: ${data.filename}`, 'success');
            } else {
                log(`파일 로드 실패: ${data.error}`, 'error');
            }
            break;

        case 'delete_workspace_file':
            if (data.success) {
                log(`파일 삭제 완료: ${data.filename}`, 'success');
                // 목록 새로고침은 handleFileList에서 처리
            } else {
                log(`파일 삭제 실패: ${data.error}`, 'error');
            }
            break;

        case 'list_presets':
            if (data.success) {
                updatePresetList(data.files);
            } else {
                log(`프리셋 목록 로드 실패: ${data.error}`, 'error');
            }
            break;

        case 'save_preset':
            if (data.success) {
                log(`프리셋 저장 완료: ${data.filename}`, 'success');
                loadPresetList();
            } else {
                log(`프리셋 저장 실패: ${data.error}`, 'error');
            }
            break;

        case 'load_preset':
            if (data.success) {
                applyPreset(data.preset);
                log(`프리셋 로드 완료: ${data.filename}`, 'success');
            } else {
                log(`프리셋 로드 실패: ${data.error}`, 'error');
            }
            break;

        case 'delete_preset':
            if (data.success) {
                log(`프리셋 삭제 완료: ${data.filename}`, 'success');
                loadPresetList();
            } else {
                log(`프리셋 삭제 실패: ${data.error}`, 'error');
            }
            break;

        // 모드 전환 관련 메시지 제거됨

        case 'list_stories':
        case 'save_story':
        case 'load_story':
        case 'delete_story':
        case 'resume_from_story':
            log('스토리 파일 기능은 비활성화되었습니다(히스토리 화면에서 확인하세요).', 'info');
            break;

        case 'get_history_snapshot':
            if (data.success) {
                renderHistorySnapshot(data.history || []);
                renderHistorySnapshotScreen(data.history || []);
            } else {
                log(`스냅샷 로드 실패: ${data.error}`, 'error');
            }
            break;

        case 'error':
            log(`에러: ${data.error}`, 'error');
            break;
    }
}

// ===== 채팅 기능 =====

function addChatMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = new Date().toLocaleTimeString();

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeSpan);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}

function addTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message assistant';
    messageDiv.id = 'typingIndicator';

    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';

    messageDiv.appendChild(typingDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

function sendChatMessage() {
    const prompt = chatInput.value.trim();

    if (!prompt) return;
    if (authRequired && !isAuthenticated) {
        log('로그인 후 이용 가능합니다.', 'error');
        return;
    }

    if (ws && ws.readyState === WebSocket.OPEN) {
        // 사용자 메시지 표시
        addChatMessage('user', prompt);

        // 입력 필드 초기화
        chatInput.value = '';
        chatInput.disabled = true;
        sendChatBtn.disabled = true;

        // 타이핑 인디케이터 표시
        addTypingIndicator();

        // 선택된 프로바이더 확인 및 저장
        const provider = (aiProvider && aiProvider.value) ? aiProvider.value : 'claude';
        currentProvider = provider;

        // 서버로 전송(프로바이더 명시)
        sendMessage({
            action: 'chat',
            prompt: prompt,
            provider: provider,
            model: (modelSelect && modelSelect.value) ? modelSelect.value : ''
        });

        const providerLabel = provider === 'gemini' ? 'Gemini' : (provider === 'droid' ? 'Droid' : 'Claude');
        const shortPrompt = prompt.length > 50 ? prompt.slice(0, 50) + '...' : prompt;
        log(`${providerLabel}에게 메시지 전송: ${shortPrompt}`);
    } else {
        log('WebSocket 연결이 끊어졌습니다', 'error');
    }
}

function handleChatStream(data) {
    const jsonData = data;

    if (jsonData.type === 'system' && jsonData.subtype === 'init') {
        log('Claude Code 세션 시작', 'success');
        return;
    }

    // Droid 세션 시작
    if (jsonData.type === 'system' && jsonData.subtype === 'droid_init' && jsonData.session_id) {
        log('Droid 세션 시작', 'success');
        return;
    }

    // Gemini 세션 시작
    if (jsonData.type === 'system' && jsonData.subtype === 'gemini_init' && jsonData.session_id) {
        log('Gemini 세션 시작', 'success');
        return;
    }

    // Droid/Gemini content_block_delta 처리
    if (jsonData.type === 'content_block_delta') {
        removeTypingIndicator();

        const deltaText = jsonData.delta?.text || '';
        if (deltaText) {
            // 스트리밍 텍스트 누적
            if (!window.streamingText) {
                window.streamingText = '';
            }
            window.streamingText += deltaText;
        }
        return;
    }

    // (폴백 제거됨)

    if (jsonData.type === 'assistant') {
        removeTypingIndicator();

        const message = jsonData.message;
        const content = message.content || [];

        let textContent = '';
        for (const item of content) {
            if (item.type === 'text') {
                textContent += item.text;
            }
        }

        if (textContent) {
            // 디버깅: 원본 응답 출력
            console.log('=== Claude 응답 원본 ===');
            console.log(textContent);

            // 멀티 캐릭터 파싱 시도
            const parsedMessages = parseMultiCharacterResponse(textContent);

            // 디버깅: 파싱 결과 출력
            console.log('=== 파싱 결과 ===');
            console.log('파싱된 메시지 수:', parsedMessages.length);
            console.log('파싱된 메시지:', parsedMessages);

            if (parsedMessages.length > 0) {
                // 기존 assistant 메시지 제거 (스트리밍 업데이트)
                const existingMsgs = chatMessages.querySelectorAll('.chat-message.assistant:not(#typingIndicator)');
                existingMsgs.forEach(msg => {
                    if (!msg.dataset.permanent) {
                        msg.remove();
                    }
                });

                // 파싱된 메시지들 표시
                parsedMessages.forEach(msg => {
                    const newMsg = addCharacterMessage(msg.character, msg.text);
                    newMsg.dataset.permanent = 'false'; // 스트리밍 중에는 업데이트 가능
                });
            } else {
                // 파싱 실패 시 일반 메시지로 표시
                if (!currentAssistantMessage) {
                    currentAssistantMessage = addChatMessage('assistant', textContent);
                } else {
                    const contentDiv = currentAssistantMessage.querySelector('.message-content');
                    if (contentDiv) {
                        contentDiv.textContent = textContent;
                    }
                }
            }
        }
    }

    if (jsonData.type === 'result') {
        const label = currentProvider === 'gemini' ? 'Gemini' : (currentProvider === 'droid' ? 'Droid' : 'Claude');
        log(`${label} 응답 완료`, 'success');
        // 스트리밍 완료 시 메시지 고정
        chatMessages.querySelectorAll('.chat-message.assistant').forEach(msg => {
            msg.dataset.permanent = 'true';
        });
    }
}

function handleChatComplete(response) {
    removeTypingIndicator();
    currentAssistantMessage = null;

    // 입력 필드 활성화
    chatInput.disabled = false;
    sendChatBtn.disabled = false;
    chatInput.focus();

    // response.data가 실제 데이터
    const data = response.data || response;

    if (data.success) {
        const used = data.provider_used || currentProvider || 'claude';
        const label = used === 'gemini' ? 'Gemini' : (used === 'droid' ? 'Droid' : 'Claude');
        log(`${label} 응답 완료`, 'success');

        // Droid/Gemini: 누적된 스트리밍 텍스트 처리
        if (window.streamingText) {
            console.log('=== Droid/Gemini 응답 원본 ===');
            console.log(window.streamingText);

            const parsedMessages = parseMultiCharacterResponse(window.streamingText);
            console.log('=== 파싱 결과 ===');
            console.log('파싱된 메시지 수:', parsedMessages.length);
            console.log('파싱된 메시지:', parsedMessages);

            if (parsedMessages.length > 0) {
                // 파싱된 메시지들 표시
                parsedMessages.forEach(msg => {
                    const newMsg = addCharacterMessage(msg.character, msg.text);
                    newMsg.dataset.permanent = 'true'; // 완료된 메시지
                });
            } else {
                // 파싱 실패 시 일반 메시지로 표시
                addChatMessage('assistant', window.streamingText);
            }

            // 스트리밍 텍스트 초기화
            window.streamingText = '';
        }

        // 토큰 사용량 업데이트
        console.log('Token usage:', data.token_usage); // 디버그
        if (data.token_usage) {
            updateTokenDisplay(data.token_usage);
        }

        // 서사 업데이트
        sendMessage({ action: 'get_narrative' });
    } else {
        log('채팅 에러: ' + data.error, 'error');
        addChatMessage('system', '에러: ' + data.error);
    }
}

// ===== 멀티 캐릭터 응답 파싱 =====

function parseMultiCharacterResponse(text) {
    const messages = [];
    const matches = [...text.matchAll(/\[([^\]]+)\]:?/g)];

    if (matches.length === 0) {
        return messages;
    }

    for (let i = 0; i < matches.length; i++) {
        const match = matches[i];
        const character = match[1].trim();
        const start = match.index + match[0].length;
        const end = i + 1 < matches.length ? matches[i + 1].index : text.length;
        const content = text.slice(start, end).trim();

        if (character && content) {
            messages.push({
                character,
                text: content
            });
        }
    }

    return messages;
}

function getCharacterColor(characterName) {
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

function addCharacterMessage(characterName, text) {
    const messageDiv = document.createElement('div');

    // 진행자인 경우 특별한 스타일 적용
    if (characterName === '진행자') {
        messageDiv.className = 'chat-message assistant narrator';
    } else {
        const colorClass = getCharacterColor(characterName);
        messageDiv.className = `chat-message assistant ${colorClass}`;
    }

    const charNameDiv = document.createElement('div');
    charNameDiv.className = 'character-name';
    charNameDiv.textContent = characterName;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // 효과음 자동 줄바꿈 처리
    // *...* 패턴 앞뒤로 줄바꿈 추가
    const formattedText = text
        .replace(/(\*[^*]+\*)/g, '\n$1\n')  // 효과음 앞뒤 줄바꿈
        .replace(/\n{3,}/g, '\n\n')  // 연속된 줄바꿈 최대 2개로 제한
        .trim();

    contentDiv.textContent = formattedText;

    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = new Date().toLocaleTimeString();

    messageDiv.appendChild(charNameDiv);
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeSpan);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}

// ===== 컨텍스트 관리 =====

// 진행자 활성화 토글
narratorEnabled.addEventListener('change', () => {
    if (narratorEnabled.checked) {
        narratorSettings.style.display = 'block';
        // AI 진행자가 활성화되면 사용자 진행자 비활성화
        userIsNarrator.checked = false;
    } else {
        narratorSettings.style.display = 'none';
    }
});

// 사용자 진행자 토글
userIsNarrator.addEventListener('change', () => {
    if (userIsNarrator.checked) {
        // 사용자가 진행자면 AI 진행자 비활성화
        narratorEnabled.checked = false;
        narratorSettings.style.display = 'none';
    }
});

// 캐릭터 추가: 빠른 편집 모달로 바로 열기(설정 화면 열지 않음)
addCharacterBtn.addEventListener('click', () => {
    openParticipantEditor(-1);
});

function addCharacterInput(name = '', gender = '', description = '', age = '') {
    const characterDiv = document.createElement('div');
    characterDiv.className = 'character-item';

    const header = document.createElement('div');
    header.className = 'character-item-header';

    // 요약/버튼 영역
    const controls = document.createElement('div');
    controls.style.display = 'flex';
    controls.style.gap = '0.25rem';
    controls.style.alignItems = 'center';
    controls.style.justifyContent = 'flex-end';

    const editBtn = document.createElement('button');
    editBtn.className = 'btn btn-sm';
    editBtn.textContent = '✏️ 편집';
    editBtn.title = '캐릭터 편집';
    editBtn.onclick = () => openCharacterEditor(characterDiv);

    const removeBtn = document.createElement('button');
    removeBtn.className = 'btn btn-sm';
    removeBtn.textContent = '❌';
    removeBtn.title = '제거';
    removeBtn.onclick = () => characterDiv.remove();

    controls.appendChild(editBtn);
    controls.appendChild(removeBtn);
    header.appendChild(controls);

    // 이름 필드
    const nameRow = document.createElement('div');
    nameRow.style.marginBottom = '0.5rem';

    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.className = 'character-name-input character-name-field';
    nameInput.placeholder = '이름';
    nameInput.value = name;
    nameInput.style.width = '100%';

    nameRow.appendChild(nameInput);

    // 성별 필드
    const genderRow = document.createElement('div');
    genderRow.style.marginBottom = '0.5rem';

    const genderSelect = document.createElement('select');
    genderSelect.className = 'character-gender-input character-gender-field';
    genderSelect.style.width = '100%';
    genderSelect.innerHTML = `
        <option value="">성별</option>
        <option value="남성">남성</option>
        <option value="여성">여성</option>
        <option value="기타">기타</option>
    `;
    genderSelect.value = gender;

    genderRow.appendChild(genderSelect);

    // 나이 필드
    const ageRow = document.createElement('div');
    ageRow.style.marginBottom = '0.5rem';
    const ageInput = document.createElement('input');
    ageInput.type = 'text';
    ageInput.className = 'character-age-input character-age-field';
    ageInput.placeholder = '나이(숫자 또는 예: 20대)';
    ageInput.value = age;
    ageInput.style.width = '100%';
    ageRow.appendChild(ageInput);

    const descTextarea = document.createElement('textarea');
    descTextarea.className = 'character-description-input';
    descTextarea.placeholder = '성격, 말투, 배경, 외모 등...';
    descTextarea.value = description;

    // 표시용 요약 바
    const summaryBar = document.createElement('div');
    summaryBar.className = 'character-summary';
    summaryBar.style.fontSize = '0.9rem';
    summaryBar.style.color = '#475569';
    summaryBar.style.margin = '0.25rem 0 0.5rem 0';

    function updateSummary() {
        const nm = nameInput.value || '이름 없음';
        const gd = genderSelect.value || '-';
        const ag = ageInput.value || '-';
        const snip = (descTextarea.value || '').slice(0, 40).replace(/\n/g, ' ');
        summaryBar.textContent = `${nm} · ${gd} · ${ag} — ${snip}`;
    }

    // 내부 입력은 모달 전용 저장소로만 쓰고 숨김
    nameRow.style.display = 'none';
    genderRow.style.display = 'none';
    ageRow.style.display = 'none';
    descTextarea.style.display = 'none';

    characterDiv.appendChild(header);
    characterDiv.appendChild(summaryBar);
    characterDiv.appendChild(nameRow);
    characterDiv.appendChild(genderRow);
    characterDiv.appendChild(ageRow);
    characterDiv.appendChild(descTextarea);
    charactersList.appendChild(characterDiv);

    updateSummary();
    // 요약은 값 변경 시 갱신되도록 이벤트 연결
    [nameInput, genderSelect, ageInput, descTextarea].forEach(el => {
        el.addEventListener('input', updateSummary);
        el.addEventListener('change', updateSummary);
    });
}

// 템플릿 목록 로드
function loadCharTemplateList(selectElement) {
    sendMessage({ action: 'list_workspace_files', file_type: 'char_template' });
    window.pendingTemplateSelect = selectElement;
}

// 캐릭터 템플릿 저장(JSON)
// 편집 모달 내 템플릿 저장에서 사용
function saveCharacterTemplateFromModal() {
    const name = document.getElementById('ceName').value.trim();
    const gender = document.getElementById('ceGender').value.trim();
    const age = document.getElementById('ceAge').value.trim();
    const summary = document.getElementById('ceSummary').value.trim();
    const traits = document.getElementById('ceTraits').value.trim();
    const goals = document.getElementById('ceGoals').value.trim();
    const boundaries = document.getElementById('ceBoundaries').value.trim();
    const examples = document.getElementById('ceExamples').value.trim().split('\n').filter(Boolean);
    const tags = document.getElementById('ceTags').value.split(',').map(s => s.trim()).filter(Boolean);
    if (!name) { alert('이름을 입력하세요'); return; }
    const filename = prompt('템플릿 파일명(확장자 제외):', slugify(name));
    if (!filename) return;
    const payload = { name, role: 'npc', gender, age, summary, traits, goals, boundaries, examples, tags };
    sendMessage({ action: 'save_workspace_file', file_type: 'char_template', filename, content: JSON.stringify(payload, null, 2) });
    // 모달의 템플릿 목록 갱신
    setTimeout(() => {
        const sel = document.getElementById('ceTemplateSelect');
        if (sel) loadCharTemplateList(sel);
    }, 500);
}

function slugify(str) {
    return (str || '')
        .toLowerCase()
        .replace(/\s+/g, '-')
        .replace(/[^a-z0-9\-]/g, '')
        .replace(/\-+/g, '-')
        .replace(/^\-+|\-+$/g, '') || 'character';
}

function composeDescription(base, gender, age, traits, goals, boundaries, examples, tags, includeMeta = true) {
    const lines = [];
    if (includeMeta) {
        const meta = [];
        if (gender) meta.push(`성별: ${gender}`);
        if (age) meta.push(`나이: ${age}`);
        if (meta.length) lines.push(meta.join(', '));
    }
    if (base) lines.push(base);
    if (traits) lines.push(`성격: ${traits}`);
    if (goals) lines.push(`목표: ${goals}`);
    if (boundaries) lines.push(`금지선: ${boundaries}`);
    if (Array.isArray(examples) && examples.length) {
        lines.push('예시 대사:');
        examples.forEach(e => lines.push(`- ${e}`));
    }
    if (tags) lines.push(`태그: ${tags}`);
    return lines.join('\n');
}

function collectCharacterFromItem(item) {
    const name = item.querySelector('.character-name-input').value.trim();
    const gender = item.querySelector('.character-gender-input').value.trim();
    const age = item.querySelector('.character-age-input').value.trim();
    const base = item.querySelector('.character-description-input').value.trim();
    if (!name || !base) return null;
    const traits = (item.dataset.traits || '').trim();
    const goals = (item.dataset.goals || '').trim();
    const boundaries = (item.dataset.boundaries || '').trim();
    const tags = (item.dataset.tags || '').trim();
    let examples = [];
    try { examples = JSON.parse(item.dataset.examples || '[]'); } catch (_) { examples = []; }
    const description = composeDescription(base, gender, age, traits, goals, boundaries, examples, tags, false);
    const obj = { name, gender, description };
    if (age) obj.age = age;
    return obj;
}

// 컨텍스트 저장
saveContextBtn.addEventListener('click', () => {
    if (!currentRoom) {
        alert('설정을 저장할 채팅방을 선택해주세요.');
        return;
    }

    if (saveContextBtn) saveContextBtn.disabled = true;
    const characters = Array.isArray(participants) ? participants : [];

    // 사용자 캐릭터 정보 수집
    const userName = document.getElementById('userCharacterName').value.trim();
    const userGender = document.getElementById('userCharacterGender').value.trim();
    const userDesc = userCharacterInput.value.trim();
    const userAge = (userCharacterAgeInput ? userCharacterAgeInput.value.trim() : '');

    // 사용자 캐릭터 정보를 하나의 문자열로 결합
    let userCharacterData = '';
    if (userName) {
        userCharacterData = `이름: ${userName}`;
        if (userGender) userCharacterData += `, 성별: ${userGender}`;
        if (userAge) userCharacterData += `, 나이: ${userAge}`;
        if (userDesc) userCharacterData += `\n${userDesc}`;
    } else if (userDesc) {
        userCharacterData = userDesc;
    }

    sendMessage({
        action: 'set_context',
        room_id: currentRoom,  // 채팅방별 독립 설정
        world: worldInput.value.trim(),
        situation: situationInput.value.trim(),
        user_character: userCharacterData,
        narrator_enabled: narratorEnabled.checked,
        narrator_mode: narratorMode.value,
        narrator_description: narratorDescription.value.trim(),
        user_is_narrator: userIsNarrator.checked,
        ai_provider: aiProvider.value,
        adult_level: adultLevel.value,
        adult_consent: adultConsent ? !!adultConsent.checked : undefined,
        narrative_separation: narrativeSeparation.checked,
        narrator_drive: narratorDrive ? narratorDrive.value : undefined,
        output_level: outputLevel ? outputLevel.value : undefined,
        characters: characters,
        choice_policy: (forceChoices && forceChoices.checked) ? 'require' : 'off',
        choice_count: choiceCount ? parseInt(choiceCount.value, 10) || 3 : undefined
    });
    // 방 설정도 함께 저장(room.json)
    try {
        const config = collectRoomConfig(currentRoom);
        sendMessage({ action: 'room_save', room_id: currentRoom, config });
    } catch (_) {}
    // 설정 적용 시 설정 모달 닫기
    try {
        const modal = document.getElementById('settingsModal');
        modal?.classList.add('hidden');
    } catch (_) {}
    setTimeout(() => { if (saveContextBtn) saveContextBtn.disabled = false; }, 5000);
});

// 캐릭터 적용 (왼쪽 패널용)
if (applyCharactersBtn) {
    applyCharactersBtn.addEventListener('click', () => {
        applyCharactersBtn.disabled = true;
        const characters = Array.isArray(participants) ? participants : [];

        // 사용자 캐릭터 정보 수집
        const userName = document.getElementById('userCharacterName').value.trim();
        const userGender = document.getElementById('userCharacterGender').value.trim();
        const userDesc = userCharacterInput.value.trim();
        const userAge = (userCharacterAgeInput ? userCharacterAgeInput.value.trim() : '');

        // 사용자 캐릭터 정보를 하나의 문자열로 결합
        let userCharacterData = '';
        if (userName) {
            userCharacterData = `이름: ${userName}`;
            if (userGender) userCharacterData += `, 성별: ${userGender}`;
            if (userAge) userCharacterData += `, 나이: ${userAge}`;
            if (userDesc) userCharacterData += `\n${userDesc}`;
        } else if (userDesc) {
            userCharacterData = userDesc;
        }

        sendMessage({
            action: 'set_context',
            world: worldInput.value.trim(),
            situation: situationInput.value.trim(),
            user_character: userCharacterData,
            narrator_enabled: narratorEnabled.checked,
            narrator_mode: narratorMode.value,
            narrator_description: narratorDescription.value.trim(),
            user_is_narrator: userIsNarrator.checked,
            ai_provider: aiProvider.value,
            adult_level: adultLevel.value,
            adult_consent: adultConsent ? !!adultConsent.checked : undefined,
            narrative_separation: narrativeSeparation.checked,
            narrator_drive: narratorDrive ? narratorDrive.value : undefined,
            output_level: outputLevel ? outputLevel.value : undefined,
            characters: characters,
            choice_policy: (forceChoices && forceChoices.checked) ? 'require' : 'off',
            choice_count: choiceCount ? parseInt(choiceCount.value, 10) || 3 : undefined
        });
        setTimeout(() => { applyCharactersBtn.disabled = false; }, 5000);
    });
}

// 컨텍스트 로드
function loadContext(context) {
    worldInput.value = context.world || '';
    situationInput.value = context.situation || '';

    // 사용자 캐릭터 정보 파싱
    const userChar = context.user_character || '';
    try {
        const nameEl = document.getElementById('userCharacterName');
        const genderEl = document.getElementById('userCharacterGender');
        const ageEl = document.getElementById('userCharacterAge');
        let body = userChar;
        const lines = (userChar || '').split(/\r?\n/);
        if (lines.length && /^\s*이름\s*:\s*/.test(lines[0])) {
            const meta = lines[0];
            body = lines.slice(1).join('\n');
            const mName = meta.match(/이름\s*:\s*([^,]+)/);
            const mGender = meta.match(/성별\s*:\s*([^,]+)/);
            const mAge = meta.match(/나이\s*:\s*([^,]+)/);
            if (nameEl) nameEl.value = mName ? mName[1].trim() : '';
            if (genderEl) genderEl.value = mGender ? mGender[1].trim() : '';
            if (ageEl) ageEl.value = mAge ? mAge[1].trim() : '';
        }
        userCharacterInput.value = (body || '').trim();
    } catch (_) {
        userCharacterInput.value = userChar;
    }

    narratorEnabled.checked = context.narrator_enabled || false;
    narratorMode.value = context.narrator_mode || 'moderate';
    narratorDescription.value = context.narrator_description || '';
    userIsNarrator.checked = context.user_is_narrator || false;
    aiProvider.value = context.ai_provider || 'claude';
    // 모델 복원 (저장된 경우)
    try {
        if (typeof modelSelect !== 'undefined' && modelSelect && context.model !== undefined) {
            // 모델이 빈 문자열이면 기본값을 유지
            const val = context.model || '';
            // 모델 옵션이 존재하면 복원
            const found = [...modelSelect.options].some(o => o.value === val);
            if (found) modelSelect.value = val;
        }
    } catch (_) {}
    // 세션 유지 복원
    try {
        if (typeof sessionRetentionToggle !== 'undefined' && sessionRetentionToggle && context.session_retention !== undefined) {
            sessionRetentionToggle.checked = !!context.session_retention;
        }
    } catch (_) {}
    adultLevel.value = context.adult_level || 'explicit';
    narrativeSeparation.checked = context.narrative_separation || false;
    if (narratorDrive) narratorDrive.value = context.narrator_drive || 'guide';
    if (outputLevel) outputLevel.value = context.output_level || 'normal';
    if (adultConsent) adultConsent.checked = false; // 세션 보관값은 서버 측, UI는 기본 해제
    if (forceChoices) forceChoices.checked = (context.choice_policy || 'off') === 'require';
    if (choiceCount) choiceCount.value = String(context.choice_count || 3);

    // 진행자 설정 표시/숨김
    if (narratorEnabled.checked) {
        narratorSettings.style.display = 'block';
    }

    // 참여자 로드 및 렌더링
    participants = Array.isArray(context.characters) ? [...context.characters] : [];
    renderParticipantsLeftPanel();
    renderParticipantsManagerList();
}

// 설정 전용 화면 채우기
function applyContextToSettingsScreen(ctx) {
    const w = document.getElementById('sWorld');
    const s = document.getElementById('sSituation');
    const u = document.getElementById('sUserChar');
    const ne = document.getElementById('sNarratorEnabled');
    const ap = document.getElementById('sAiProvider');
    if (!w && !s && !u) return; // 화면 아닐 때
    try { if (w) w.value = ctx.world || ''; } catch (_) {}
    try { if (s) s.value = ctx.situation || ''; } catch (_) {}
    try { if (u) u.value = ctx.user_character || ''; } catch (_) {}
    try { if (ne) ne.checked = !!ctx.narrator_enabled; } catch (_) {}
    try { if (ap && ctx.ai_provider) ap.value = ctx.ai_provider; } catch (_) {}
}

function renderSettingsScreenView(roomId) {
    const html = `
      <section aria-labelledby="settingsScreenTitle">
        <h1 id="settingsScreenTitle">설정 — ${roomId}</h1>
        <div style="display:grid; gap:0.75rem; max-width:920px;">
          <div>
            <label class="field-label">🌍 세계관/배경</label>
            <textarea id="sWorld" rows="4" class="input" placeholder="세계관..."></textarea>
          </div>
          <div>
            <label class="field-label">📍 현재 상황</label>
            <textarea id="sSituation" rows="3" class="input" placeholder="상황..."></textarea>
          </div>
          <div>
            <label class="field-label">🙋 나의 캐릭터</label>
            <textarea id="sUserChar" rows="3" class="input" placeholder="캐릭터 요약..."></textarea>
          </div>
          <div>
            <label class="checkbox-label"><input type="checkbox" id="sNarratorEnabled"> <span>AI 진행자</span></label>
          </div>
          <div>
            <label class="field-label">🤖 AI 제공자</label>
            <select id="sAiProvider" class="select-input">
              <option value="claude">Claude</option>
              <option value="droid">Droid</option>
              <option value="gemini">Gemini</option>
            </select>
          </div>
          <div style="display:flex; gap:0.5rem;">
            <button class="btn" onclick="navigate('/rooms/${encodeURIComponent(roomId)}')">← 돌아가기</button>
            <button id="sSaveBtn" class="btn btn-primary">저장</button>
          </div>
        </div>
      </section>`;
    showScreen(html);
    // 기존 UI 값 복사(빠른 프리필)
    try {
        applyContextToSettingsScreen({
            world: worldInput?.value || '',
            situation: situationInput?.value || '',
            user_character: userCharacterInput?.value || '',
            narrator_enabled: !!narratorEnabled?.checked,
            ai_provider: aiProvider?.value || 'claude'
        });
    } catch (_) {}

    const save = document.getElementById('sSaveBtn');
    save?.addEventListener('click', () => {
        const ctx = {
            world: document.getElementById('sWorld')?.value || '',
            situation: document.getElementById('sSituation')?.value || '',
            user_character: document.getElementById('sUserChar')?.value || '',
            narrator_enabled: !!document.getElementById('sNarratorEnabled')?.checked,
            ai_provider: document.getElementById('sAiProvider')?.value || 'claude',
        };
        sendMessage({ action: 'set_context', ...ctx });
        const config = { room_id: roomId, title: roomId, context: ctx };
        sendMessage({ action: 'room_save', room_id: roomId, config });
        navigate(`/rooms/${encodeURIComponent(roomId)}`);
    });
}


// ===== 히스토리 초기화 =====

clearHistoryBtn.addEventListener('click', () => {
    if (confirm('대화 히스토리를 초기화하시겠습니까?')) {
        sendMessage({ action: 'clear_history' });
    }
});

if (resetSessionsBtn) {
    resetSessionsBtn.addEventListener('click', () => {
        if (confirm('현재 연결된 AI 세션을 모두 초기화하시겠습니까?')) {
            sendMessage({ action: 'reset_sessions' });
        }
    });
}

if (sessionRetentionToggle) {
    sessionRetentionToggle.checked = false;
    sessionRetentionToggle.disabled = true;
    sessionRetentionToggle.parentElement?.classList.add('disabled');
}

// ===== 서사 관리 =====

function updateNarrative(markdown) {
    if (!markdown || markdown.includes('아직 대화가 없습니다')) {
        narrativeContent.innerHTML = '<p class="placeholder">대화가 진행되면 여기에 서사가 기록됩니다.</p>';
        return;
    }

    // 간단한 마크다운 렌더링
    let html = markdown
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^---$/gm, '<hr>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/^(.+)$/gm, '<p>$1</p>');

    narrativeContent.innerHTML = html;
}

// 서사 내용을 마크다운으로 변환
function getNarrativeMarkdown() {
    let markdown = '# 서사 기록\n\n';
    markdown += `생성 일시: ${new Date().toLocaleString('ko-KR')}\n\n---\n\n`;

    const messages = chatMessages.querySelectorAll('.chat-message:not(.system)');

    messages.forEach((msg, index) => {
        const isUser = msg.classList.contains('user');
        const content = msg.querySelector('.message-content').textContent;
        const charName = msg.querySelector('.character-name');

        if (isUser) {
            markdown += `## ${index + 1}. 사용자\n\n${content}\n\n`;
        } else {
            const name = charName ? charName.textContent : 'AI';
            markdown += `## ${index + 1}. ${name}\n\n${content}\n\n---\n\n`;
        }
    });

    return markdown;
}

// 서사 저장
saveNarrativeBtn.addEventListener('click', () => {
    const hasContent = narrativeContent.innerText && !narrativeContent.innerText.includes('대화가 진행되면');
    if (!hasContent) {
        alert('저장할 서사가 없습니다.');
        return;
    }

    const defaultName = `서사_${new Date().toISOString().slice(0, 10)}`;
    const filename = prompt('채팅방(서사) 이름을 입력하세요:', currentRoom || defaultName) || currentRoom || defaultName;
    if (!filename) return;

    const exists = (typeof latestStories !== 'undefined') && latestStories.some(f => f.name === filename || f.filename === filename || f.filename === `${filename}.md`);
    const append = !!exists; // 동일 파일명은 항상 덧붙이기 정책
    if (exists) {
        log(`기존 파일에 덧붙여 저장: ${filename}`, 'info');
    }

    // 서버 원본 서사를 사용하여 저장 (append 지원)
    sendMessage({
        action: 'save_story',
        filename: filename,
        use_server: true,
        append: append
    });
    currentRoom = filename;
    try { localStorage.setItem(CURRENT_ROOM_KEY, currentRoom); } catch (_) {}
    // 서사 저장과 동시에 방 설정도 저장
    try {
        const config = collectRoomConfig(currentRoom);
        sendMessage({ action: 'room_save', room_id: currentRoom, config });
    } catch (_) {}
});

// ===== 토큰 표시 =====

function updateTokenDisplay(tokenUsage) {
    const tokenInfoDiv = document.getElementById('tokenInfo');

    // show_token_usage 설정 확인
    if (!appConfig.show_token_usage) {
        tokenInfoDiv.style.display = 'none';
        return;
    }

    tokenInfoDiv.style.display = 'flex';

    if (!tokenUsage || !tokenUsage.providers) return;

    const formatNumber = (num) => num.toLocaleString('ko-KR');
    const providers = tokenUsage.providers;

    // 현재 사용 중인 제공자 또는 Claude 우선
    let activeProvider = null;
    if (currentProvider && providers[currentProvider] && providers[currentProvider].supported) {
        activeProvider = currentProvider;
    } else if (providers.claude && providers.claude.supported) {
        activeProvider = 'claude';
    } else if (providers.gemini && providers.gemini.supported) {
        activeProvider = 'gemini';
    } else if (providers.droid && providers.droid.supported) {
        activeProvider = 'droid';
    }

    if (!activeProvider) {
        // 토큰 정보를 제공하는 제공자가 없음
        tokenText.textContent = '토큰: 정보 없음';
        tokenText.title = '사용 중인 AI 제공자가 토큰 정보를 제공하지 않습니다.';
        tokenInfoDiv.style.color = '#808080'; // 회색
        return;
    }

    const providerData = providers[activeProvider];
    const total = providerData.total_tokens || 0;
    const contextWindow = 200000; // Claude 기본 컨텍스트 윈도우

    // 남은 비율 계산
    const usagePercent = total > 0 ? ((total / contextWindow) * 100).toFixed(1) : 0;

    // 제공자 레이블
    const providerLabel = activeProvider === 'claude' ? 'Claude' :
                         activeProvider === 'gemini' ? 'Gemini' : 'Droid';

    // 메인 텍스트
    tokenText.textContent = `${providerLabel}: ${formatNumber(total)} / ${formatNumber(contextWindow)} (${usagePercent}%)`;

    // 툴팁에 상세 정보 표시
    const tooltipLines = [
        `=== ${providerLabel} 토큰 사용량 ===`,
        `총 누적: ${formatNumber(total)} 토큰 (${providerData.message_count || 0}회)`,
        `최근: ${formatNumber(providerData.last_total_tokens || 0)} 토큰`,
        ``,
        `[누적 상세]`,
        `입력: ${formatNumber(providerData.total_input_tokens || 0)}`,
        `출력: ${formatNumber(providerData.total_output_tokens || 0)}`,
        `캐시 읽기: ${formatNumber(providerData.total_cache_read_tokens || 0)}`,
        `캐시 생성: ${formatNumber(providerData.total_cache_creation_tokens || 0)}`,
        ``,
        `[최근 사용량]`,
        `입력: ${formatNumber(providerData.last_input_tokens || 0)}`,
        `출력: ${formatNumber(providerData.last_output_tokens || 0)}`,
        `캐시 읽기: ${formatNumber(providerData.last_cache_read_tokens || 0)}`,
        `캐시 생성: ${formatNumber(providerData.last_cache_creation_tokens || 0)}`
    ];

    // 다른 제공자 정보도 추가
    Object.keys(providers).forEach(provider => {
        if (provider !== activeProvider && providers[provider].supported) {
            const pData = providers[provider];
            const pLabel = provider === 'claude' ? 'Claude' :
                          provider === 'gemini' ? 'Gemini' : 'Droid';
            tooltipLines.push('');
            tooltipLines.push(`[${pLabel}]`);
            tooltipLines.push(`총: ${formatNumber(pData.total_tokens || 0)} (${pData.message_count || 0}회)`);
            tooltipLines.push(`최근: ${formatNumber(pData.last_total_tokens || 0)}`);
        }
    });

    tokenText.title = tooltipLines.join('\n');

    // 토큰 사용량에 따라 색상 변경
    if (usagePercent > 80) {
        tokenInfoDiv.style.color = '#f48771'; // 빨강 (경고)
    } else if (usagePercent > 50) {
        tokenInfoDiv.style.color = '#dcdcaa'; // 노랑
    } else {
        tokenInfoDiv.style.color = '#4ec9b0'; // 청록 (정상)
    }
}

// ===== 이벤트 리스너 바인딩(동적) =====
let isComposing = false; // IME 입력 중 플래그 (한글, 일본어, 중국어 등)

function bindChatEvents() {
    refreshChatRefs();
    try {
        if (sendChatBtn && !sendChatBtn.dataset.bound) {
            sendChatBtn.addEventListener('click', sendChatMessage);
            sendChatBtn.dataset.bound = '1';
        }
        if (chatInput && !chatInput.dataset.bound) {
            // IME 입력 시작/종료 감지
            chatInput.addEventListener('compositionstart', () => {
                isComposing = true;
            });
            chatInput.addEventListener('compositionend', () => {
                isComposing = false;
            });

            // 모바일(터치) 환경에서는 Enter 키 전송을 막고 버튼으로만 전송하도록 처리
              const isTouchDevice = (typeof window !== 'undefined') && (
                  ('ontouchstart' in window) ||
                  (navigator.maxTouchPoints && navigator.maxTouchPoints > 0) ||
                  (window.matchMedia && window.matchMedia('(pointer: coarse)').matches) ||
                  /Mobi|Android|iPhone|iPad|iPod|Windows Phone|webOS/i.test(navigator.userAgent)
              );

            if (!isTouchDevice) {
                chatInput.addEventListener('keydown', (e) => {
                    // IME 입력 중이 아닐 때만 Enter로 전송
                    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
                        e.preventDefault();
                        sendChatMessage();
                    }
                });
            }

            chatInput.dataset.bound = '1';
        }
    } catch (_) {}
}

bindChatEvents();

// ===== 탭 전환 =====

// ===== 설정 모달 =====

const settingsModal = document.getElementById('settingsModal');
const settingsBtn = document.getElementById('settingsBtn');
const closeSettingsBtn = document.getElementById('closeSettingsBtn');
const settingsModalOverlay = document.querySelector('.settings-modal-overlay');

// 설정 모달 열기
if (settingsBtn) {
    settingsBtn.addEventListener('click', () => {
        try { window.__lastSettingsTrigger = document.activeElement; } catch (_) {}
        settingsModal.classList.remove('hidden');
        enableFocusTrap(settingsModal);
    });
}

// 설정 모달 닫기
if (closeSettingsBtn) {
    closeSettingsBtn.addEventListener('click', () => {
        settingsModal.classList.add('hidden');
        disableFocusTrap(settingsModal);
        try { window.__lastSettingsTrigger?.focus?.(); } catch (_) {}
    });
}

// 오버레이 클릭 시 모달 닫기
if (settingsModalOverlay) {
    settingsModalOverlay.addEventListener('click', () => {
        settingsModal.classList.add('hidden');
        disableFocusTrap(settingsModal);
        try { window.__lastSettingsTrigger?.focus?.(); } catch (_) {}
    });
}

// ===== 관리자 모달 =====
// 로그인 버튼
if (loginBtn) {
    loginBtn.addEventListener('click', () => {
        showLoginModal();
    });
}
if (moreLoginBtn) {
    moreLoginBtn.addEventListener('click', () => {
        showLoginModal();
    });
}

// 로그아웃 핸들러
function handleLogout() {
    clearAuthToken();
    setRefreshToken('', '');
    localStorage.removeItem(USER_ROLE_KEY);
    userRole = 'user';
    isAuthenticated = false;
    adminBtn.style.display = 'none';
    moreAdminBtn.style.display = 'none';
    loginBtn.style.display = 'block';
    moreLoginBtn.style.display = 'block';
    logoutBtn.style.display = 'none';
    moreLogoutBtn.style.display = 'none';
    log('로그아웃 되었습니다.', 'info');
    location.reload();
}

// 로그아웃 버튼
if (logoutBtn) {
    logoutBtn.addEventListener('click', handleLogout);
}
if (moreLogoutBtn) {
    moreLogoutBtn.addEventListener('click', handleLogout);
}

// 관리자 모달 열기
async function openAdminModal() {
    adminModal.classList.remove('hidden');
    await fetchPendingUsers();
}

if (adminBtn) {
    adminBtn.addEventListener('click', openAdminModal);
}
if (moreAdminBtn) {
    moreAdminBtn.addEventListener('click', openAdminModal);
}

// 관리자 모달 닫기
if (adminCloseBtn) {
    adminCloseBtn.addEventListener('click', () => {
        adminModal.classList.add('hidden');
    });
}

// 승인 대기 사용자 목록 조회
async function fetchPendingUsers() {
    if (!authToken) {
        log('관리자 권한이 필요합니다.', 'error');
        return;
    }

    try {
        const response = await fetch('/api/admin/pending-users', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            renderPendingUsers(data.users || []);
        } else {
            log(data.error || '사용자 목록 조회 실패', 'error');
            renderPendingUsers([]);
        }
    } catch (error) {
        console.error('Fetch pending users error:', error);
        log('서버 오류가 발생했습니다.', 'error');
        renderPendingUsers([]);
    }
}

// 승인 대기 사용자 목록 렌더링
function renderPendingUsers(users) {
    if (!users || users.length === 0) {
        pendingUsersList.style.display = 'none';
        noPendingUsers.style.display = 'block';
        return;
    }

    pendingUsersList.style.display = 'block';
    noPendingUsers.style.display = 'none';

    pendingUsersList.innerHTML = users.map(user => `
        <div class="pending-user-card" style="
            background: #f8f9fa;
            padding: 1rem;
            margin-bottom: 0.75rem;
            border-radius: 8px;
            border: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <div style="flex: 1;">
                <div style="font-weight: 600; color: #333; margin-bottom: 0.25rem;">
                    ${escapeHtml(user.username)}
                </div>
                <div style="font-size: 0.875rem; color: #666; margin-bottom: 0.25rem;">
                    📧 ${escapeHtml(user.email)}
                </div>
                <div style="font-size: 0.75rem; color: #999;">
                    가입일: ${new Date(user.created_at).toLocaleString('ko-KR')}
                </div>
            </div>
            <button
                class="approve-user-btn btn btn-sm"
                data-user-id="${user.user_id}"
                style="
                    background: #28a745;
                    color: white;
                    border: none;
                    padding: 0.5rem 1rem;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 0.875rem;
                    white-space: nowrap;
                "
            >
                ✓ 승인
            </button>
        </div>
    `).join('');

    // 승인 버튼 이벤트 리스너 등록
    document.querySelectorAll('.approve-user-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const userId = parseInt(e.target.dataset.userId);
            await approveUser(userId);
        });
    });
}

// 사용자 승인
async function approveUser(userId) {
    if (!authToken) {
        log('관리자 권한이 필요합니다.', 'error');
        return;
    }

    try {
        const response = await fetch('/api/admin/approve-user', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: userId })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            log('사용자 승인이 완료되었습니다.', 'success');
            // 목록 새로고침
            await fetchPendingUsers();
        } else {
            log(data.error || '승인 실패', 'error');
        }
    } catch (error) {
        console.error('Approve user error:', error);
        log('서버 오류가 발생했습니다.', 'error');
    }
}

// HTML 이스케이프 함수
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== 파일 관리 =====

// 파일 목록 응답 처리
function handleFileList(data) {
    if (window.pendingFileListSelect) {
        updateFileList(window.pendingFileListSelect, data.files);
        window.pendingFileListSelect = null;
        window.pendingFileListType = null;
    } else if (window.pendingTemplateSelect) {
        // 캐릭터 템플릿 목록 업데이트
        updateTemplateList(window.pendingTemplateSelect, data.files);
        window.pendingTemplateSelect = null;
    }
}

// NPC 목록 업데이트
function updateTemplateList(selectElement, files) {
    const currentValue = selectElement.value;
    selectElement.innerHTML = '<option value="">📂 템플릿</option>';

    files.forEach(file => {
        const option = document.createElement('option');
        option.value = file.name;
        option.textContent = file.name;
        selectElement.appendChild(option);
    });

    if (currentValue && files.some(f => f.name === currentValue)) {
        selectElement.value = currentValue;
    }
}

// 파일 목록 로드
async function loadFileList(fileType, selectElement) {
    // 응답 처리를 위해 fileType을 저장
    window.pendingFileListType = fileType;
    window.pendingFileListSelect = selectElement;
    sendMessage({ action: 'list_workspace_files', file_type: fileType });
}

// 실제 파일 목록 업데이트
function updateFileList(selectElement, files) {
    const currentValue = selectElement.value;
    selectElement.innerHTML = '<option value="">새로 만들기...</option>';

    files.forEach(file => {
        const option = document.createElement('option');
        option.value = file.name;
        option.textContent = file.name;
        selectElement.appendChild(option);
    });

    // 이전 선택값 복원
    if (currentValue && files.some(f => f.name === currentValue)) {
        selectElement.value = currentValue;
    }
}

// 파일 로드 응답 처리
function handleFileLoad(data) {
    const content = data.content;
    const filename = data.filename;

    // 파일 타입에 따라 적절한 곳에 로드
    if (window.pendingLoadType === 'world') {
        worldInput.value = content;
        worldSelect.value = filename.replace('.md', '');
    } else if (window.pendingLoadType === 'situation') {
        situationInput.value = content;
        situationSelect.value = filename.replace('.md', '');
    } else if (window.pendingLoadType === 'my_character') {
        // 메타 파싱(이름/성별/나이)
        try {
            const nameEl = document.getElementById('userCharacterName');
            const genderEl = document.getElementById('userCharacterGender');
            const ageEl = document.getElementById('userCharacterAge');
            let body = content || '';
            const lines = body.split(/\r?\n/);
            if (lines.length && /^\s*이름\s*:\s*/.test(lines[0])) {
                const meta = lines[0];
                body = lines.slice(1).join('\n');
                // 이름, 성별, 나이 추출
                const mName = meta.match(/이름\s*:\s*([^,]+)/);
                const mGender = meta.match(/성별\s*:\s*([^,]+)/);
                const mAge = meta.match(/나이\s*:\s*([^,]+)/);
                if (nameEl) nameEl.value = mName ? mName[1].trim() : '';
                if (genderEl) genderEl.value = mGender ? mGender[1].trim() : '';
                if (ageEl) ageEl.value = mAge ? mAge[1].trim() : '';
            }
            userCharacterInput.value = body.trim();
        } catch (_) {
            userCharacterInput.value = content;
        }
        myCharacterSelect.value = filename.replace('.md', '');
    } else if (window.pendingLoadType === 'char_template') {
        // 템플릿(JSON) 로드 → 모달 또는 캐릭터 아이템에 반영
        try {
            const obj = JSON.parse(content || '{}');
            if (window.pendingAddFromTemplate) {
                const name = obj.name || '';
                const gender = obj.gender || '';
                const age = (obj.age !== undefined && obj.age !== null) ? String(obj.age) : '';
                const summary = obj.summary || obj.description || '';
                const traits = obj.traits || '';
                const goals = obj.goals || '';
                const boundaries = obj.boundaries || '';
                const examples = Array.isArray(obj.examples) ? obj.examples : [];
                const tags = Array.isArray(obj.tags) ? obj.tags.join(', ') : '';
            const desc = composeDescription(summary, gender, age, traits, goals, boundaries, examples, tags, false);
            participants.push({ name, gender, age, description: desc });
            renderParticipantsLeftPanel();
            renderParticipantsManagerList();
            } else if (window.pendingTemplateModal) {
                const ceName = document.getElementById('ceName');
                const ceGender = document.getElementById('ceGender');
                const ceAge = document.getElementById('ceAge');
                const ceSummary = document.getElementById('ceSummary');
                const ceTraits = document.getElementById('ceTraits');
                const ceGoals = document.getElementById('ceGoals');
                const ceBoundaries = document.getElementById('ceBoundaries');
                const ceExamples = document.getElementById('ceExamples');
                const ceTags = document.getElementById('ceTags');
                ceName.value = obj.name || '';
                ceGender.value = obj.gender || '';
                ceAge.value = (obj.age !== undefined && obj.age !== null) ? String(obj.age) : '';
                ceSummary.value = obj.summary || obj.description || '';
                ceTraits.value = obj.traits || '';
                ceGoals.value = obj.goals || '';
                ceBoundaries.value = obj.boundaries || '';
                ceExamples.value = Array.isArray(obj.examples) ? obj.examples.join('\n') : '';
                ceTags.value = Array.isArray(obj.tags) ? obj.tags.join(', ') : '';
            } else if (window.pendingTemplateItem) {
                const nameInput = window.pendingTemplateItem.querySelector('.character-name-input');
                const genderSelect = window.pendingTemplateItem.querySelector('.character-gender-input');
                const ageInput = window.pendingTemplateItem.querySelector('.character-age-input');
                const descInput = window.pendingTemplateItem.querySelector('.character-description-input');
                if (obj.name) nameInput.value = obj.name;
                if (obj.gender !== undefined) genderSelect.value = obj.gender;
                if (obj.age !== undefined) ageInput.value = obj.age;
                if (obj.description !== undefined) descInput.value = obj.description;
                else if (obj.summary !== undefined) descInput.value = obj.summary;
            }
        } catch (e) {
            log('템플릿 JSON 파싱 실패', 'error');
        }
        window.pendingTemplateItem = null;
        window.pendingTemplateModal = false;
        window.pendingAddFromTemplate = false;
    } else if (window.pendingLoadType === 'my_profile') {
        try {
            const obj = JSON.parse(content || '{}');
            if (loginModal) { /* noop */ }
            const nameEl = document.getElementById('userCharacterName');
            const genderEl = document.getElementById('userCharacterGender');
            const ageEl = document.getElementById('userCharacterAge');
            if (nameEl) nameEl.value = obj.name || '';
            if (genderEl) genderEl.value = obj.gender || '';
            if (ageEl) ageEl.value = (obj.age !== undefined && obj.age !== null) ? String(obj.age) : '';
            userCharacterInput.value = obj.description || obj.summary || '';
            log('내 프로필을 불러왔습니다.', 'success');
        } catch (e) {
            log('내 프로필 JSON 파싱 실패', 'error');
        }
    }
}

// 파일 저장
async function saveFile(fileType, selectElement, contentGetter) {
    const filename = prompt(`파일 이름을 입력하세요 (${fileType}):`);
    if (!filename) return;

    const content = contentGetter();
    sendMessage({
        action: 'save_workspace_file',
        file_type: fileType,
        filename: filename,
        content: content
    });

    // 저장 후 목록 새로고침
    setTimeout(() => {
        loadFileList(fileType, selectElement);
    }, 500);
}

// 파일 로드
function loadFile(fileType, filename) {
    window.pendingLoadType = fileType;
    sendMessage({
        action: 'load_workspace_file',
        file_type: fileType,
        filename: filename
    });
}

// 파일 삭제
function deleteFile(fileType, selectElement) {
    const filename = selectElement.value;
    if (!filename) {
        alert('삭제할 파일을 선택하세요');
        return;
    }

    if (!confirm(`"${filename}" 파일을 삭제하시겠습니까?`)) {
        return;
    }

    sendMessage({
        action: 'delete_workspace_file',
        file_type: fileType,
        filename: filename
    });

    // 삭제 후 목록 새로고침
    setTimeout(() => {
        loadFileList(fileType, selectElement);
    }, 500);
}

// 세계관 파일 관리
saveWorldBtn.addEventListener('click', () => {
    saveFile('world', worldSelect, () => worldInput.value);
});

worldSelect.addEventListener('change', () => {
    if (worldSelect.value) {
        loadFile('world', worldSelect.value);
    }
});

deleteWorldBtn.addEventListener('click', () => {
    deleteFile('world', worldSelect);
});

// 상황 파일 관리
saveSituationBtn.addEventListener('click', () => {
    saveFile('situation', situationSelect, () => situationInput.value);
});

situationSelect.addEventListener('change', () => {
    if (situationSelect.value) {
        loadFile('situation', situationSelect.value);
    }
});

deleteSituationBtn.addEventListener('click', () => {
    deleteFile('situation', situationSelect);
});

// 나의 캐릭터 관리
saveMyCharacterBtn.addEventListener('click', () => {
    const name = document.getElementById('userCharacterName').value.trim();
    const gender = document.getElementById('userCharacterGender').value.trim();
    const age = userCharacterAgeInput ? userCharacterAgeInput.value.trim() : '';
    const desc = userCharacterInput.value.trim();
    if (!name && !desc) {
        alert('이름 또는 캐릭터 내용을 입력하세요');
        return;
    }
    const lines = [];
    if (name) {
        const meta = [`이름: ${name}`];
        if (gender) meta.push(`성별: ${gender}`);
        if (age) meta.push(`나이: ${age}`);
        lines.push(meta.join(', '));
    }
    if (desc) lines.push(desc);
    const content = lines.join('\n');
    saveFile('my_character', myCharacterSelect, () => content);
});

myCharacterSelect.addEventListener('change', () => {
    if (myCharacterSelect.value) {
        loadFile('my_character', myCharacterSelect.value);
    }
});

deleteMyCharacterBtn.addEventListener('click', () => {
    deleteFile('my_character', myCharacterSelect);
});

// 내 프로필(JSON) 저장/불러오기
if (saveProfileJsonBtn) {
    saveProfileJsonBtn.addEventListener('click', () => {
        const name = document.getElementById('userCharacterName').value.trim();
        const gender = document.getElementById('userCharacterGender').value.trim();
        const age = userCharacterAgeInput ? userCharacterAgeInput.value.trim() : '';
        const description = userCharacterInput.value.trim();
        const payload = { name, role: 'user', gender, age, description };
        sendMessage({
            action: 'save_workspace_file',
            file_type: 'my_profile',
            filename: 'my_profile',
            content: JSON.stringify(payload, null, 2)
        });
        log('내 프로필(JSON) 저장 요청', 'info');
    });
}

if (loadProfileJsonBtn) {
    loadProfileJsonBtn.addEventListener('click', () => {
        window.pendingLoadType = 'my_profile';
        sendMessage({
            action: 'load_workspace_file',
            file_type: 'my_profile',
            filename: 'my_profile'
        });
    });
}

// ===== 캐릭터 편집 모달 =====

let currentEditingCharacterItem = null;

function openCharacterEditor(characterDiv) {
    currentEditingCharacterItem = characterDiv;
    const modal = document.getElementById('characterEditorModal');
    const ceName = document.getElementById('ceName');
    const ceGender = document.getElementById('ceGender');
    const ceAge = document.getElementById('ceAge');
    const ceSummary = document.getElementById('ceSummary');
    const ceTraits = document.getElementById('ceTraits');
    const ceGoals = document.getElementById('ceGoals');
    const ceBoundaries = document.getElementById('ceBoundaries');
    const ceExamples = document.getElementById('ceExamples');
    const ceTags = document.getElementById('ceTags');
    const nameInput = characterDiv.querySelector('.character-name-input');
    const genderInput = characterDiv.querySelector('.character-gender-input');
    const ageInput = characterDiv.querySelector('.character-age-input');
    const descInput = characterDiv.querySelector('.character-description-input');

    // 값 채우기
    ceName.value = nameInput.value || '';
    ceGender.value = genderInput.value || '';
    ceAge.value = ageInput.value || '';
    ceSummary.value = descInput.value || '';
    ceTraits.value = characterDiv.dataset.traits || '';
    ceGoals.value = characterDiv.dataset.goals || '';
    ceBoundaries.value = characterDiv.dataset.boundaries || '';
    ceExamples.value = characterDiv.dataset.examples ? JSON.parse(characterDiv.dataset.examples).join('\n') : '';
    ceTags.value = characterDiv.dataset.tags || '';

    // 템플릿 목록 갱신
    loadCharTemplateList(document.getElementById('ceTemplateSelect'));

    try { window.__lastEditorTrigger = document.activeElement; } catch (_) {}
    modal.classList.remove('hidden');
    enableFocusTrap(modal);
}

function closeCharacterEditor() {
    const modal = document.getElementById('characterEditorModal');
    modal.classList.add('hidden');
    disableFocusTrap(modal);
    currentEditingCharacterItem = null;
    try { window.__lastEditorTrigger?.focus?.(); } catch (_) {}
}

function applyCharacterEditorToItem() {
    if (!currentEditingCharacterItem) return;
    const ceName = document.getElementById('ceName');
    const ceGender = document.getElementById('ceGender');
    const ceAge = document.getElementById('ceAge');
    const ceSummary = document.getElementById('ceSummary');
    const ceTraits = document.getElementById('ceTraits');
    const ceGoals = document.getElementById('ceGoals');
    const ceBoundaries = document.getElementById('ceBoundaries');
    const ceExamples = document.getElementById('ceExamples');
    const ceTags = document.getElementById('ceTags');

    const nameInput = currentEditingCharacterItem.querySelector('.character-name-input');
    const genderInput = currentEditingCharacterItem.querySelector('.character-gender-input');
    const ageInput = currentEditingCharacterItem.querySelector('.character-age-input');
    const descInput = currentEditingCharacterItem.querySelector('.character-description-input');

    nameInput.value = ceName.value.trim();
    genderInput.value = ceGender.value.trim();
    ageInput.value = ceAge.value.trim();
    descInput.value = ceSummary.value.trim();

    // 확장 필드 저장 (dataset)
    currentEditingCharacterItem.dataset.traits = ceTraits.value.trim();
    currentEditingCharacterItem.dataset.goals = ceGoals.value.trim();
    currentEditingCharacterItem.dataset.boundaries = ceBoundaries.value.trim();
    const examplesArr = ceExamples.value.split('\n').map(s => s.trim()).filter(Boolean);
    currentEditingCharacterItem.dataset.examples = JSON.stringify(examplesArr);
    currentEditingCharacterItem.dataset.tags = ceTags.value.trim();

    // 요약 갱신
    const summaryBar = currentEditingCharacterItem.querySelector('.character-summary');
    if (summaryBar) {
        const nm = nameInput.value || '이름 없음';
        const gd = genderInput.value || '-';
        const ag = ageInput.value || '-';
        const snip = (descInput.value || '').slice(0, 40).replace(/\n/g, ' ');
        summaryBar.textContent = `${nm} · ${gd} · ${ag} — ${snip}`;
    }

    closeCharacterEditor();
}

// 모달 버튼 이벤트
document.getElementById('ceCloseBtn')?.addEventListener('click', closeCharacterEditor);
document.getElementById('ceCancelBtn')?.addEventListener('click', closeCharacterEditor);
document.getElementById('ceSaveBtn')?.addEventListener('click', applyCharacterEditorToItem);
document.getElementById('ceSaveTemplateBtn')?.addEventListener('click', saveCharacterTemplateFromModal);

// 모달 템플릿 선택 시 로드
document.getElementById('ceTemplateSelect')?.addEventListener('change', (e) => {
    const sel = e.target;
    if (sel.value) {
        window.pendingLoadType = 'char_template';
        window.pendingTemplateModal = true;
        sendMessage({ action: 'load_workspace_file', file_type: 'char_template', filename: sel.value });
    }
});

// ===== 참여자 관리 (전용 모달) =====

function openParticipantsModal() {
    const modal = document.getElementById('participantsModal');
    if (!modal) return;
    // 템플릿 목록 갱신 및 참여자 목록 렌더
    loadCharTemplateList(document.getElementById('pmTemplateSelect'));
    renderParticipantsManagerList();
    modal.classList.remove('hidden');
    enableFocusTrap(modal);
}

function closeParticipantsModal() {
    const modal = document.getElementById('participantsModal');
    if (modal) {
        modal.classList.add('hidden');
        disableFocusTrap(modal);
    }
}

function renderParticipantsLeftPanel() {
    charactersList.innerHTML = '';
    if (!Array.isArray(participants) || participants.length === 0) {
        const p = document.createElement('p');
        p.className = 'placeholder';
        p.textContent = '현재 참여자가 없습니다. “참여자 추가”를 눌러 추가하세요.';
        charactersList.appendChild(p);
        return;
    }
    const stripMeta = (text) => (text || '')
        .replace(/(^|\n)\s*(성별|나이|이름)\s*:[^\n]*\n?/g, '$1')
        .trim();
    participants.forEach((c, idx) => {
        const row = document.createElement('div');
        row.className = 'character-chip';
        row.style.padding = '6px 8px';
        row.style.marginBottom = '6px';
        row.style.border = '1px solid #e8ecef';
        row.style.borderRadius = '8px';
        row.style.background = '#fff';
        const nm = c.name || '이름 없음';
        const gd = c.gender || '-';
        const ag = c.age || '-';
        const snip = stripMeta(c.description).slice(0, 60).replace(/\n/g, ' ');
        row.textContent = `${nm} · ${gd} · ${ag} — ${snip}`;
        charactersList.appendChild(row);
    });
}

function renderParticipantsManagerList() {
    const wrap = document.getElementById('participantsManagerList');
    if (!wrap) return;
    wrap.innerHTML = '';
    if (!Array.isArray(participants) || participants.length === 0) {
        wrap.innerHTML = '<p class="placeholder">참여자가 없습니다.</p>';
        return;
    }
    const stripMeta = (text) => (text || '')
        .replace(/(^|\n)\s*(성별|나이|이름)\s*:[^\n]*\n?/g, '$1')
        .trim();
    participants.forEach((c, idx) => {
        const row = document.createElement('div');
        row.style.display = 'flex';
        row.style.alignItems = 'center';
        row.style.gap = '0.5rem';
        row.style.margin = '4px 0';
        const info = document.createElement('div');
        info.style.flex = '1';
        info.textContent = `${c.name || '이름 없음'} · ${c.gender || '-'} · ${c.age || '-'} — ${stripMeta(c.description).slice(0,60).replace(/\n/g,' ')}`;
        const edit = document.createElement('button');
        edit.className = 'btn btn-sm';
        edit.textContent = '✏️ 편집';
        edit.onclick = () => openParticipantEditor(idx);
        const del = document.createElement('button');
        del.className = 'btn btn-sm btn-remove';
        del.textContent = '🗑️';
        del.onclick = () => { participants.splice(idx,1); renderParticipantsLeftPanel(); renderParticipantsManagerList(); };
        row.appendChild(info);
        row.appendChild(edit);
        row.appendChild(del);
        wrap.appendChild(row);
    });
}

function openParticipantEditor(index) {
    // 참여자 모달이 열려 있으면 닫고(오버레이 제거) 편집 모달을 연다
    closeParticipantsModal();
    // 채우고 모달 오픈
    const c = (index != null && index >=0) ? participants[index] : { name:'', gender:'', age:'', description:'', traits:'', goals:'', boundaries:'', examples:[], tags:[] };
    const modal = document.getElementById('characterEditorModal');
    document.getElementById('ceName').value = c.name || '';
    document.getElementById('ceGender').value = c.gender || '';
    document.getElementById('ceAge').value = c.age || '';
    document.getElementById('ceSummary').value = c.description || '';
    document.getElementById('ceTraits').value = c.traits || '';
    document.getElementById('ceGoals').value = c.goals || '';
    document.getElementById('ceBoundaries').value = c.boundaries || '';
    document.getElementById('ceExamples').value = Array.isArray(c.examples)? c.examples.join('\n'): '';
    document.getElementById('ceTags').value = Array.isArray(c.tags)? c.tags.join(', '): (c.tags || '');
    loadCharTemplateList(document.getElementById('ceTemplateSelect'));
    modal.classList.remove('hidden');
    // 저장 핸들러 재바인딩
    const saveBtn = document.getElementById('ceSaveBtn');
    saveBtn.onclick = () => {
        const name = document.getElementById('ceName').value.trim();
        const gender = document.getElementById('ceGender').value.trim();
        const age = document.getElementById('ceAge').value.trim();
        const summary = document.getElementById('ceSummary').value.trim();
        const traits = document.getElementById('ceTraits').value.trim();
        const goals = document.getElementById('ceGoals').value.trim();
        const boundaries = document.getElementById('ceBoundaries').value.trim();
        const examples = document.getElementById('ceExamples').value.split('\n').map(s=>s.trim()).filter(Boolean);
        const tags = document.getElementById('ceTags').value.split(',').map(s=>s.trim()).filter(Boolean);
        const desc = composeDescription(summary, gender, age, traits, goals, boundaries, examples, tags.join(', '));
        const obj = { name, gender, age, description: desc };
        if (index != null && index >= 0) participants[index] = obj; else participants.push(obj);
        renderParticipantsLeftPanel();
        renderParticipantsManagerList();
        closeCharacterEditor();
    };
}

// 설정 모달: 참여자 추가/템플릿 추가
document.getElementById('participantsBtn')?.addEventListener('click', openParticipantsModal);
document.getElementById('pmCloseBtn')?.addEventListener('click', closeParticipantsModal);
document.querySelector('#participantsModal .settings-modal-overlay')?.addEventListener('click', closeParticipantsModal);
document.getElementById('pmApplyBtn')?.addEventListener('click', () => {
    // participants 를 서버 컨텍스트에 즉시 적용
    const userName = document.getElementById('userCharacterName').value.trim();
    const userGender = document.getElementById('userCharacterGender').value.trim();
    const userDesc = userCharacterInput.value.trim();
    const userAge = (userCharacterAgeInput ? userCharacterAgeInput.value.trim() : '');
    let userCharacterData = '';
    if (userName) {
        userCharacterData = `이름: ${userName}`;
        if (userGender) userCharacterData += `, 성별: ${userGender}`;
        if (userAge) userCharacterData += `, 나이: ${userAge}`;
        if (userDesc) userCharacterData += `\n${userDesc}`;
    } else if (userDesc) {
        userCharacterData = userDesc;
    }
    sendMessage({
        action: 'set_context',
        world: worldInput.value.trim(),
        situation: situationInput.value.trim(),
        user_character: userCharacterData,
        narrator_enabled: narratorEnabled.checked,
        narrator_mode: narratorMode.value,
        narrator_description: narratorDescription.value.trim(),
        user_is_narrator: userIsNarrator.checked,
        ai_provider: aiProvider.value,
        adult_level: adultLevel.value,
        narrative_separation: narrativeSeparation.checked,
        characters: Array.isArray(participants) ? participants : []
    });
});

document.getElementById('pmAddNewBtn')?.addEventListener('click', () => openParticipantEditor(-1));
document.getElementById('pmAddFromTemplateBtn')?.addEventListener('click', () => {
    const sel = document.getElementById('pmTemplateSelect');
    if (sel && sel.value) {
        window.pendingLoadType = 'char_template';
        window.pendingAddFromTemplate = true;
        sendMessage({ action: 'load_workspace_file', file_type: 'char_template', filename: sel.value });
    }
});

// ===== 프리셋 관리 =====

// 프리셋 목록 로드
function loadPresetList() {
    sendMessage({ action: 'list_presets' });
}

// 프리셋 목록 업데이트
function updatePresetList(files) {
    const currentValue = presetSelect.value;
    presetSelect.innerHTML = '<option value="">프리셋 선택...</option>';

    files.forEach(file => {
        const option = document.createElement('option');
        option.value = file.name;
        option.textContent = file.name;
        presetSelect.appendChild(option);
    });

    if (currentValue && files.some(f => f.name === currentValue)) {
        presetSelect.value = currentValue;
    }
}

// 현재 설정을 프리셋으로 저장
function savePreset() {
    const filename = prompt('프리셋 이름을 입력하세요:');
    if (!filename) return;

    // 현재 참여자 수집
    const characters = Array.isArray(participants) ? participants : [];

    // 전체 설정 데이터
    const preset = {
        world: worldInput.value,
        situation: situationInput.value,
        user_character: userCharacterInput.value,
        characters: characters,
        narrator_enabled: narratorEnabled.checked,
        narrator_mode: narratorMode.value,
        narrator_description: narratorDescription.value,
        user_is_narrator: userIsNarrator.checked,
        adult_level: adultLevel.value,
        narrative_separation: narrativeSeparation.checked,
        // 확장 저장: AI/출력/주도권/선택지/유저프로필
        ai_provider: aiProvider ? aiProvider.value : 'claude',
        output_level: outputLevel ? outputLevel.value : 'normal',
        narrator_drive: narratorDrive ? narratorDrive.value : 'guide',
        choice_policy: (forceChoices && forceChoices.checked) ? 'require' : 'off',
        choice_count: choiceCount ? (parseInt(choiceCount.value, 10) || 3) : 3,
        user_profile: {
            name: (document.getElementById('userCharacterName')?.value || '').trim(),
            gender: (document.getElementById('userCharacterGender')?.value || '').trim(),
            age: (document.getElementById('userCharacterAge')?.value || '').trim()
        }
    };

    sendMessage({
        action: 'save_preset',
        filename: filename,
        preset: preset
    });
}

// 프리셋 적용
function applyPreset(preset) {
    // 기본 설정
    worldInput.value = preset.world || '';
    situationInput.value = preset.situation || '';
    userCharacterInput.value = preset.user_character || '';

    // 참여자 초기화 및 로드
    participants = Array.isArray(preset.characters) ? [...preset.characters] : [];
    renderParticipantsLeftPanel();
    renderParticipantsManagerList();

    // 진행자 설정
    narratorEnabled.checked = preset.narrator_enabled || false;
    narratorMode.value = preset.narrator_mode || 'moderate';
    narratorDescription.value = preset.narrator_description || '';
    userIsNarrator.checked = preset.user_is_narrator || false;

    // 모드/기타 설정
    adultLevel.value = preset.adult_level || 'explicit';
    narrativeSeparation.checked = preset.narrative_separation || false;
    if (aiProvider && preset.ai_provider) aiProvider.value = preset.ai_provider;
    if (outputLevel && preset.output_level) outputLevel.value = preset.output_level;
    if (narratorDrive && preset.narrator_drive) narratorDrive.value = preset.narrator_drive;
    if (forceChoices) forceChoices.checked = (preset.choice_policy || 'off') === 'require';
    if (choiceCount && (preset.choice_count !== undefined)) choiceCount.value = String(preset.choice_count);

    // 사용자 프로필 메타(이름/성별/나이)
    try {
        const prof = preset.user_profile || {};
        const nameEl = document.getElementById('userCharacterName');
        const genderEl = document.getElementById('userCharacterGender');
        const ageEl = document.getElementById('userCharacterAge');
        if (nameEl) nameEl.value = prof.name || '';
        if (genderEl) genderEl.value = prof.gender || '';
        if (ageEl) ageEl.value = prof.age || '';
    } catch (_) {}

    // 진행자 설정 표시/숨김
    if (narratorEnabled.checked && !userIsNarrator.checked) {
        narratorSettings.style.display = 'block';
    } else {
        narratorSettings.style.display = 'none';
    }
}

// 프리셋 삭제
function deletePreset() {
    const filename = presetSelect.value;
    if (!filename) {
        alert('삭제할 프리셋을 선택하세요');
        return;
    }

    if (!confirm(`"${filename}" 프리셋을 삭제하시겠습니까?`)) {
        return;
    }

    sendMessage({
        action: 'delete_preset',
        filename: filename
    });
}

// 프리셋 이벤트 리스너
savePresetBtn.addEventListener('click', savePreset);

loadPresetBtn.addEventListener('click', () => {
    const filename = presetSelect.value;
    if (!filename) {
        alert('불러올 프리셋을 선택하세요');
        return;
    }

    sendMessage({
        action: 'load_preset',
        filename: filename
    });
});

deletePresetBtn.addEventListener('click', deletePreset);

// (제거됨) 모드 관리 UI/로직은 더 이상 사용하지 않습니다.

// ===== 서사 관리(dead) 제거됨: UI는 비활성화됨(서버 스텁 유지) =====

// 서사 표시
function displayStoryContent(_) { /* no-op: stories disabled */ }

// 서사 로드 버튼
loadStoryBtn?.addEventListener('click', () => alert('스토리 불러오기 기능은 비활성화되었습니다.'));

// 서사 이어하기 버튼
resumeStoryBtn?.addEventListener('click', () => alert('스토리 이어하기 기능은 비활성화되었습니다.'));

function renderHistorySnapshot(history) {
    try {
        chatMessages.innerHTML = '';
        if (!Array.isArray(history) || history.length === 0) {
            chatMessages.innerHTML = '<div class="chat-message system"><p>대화를 시작하세요</p></div>';
            return;
        }
        history.forEach(msg => {
            const role = msg.role === 'user' ? 'user' : 'assistant';
            addChatMessage(role, msg.content || '');
        });
        // 서사 패널도 최신으로 갱신
        sendMessage({ action: 'get_narrative' });
        announce('히스토리가 갱신되었습니다');
    } catch (e) {
        console.error('renderHistorySnapshot error', e);
    }
}

// 서사 삭제 버튼
deleteStoryBtn?.addEventListener('click', () => alert('스토리 삭제 기능은 비활성화되었습니다.'));

// 서사 → 컨텍스트 주입 버튼
injectStoryBtn?.addEventListener('click', () => alert('스토리 주입 기능은 비활성화되었습니다.'));

// ===== 햄버거 메뉴 (모바일) =====

const hamburgerBtn = document.getElementById('hamburgerBtn');
const narrativeMenuBtn = document.getElementById('narrativeMenuBtn');
const moreMenuBtn = document.getElementById('moreMenuBtn');
const moreMenuDropdown = document.getElementById('moreMenuDropdown');
const mobileOverlay = document.getElementById('mobileOverlay');
const leftPanel = document.querySelector('.left-panel');
const rightPanel = document.querySelector('.right-panel');

let currentMobilePanel = null; // 'left' or 'right' or null

if (hamburgerBtn) {
    hamburgerBtn.addEventListener('click', () => {
        if (currentMobilePanel === 'left') {
            // 이미 좌측 패널이 열려 있으면 닫기
            closeMobilePanel();
        } else {
            // 좌측 패널 열기
            openMobilePanel('left');
        }
    });
}

if (narrativeMenuBtn) {
    narrativeMenuBtn.addEventListener('click', () => {
        if (currentMobilePanel === 'right') {
            // 이미 우측 패널이 열려 있으면 닫기
            closeMobilePanel();
        } else {
            // 우측 패널 열기
            openMobilePanel('right');
        }
    });
}

// 더보기 메뉴 토글
if (moreMenuBtn) {
    moreMenuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleMoreMenu();
    });
}

function toggleMoreMenu() {
    const isVisible = moreMenuDropdown.classList.contains('visible');
    if (isVisible) {
        closeMoreMenu();
    } else {
        openMoreMenu();
    }
}

function openMoreMenu() {
    closeMoreMenu(); // 먼저 닫기
    moreMenuDropdown.classList.remove('hidden');
    moreMenuDropdown.classList.add('visible');
    moreMenuBtn.classList.add('active');

    // 토큰 정보, 연결 상태, 세션 정보 동기화
    syncMoreMenuStatus();
}

function closeMoreMenu() {
    moreMenuDropdown.classList.remove('visible');
    moreMenuDropdown.classList.add('hidden');
    moreMenuBtn.classList.remove('active');
}

function syncMoreMenuStatus() {
    // 토큰 정보
    const tokenInfo = document.getElementById('tokenInfo');
    const moreTokenInfo = document.getElementById('moreTokenInfo');
    if (tokenInfo && moreTokenInfo) {
        moreTokenInfo.textContent = tokenInfo.textContent;
    }

    // 연결 상태
    const statusIndicator = document.getElementById('statusIndicator');
    const moreStatusIndicator = document.getElementById('moreStatusIndicator');
    const statusText = document.getElementById('statusText');
    const moreStatusText = document.getElementById('moreStatusText');
    if (statusIndicator && moreStatusIndicator) {
        moreStatusIndicator.className = statusIndicator.className;
    }
    if (statusText && moreStatusText) {
        moreStatusText.textContent = statusText.textContent;
    }

    // 세션 상태
    const sessionBadge = document.getElementById('sessionBadge');
    const moreSessionBadgeText = document.getElementById('moreSessionBadgeText');
    if (sessionBadge && moreSessionBadgeText) {
        moreSessionBadgeText.textContent = sessionBadge.textContent.replace('세션: ', '');
        moreSessionBadgeText.className = sessionBadge.className;
    }
}

// 더보기 메뉴 아이템 클릭 이벤트
document.getElementById('moreSettingsBtn')?.addEventListener('click', () => {
    closeMoreMenu();
    const settingsModal = document.getElementById('settingsModal');
    settingsModal?.classList.remove('hidden');
    enableFocusTrap(settingsModal);
});

document.getElementById('moreParticipantsBtn')?.addEventListener('click', () => {
    closeMoreMenu();
    openParticipantsModal();
});

document.getElementById('moreClearHistoryBtn')?.addEventListener('click', () => {
    closeMoreMenu();
    document.getElementById('clearHistoryBtn')?.click();
});

document.getElementById('moreResetSessionsBtn')?.addEventListener('click', () => {
    closeMoreMenu();
    document.getElementById('resetSessionsBtn')?.click();
});

// 로그아웃 버튼
document.getElementById('logoutBtn')?.addEventListener('click', () => {
    closeMoreMenu();
    handleLogout();
});

function handleLogout() {
    if (confirm('로그아웃하시겠습니까?')) {
        // WebSocket 연결 끊기
        if (ws) {
            ws.close();
        }

        // 로그인 상태 초기화
        localStorage.removeItem('savedUsername');
        localStorage.removeItem('savedPassword');
        localStorage.removeItem('rememberMe');
        localStorage.removeItem('autoLogin');

        // 로그인 모달 표시
        const loginModal = document.getElementById('loginModal');
        if (loginModal) {
            loginModal.classList.remove('hidden');
        }

        // 페이지 새로고침
        setTimeout(() => {
            location.reload();
        }, 500);
    }
}

// 문서 전체 클릭 시 더보기 메뉴 닫기
document.addEventListener('click', (e) => {
    if (moreMenuDropdown && !moreMenuDropdown.contains(e.target) && e.target !== moreMenuBtn) {
        closeMoreMenu();
    }
});

function openMobilePanel(panel) {
    closeMobilePanel(); // 먼저 기존 패널 닫기

    if (panel === 'left' && leftPanel) {
        leftPanel.classList.add('mobile-visible');
        currentMobilePanel = 'left';
        if (hamburgerBtn) {
            hamburgerBtn.classList.add('active');
        }
    } else if (panel === 'right' && rightPanel) {
        rightPanel.classList.add('mobile-visible');
        currentMobilePanel = 'right';
        if (narrativeMenuBtn) {
            narrativeMenuBtn.classList.add('active');
        }
    }

    if (mobileOverlay) {
        mobileOverlay.classList.add('active');
    }
}

function closeMobilePanel() {
    if (leftPanel) {
        leftPanel.classList.remove('mobile-visible');
    }
    if (rightPanel) {
        rightPanel.classList.remove('mobile-visible');
    }
    if (mobileOverlay) {
        mobileOverlay.classList.remove('active');
    }
    if (hamburgerBtn) {
        hamburgerBtn.classList.remove('active');
    }
    if (narrativeMenuBtn) {
        narrativeMenuBtn.classList.remove('active');
    }
    currentMobilePanel = null;
}

// ===== 스와이프 제스처 =====
let touchStartX = 0;
let touchStartY = 0;
let touchStartTime = 0;
const SWIPE_THRESHOLD = 50; // 최소 이동 거리 (px)
const SWIPE_VELOCITY_THRESHOLD = 0.3; // 최소 속도 (px/ms)
const SWIPE_MAX_VERTICAL_RATIO = 0.5; // 수직 이동 비율 제한

function handleTouchStart(e) {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
    touchStartTime = Date.now();
}

function handleTouchEnd(e) {
    if (!currentMobilePanel) return;

    const touchEndX = e.changedTouches[0].clientX;
    const touchEndY = e.changedTouches[0].clientY;
    const touchEndTime = Date.now();

    const deltaX = touchEndX - touchStartX;
    const deltaY = touchEndY - touchStartY;
    const deltaTime = touchEndTime - touchStartTime;

    // 수직 이동이 너무 크면 스와이프로 인식하지 않음
    if (Math.abs(deltaY) > Math.abs(deltaX) * SWIPE_MAX_VERTICAL_RATIO) {
        return;
    }

    const distance = Math.abs(deltaX);
    const velocity = distance / deltaTime;

    // 최소 거리 또는 최소 속도 조건 만족 시 스와이프로 인식
    if (distance < SWIPE_THRESHOLD && velocity < SWIPE_VELOCITY_THRESHOLD) {
        return;
    }

    // 좌측 패널: 좌측으로 스와이프 → 닫기
    if (currentMobilePanel === 'left' && deltaX < 0) {
        closeMobilePanel();
    }

    // 우측 패널: 우측으로 스와이프 → 닫기
    if (currentMobilePanel === 'right' && deltaX > 0) {
        closeMobilePanel();
    }
}

// 패널에 스와이프 이벤트 리스너 추가
if (leftPanel) {
    leftPanel.addEventListener('touchstart', handleTouchStart, { passive: true });
    leftPanel.addEventListener('touchend', handleTouchEnd, { passive: true });
}

if (rightPanel) {
    rightPanel.addEventListener('touchstart', handleTouchStart, { passive: true });
    rightPanel.addEventListener('touchend', handleTouchEnd, { passive: true });
}

// 오버레이 클릭 시 패널 닫기
if (mobileOverlay) {
    mobileOverlay.addEventListener('click', closeMobilePanel);
}

// 서사 패널을 여는 기능 추가 (필요 시)
// 예: 서사 버튼 클릭 시 우측 패널 열기
// 이 기능은 필요에 따라 나중에 추가할 수 있습니다.

// ===== 초기화 =====

window.addEventListener('load', async () => {
    await loadAppConfig();
    // UI 초기 상태 강제 정리 (헤더 가려짐 방지)
    document.getElementById('settingsModal')?.classList.add('hidden');
    document.getElementById('characterEditorModal')?.classList.add('hidden');
    document.getElementById('moreMenuDropdown')?.classList.add('hidden');
    document.getElementById('mobileOverlay')?.classList.remove('active');
    document.getElementById('participantsModal')?.classList.add('hidden');

    // 인증 상태에 따라 로그인/로그아웃 버튼 가시성 설정
    const savedToken = localStorage.getItem(AUTH_TOKEN_KEY);
    const savedExp = localStorage.getItem(AUTH_EXP_KEY);
    if (savedToken && savedExp && new Date(savedExp) > new Date()) {
        authToken = savedToken;
        authTokenExpiresAt = savedExp;
        isAuthenticated = true;
        userRole = localStorage.getItem(USER_ROLE_KEY) || 'user';
        loginBtn.style.display = 'none';
        moreLoginBtn.style.display = 'none';
        logoutBtn.style.display = 'block';
        moreLogoutBtn.style.display = 'block';
        if (userRole === 'admin') {
            adminBtn.style.display = 'block';
            moreAdminBtn.style.display = 'block';
        }
    } else {
        loginBtn.style.display = 'block';
        moreLoginBtn.style.display = 'block';
        logoutBtn.style.display = 'none';
        moreLogoutBtn.style.display = 'none';
        adminBtn.style.display = 'none';
        moreAdminBtn.style.display = 'none';
    }

    connect();
    // 연결 전이라도 라우트 화면을 먼저 표시(데이터는 연결 후 갱신)
    try { renderCurrentScreenFrom(location.pathname); } catch (_) {}
});
// 서사(=채팅방) 선택 시 방 전환 처리
// stories UI는 비활성화 상태이므로 관련 이벤트 없음

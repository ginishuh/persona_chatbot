// WebSocket 연결
let ws = null;
let appConfig = {
    ws_url: '',
    ws_port: 8765,
    login_required: false,
    show_token_usage: true
};

// DOM 요소
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const logArea = document.getElementById('logArea');

// 채팅 관련 요소
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendChatBtn = document.getElementById('sendChatBtn');

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
// 채팅방 UI
const roomSelect = document.getElementById('roomSelect');
const roomAddBtn = document.getElementById('roomAddBtn');
const roomDelBtn = document.getElementById('roomDelBtn');
const roomSaveBtn = document.getElementById('roomSaveBtn');

// 로그인 요소
const loginModal = document.getElementById('loginModal');
const loginUsernameInput = document.getElementById('loginUsername');
const loginPasswordInput = document.getElementById('loginPassword');
const rememberIdCheckbox = document.getElementById('rememberId');
const autoLoginCheckbox = document.getElementById('autoLogin');
const loginButton = document.getElementById('loginButton');
const autoLoginButton = document.getElementById('autoLoginButton');
const loginError = document.getElementById('loginError');
const loginAdultConsent = document.getElementById('loginAdultConsent');

let currentAssistantMessage = null;
let characterColors = {}; // 캐릭터별 색상 매핑
let authRequired = false;
let isAuthenticated = false;
let currentProvider = 'claude'; // 최근 전송에 사용한 프로바이더
let participants = []; // 현재 대화 참여자 목록
let pendingConsentResend = false; // 성인 동의 직후 직전 요청 재전송

const AUTH_TOKEN_KEY = 'persona_auth_token';
const AUTH_EXP_KEY = 'persona_auth_exp';
const REFRESH_TOKEN_KEY = 'persona_refresh_token';
const REFRESH_EXP_KEY = 'persona_refresh_exp';
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
let rooms = ['default'];
let currentRoom = 'default';
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
    authToken = sessionStorage.getItem(AUTH_TOKEN_KEY) || '';
    authTokenExpiresAt = sessionStorage.getItem(AUTH_EXP_KEY) || '';
    refreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY) || '';
    refreshTokenExpiresAt = sessionStorage.getItem(REFRESH_EXP_KEY) || '';
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
            sessionStorage.setItem(AUTH_TOKEN_KEY, authToken);
            if (authTokenExpiresAt) {
                sessionStorage.setItem(AUTH_EXP_KEY, authTokenExpiresAt);
            } else {
                sessionStorage.removeItem(AUTH_EXP_KEY);
            }
        } else {
            sessionStorage.removeItem(AUTH_TOKEN_KEY);
            sessionStorage.removeItem(AUTH_EXP_KEY);
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
            sessionStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
            if (refreshTokenExpiresAt) {
                sessionStorage.setItem(REFRESH_EXP_KEY, refreshTokenExpiresAt);
            } else {
                sessionStorage.removeItem(REFRESH_EXP_KEY);
            }
        } else {
            sessionStorage.removeItem(REFRESH_TOKEN_KEY);
            sessionStorage.removeItem(REFRESH_EXP_KEY);
        }
    } catch (_) { /* ignore */ }
}

// ===== History API Router (스켈레톤) =====
// 간단한 경로 → 화면 매핑. 현재 단계에서는 기존 화면 구조를 유지하면서 URL만 관리합니다.
const routeTable = [
    { pattern: /^\/$/, view: 'room-list' },
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
    return { view: 'room-list', params: [] };
}

function renderCurrentScreenFrom(pathname) {
    const { view, params } = parsePathname(pathname);
    // 최소 동작: URL이 /rooms/:id 계열이면 현재 방만 전환하고 기존 UI 그대로 사용
    if (view.startsWith('room-') && params[0]) {
        const rid = decodeURIComponent(params[0]);
        if (currentRoom !== rid) {
            currentRoom = rid;
            persistRooms();
            renderRoomsUI();
            sendMessage({ action: 'room_load', room_id: currentRoom });
            sendMessage({ action: 'reset_sessions', room_id: currentRoom });
            refreshRoomViews();
        }
    }
    // 추후: 각 view별 전용 렌더러 연결 예정
}

function navigate(path) {
    window.history.pushState({ path }, '', path);
    renderCurrentScreenFrom(location.pathname);
}

window.addEventListener('popstate', () => renderCurrentScreenFrom(location.pathname));

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
        isAuthenticated = false;
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
        message.room_id = currentRoom || 'default';
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
    loadStoryList();
}

// ===== 채팅방 관리 =====
function sanitizeRoomName(name) {
    return (name || '').trim().replace(/[^A-Za-z0-9_\-]/g, '_') || 'default';
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
    (rooms || []).forEach(r => {
        const roomId = typeof r === 'string' ? r : (r.room_id || r.title || 'default');
        const title = (typeof r === 'object' && r.title) ? r.title : roomId;
        const opt = document.createElement('option');
        opt.value = roomId;
        opt.textContent = title;
        roomSelect.appendChild(opt);
    });
    const hasCurrent = (rooms || []).some(x => (typeof x === 'string' ? x : x.room_id) === currentRoom);
    if (!hasCurrent) currentRoom = 'default';
    roomSelect.value = currentRoom;
}

function refreshRoomViews() {
    sendMessage({ action: 'get_narrative' });
    sendMessage({ action: 'get_history_settings' });
    sendMessage({ action: 'get_history_snapshot' });
    loadStoryList();
}

if (roomSelect) {
    roomSelect.addEventListener('change', () => {
        currentRoom = roomSelect.value || 'default';
        persistRooms();
        // 방 설정 로드 시도
        sendMessage({ action: 'room_load', room_id: currentRoom });
        // 방 전환 시 해당 방의 프로바이더 세션 초기화(신규 프롬프트 적용)
        sendMessage({ action: 'reset_sessions', room_id: currentRoom });
        // 서사/히스토리 뷰 갱신
        refreshRoomViews();
        log(`채팅방 전환: ${currentRoom}`, 'info');
    });
}
if (roomAddBtn) {
    roomAddBtn.addEventListener('click', () => {
        const name = prompt('새 채팅방 이름', 'room_' + Math.random().toString(36).slice(2, 6));
        if (!name) return;
        const r = sanitizeRoomName(name);
        if (!rooms.find(x => (typeof x === 'string' ? x : x.room_id) === r)) rooms.push(r);
        currentRoom = r;
        persistRooms();
        renderRoomsUI();
        // 현재 설정으로 방 저장
        const config = collectRoomConfig(r);
        sendMessage({ action: 'room_save', room_id: r, config });
        setTimeout(() => sendMessage({ action: 'room_list' }), 300);
        refreshRoomViews();
        log(`채팅방 추가: ${r}`, 'success');
    });
}
if (roomDelBtn) {
    roomDelBtn.addEventListener('click', () => {
        if (currentRoom === 'default') {
            alert('기본 채팅방은 삭제할 수 없습니다.');
            return;
        }
        if (!confirm(`채팅방 '${currentRoom}' 설정을 삭제하시겠습니까? (서사 파일은 보존)`)) return;
        sendMessage({ action: 'room_delete', room_id: currentRoom });
        rooms = rooms.filter(r => (typeof r === 'string' ? r : r.room_id) !== currentRoom);
        currentRoom = 'default';
        persistRooms();
        renderRoomsUI();
        refreshRoomViews();
        log('채팅방 삭제 완료', 'success');
    });
}
if (roomSaveBtn) {
    roomSaveBtn.addEventListener('click', () => {
        const r = currentRoom || 'default';
        const config = collectRoomConfig(r);
        sendMessage({ action: 'room_save', room_id: r, config });
        setTimeout(() => sendMessage({ action: 'room_list' }), 300);
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
        sendMessage({ action: 'login' });
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
    // 아이디/체크박스 초기화
    try {
        const savedUser = localStorage.getItem(LOGIN_USER_KEY) || '';
        if (loginUsernameInput) loginUsernameInput.value = savedUser;
        const auto = localStorage.getItem(LOGIN_AUTOLOGIN_KEY) === '1';
        if (rememberIdCheckbox) rememberIdCheckbox.checked = !!savedUser;
        if (autoLoginCheckbox) autoLoginCheckbox.checked = auto;
        if (loginAdultConsent) loginAdultConsent.checked = (localStorage.getItem(LOGIN_ADULT_KEY) === '1');
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
}

function submitLogin() {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const username = (loginUsernameInput?.value || '').trim();
    const password = loginPasswordInput.value.trim();
    if (!password) {
        loginError.textContent = '비밀번호를 입력하세요.';
        return;
    }
    const consent = loginAdultConsent ? !!loginAdultConsent.checked : false;
    sendMessage({
        action: 'login',
        username,
        password,
        adult_consent: consent ? true : undefined
    }, { skipToken: true });
    loginError.textContent = '';
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
if (autoLoginButton) {
    autoLoginButton.addEventListener('click', () => {
        try {
            const user = loginUsernameInput?.value || localStorage.getItem(LOGIN_USER_KEY) || '';
            const pw = localStorage.getItem(LOGIN_SAVED_PW_KEY) || '';
            if (!user || !pw) {
                alert('저장된 아이디/비밀번호가 없습니다. 먼저 로그인 후 자동 로그인을 설정하세요.');
                return;
            }
            const consent = localStorage.getItem(LOGIN_ADULT_KEY) === '1';
            sendMessage({ action: 'login', username: user, password: pw, adult_consent: consent || undefined }, { skipToken: true });
        } catch (e) {
            console.error(e);
        }
    });
}

// 메시지 처리
function handleMessage(msg) {
    const { action, data } = msg;

    switch (action) {
        case 'connected':
            log('서버 연결 완료', 'success');
            if (data && data.login_required) {
                authRequired = true;
                isAuthenticated = false;
                if (authToken) {
                    const consent = (localStorage.getItem(LOGIN_ADULT_KEY) === '1');
                    sendMessage({ action: 'login', adult_consent: consent || undefined });
                } else {
                    // 자동 로그인 시도
                    try {
                        const auto = localStorage.getItem(LOGIN_AUTOLOGIN_KEY) === '1';
                        const user = localStorage.getItem(LOGIN_USER_KEY) || '';
                        const pw = localStorage.getItem(LOGIN_SAVED_PW_KEY) || '';
                        if (auto && user && pw) {
                            const consent = (localStorage.getItem(LOGIN_ADULT_KEY) === '1');
                            sendMessage({ action: 'login', username: user, password: pw, adult_consent: consent || undefined }, { skipToken: true });
                        } else {
                            showLoginModal();
                        }
                    } catch (_) {
                        showLoginModal();
                    }
                }
            } else {
                authRequired = false;
                isAuthenticated = true;
                hideLoginModal();
                initializeAppData();
            }
            break;

        case 'auth_required':
            authRequired = true;
            isAuthenticated = false;
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
                log('로그인 성공', 'success');
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
                    if (loginAdultConsent && loginAdultConsent.checked) {
                        localStorage.setItem(LOGIN_ADULT_KEY, '1');
                    }
                } catch (_) {}
                // 직전 사용자 액션이 있었다면 우선 재전송
                if (lastRequest) {
                    const payload = { ...lastRequest };
                    sendMessage(payload, { skipRetry: true });
                    lastRequest = null;
                }
                initializeAppData();
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
                // 서버 컨텍스트에도 적용
                sendMessage({ action: 'set_context', ...ctx });
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
            if (data.success) {
                updateStoryList(data.files);
            } else {
                log(`서사 목록 로드 실패: ${data.error}`, 'error');
            }
            break;

        case 'save_story':
            if (data.success) {
                log(`서사 저장 완료: ${data.filename}`, 'success');
                loadStoryList(); // 목록 새로고침
            } else {
                log(`서사 저장 실패: ${data.error}`, 'error');
            }
            break;

        case 'load_story':
            if (data.success) {
                displayStoryContent(data.content);
                log(`서사 로드 완료: ${data.filename}`, 'success');
            } else {
                log(`서사 로드 실패: ${data.error}`, 'error');
            }
            break;

        case 'delete_story':
            if (data.success) {
                log(`서사 삭제 완료: ${data.filename}`, 'success');
                loadStoryList(); // 목록 새로고침
                narrativeContent.innerHTML = '<p class="placeholder">대화가 진행되면 여기에 서사가 기록됩니다.</p>';
            } else {
                log(`서사 삭제 실패: ${data.error}`, 'error');
            }
            break;

        case 'resume_from_story':
            if (data.success) {
                log(`이어하기 완료: 최근 ${data.injected_turns}턴 주입${data.summarized ? ' + 요약' : ''} (예상 토큰 ~${data.approx_tokens})`, 'success');
                // 주입 후 스냅샷 받아 채팅창 복원
                sendMessage({ action: 'get_history_snapshot' });
            } else {
                log(`이어하기 실패: ${data.error}`, 'error');
            }
            break;

        case 'get_history_snapshot':
            if (data.success) {
                renderHistorySnapshot(data.history || []);
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
        const r = currentRoom || 'default';
        const config = collectRoomConfig(r);
        sendMessage({ action: 'room_save', room_id: r, config });
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

// ===== 이벤트 리스너 =====

sendChatBtn.addEventListener('click', sendChatMessage);

chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
    }
});

// ===== 탭 전환 =====

// ===== 설정 모달 =====

const settingsModal = document.getElementById('settingsModal');
const settingsBtn = document.getElementById('settingsBtn');
const closeSettingsBtn = document.getElementById('closeSettingsBtn');
const settingsModalOverlay = document.querySelector('.settings-modal-overlay');

// 설정 모달 열기
if (settingsBtn) {
    settingsBtn.addEventListener('click', () => {
        settingsModal.classList.remove('hidden');
    });
}

// 설정 모달 닫기
if (closeSettingsBtn) {
    closeSettingsBtn.addEventListener('click', () => {
        settingsModal.classList.add('hidden');
    });
}

// 오버레이 클릭 시 모달 닫기
if (settingsModalOverlay) {
    settingsModalOverlay.addEventListener('click', () => {
        settingsModal.classList.add('hidden');
    });
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

    modal.classList.remove('hidden');
}

function closeCharacterEditor() {
    const modal = document.getElementById('characterEditorModal');
    modal.classList.add('hidden');
    currentEditingCharacterItem = null;
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
}

function closeParticipantsModal() {
    const modal = document.getElementById('participantsModal');
    if (modal) modal.classList.add('hidden');
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

// ===== 서사 관리 =====

// 서사 목록 로드
function loadStoryList() {
    sendMessage({ action: 'list_stories' });
}

// 서사 목록 업데이트
function updateStoryList(files) {
    const currentValue = storySelect.value;
    storySelect.innerHTML = '<option value="">채팅방 선택...</option>';

    files.forEach(file => {
        const option = document.createElement('option');
        option.value = file.name;
        option.textContent = file.name;
        storySelect.appendChild(option);
    });

    // 현재 선택 복원 또는 첫 항목 선택
    let desired = currentRoom || currentValue;
    const names = files.map(f => f.name);
    if (desired && names.includes(desired)) {
        storySelect.value = desired;
    } else if (names.length) {
        storySelect.value = names[0];
        desired = names[0];
    } else {
        storySelect.value = '';
        desired = 'default';
    }
    currentRoom = desired;
    try { localStorage.setItem(CURRENT_ROOM_KEY, currentRoom); } catch (_) {}
    latestStories = files || [];
    updateRoomListUI();
}

function updateRoomListUI() {
    if (!roomList) return;
    roomList.innerHTML = '';
    const q = (roomSearch?.value || '').trim();
    const items = (latestStories || []).filter(f => !q || f.name.includes(q));
    if (!items.length) {
        roomList.innerHTML = '<div class="empty">저장된 채팅방이 없습니다.</div>';
        return;
    }
    items.forEach(f => {
        const btn = document.createElement('button');
        btn.className = 'btn btn-sm';
        btn.style = 'width:100%; text-align:left; margin-bottom:4px;';
        btn.textContent = f.name;
        btn.title = `${f.name} (${Math.round((f.size || 0)/1024)} KB)`;
        btn.addEventListener('click', () => {
            storySelect.value = f.name;
            storySelect.dispatchEvent(new Event('change'));
        });
        roomList.appendChild(btn);
    });
}

// 서사 표시
function displayStoryContent(markdown) {
    // 간단한 마크다운 렌더링
    let html = markdown
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^---$/gm, '<hr>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/^(.+)$/gm, '<p>$1</p>');

    narrativeContent.innerHTML = html;
}

// 서사 로드 버튼
loadStoryBtn.addEventListener('click', () => {
    const filename = storySelect.value;
    if (!filename) {
        alert('불러올 서사를 선택하세요');
        return;
    }

    sendMessage({
        action: 'load_story',
        filename: filename
    });
});

// 서사 이어하기 버튼
if (resumeStoryBtn) {
    resumeStoryBtn.addEventListener('click', () => {
        const filename = storySelect.value;
        if (!filename) {
            alert('이어할 서사를 선택하세요');
            return;
        }
        // 불러올 턴 수: 기본 = 현재 슬라이더 값
        const defaultTurns = currentHistoryLimit || HISTORY_LIMIT_DEFAULT;
        const input = prompt('불러올 턴 수(최근 N턴):', String(defaultTurns));
        if (!input) return;
        const turns = Math.max(1, parseInt(input, 10) || defaultTurns);
        const summarize = confirm('이전 구간을 간단히 요약해서 포함할까요?');

        sendMessage({
            action: 'resume_from_story',
            filename: filename,
            turns: turns,
            summarize: summarize
        });
    });
}

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
    } catch (e) {
        console.error('renderHistorySnapshot error', e);
    }
}

// 서사 삭제 버튼
deleteStoryBtn.addEventListener('click', () => {
    const filename = storySelect.value;
    if (!filename) {
        alert('삭제할 서사를 선택하세요');
        return;
    }

    if (!confirm(`"${filename}" 서사를 삭제하시겠습니까?`)) {
        return;
    }

    sendMessage({
        action: 'delete_story',
        filename: filename
    });
});

// 서사 → 컨텍스트 주입 버튼
if (injectStoryBtn) {
    injectStoryBtn.addEventListener('click', () => {
        const text = narrativeContent.innerText || '';
        if (!text.trim()) {
            alert('주입할 서사가 없습니다. 먼저 서사를 불러오세요.');
            return;
        }
        // 기존 세계관에 서사를 덧붙임
        const sep = worldInput.value.trim() ? '\n\n---\n\n' : '';
        worldInput.value = worldInput.value + sep + text.trim();
        log('서사를 세계관에 주입했습니다. 좌측의 "설정 적용"을 눌러 반영하세요.', 'success');
    });
}

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
    connect();
});
// 서사(=채팅방) 선택 시 방 전환 처리
if (storySelect) {
    storySelect.addEventListener('change', () => {
        currentRoom = storySelect.value || 'default';
        try { localStorage.setItem(CURRENT_ROOM_KEY, currentRoom); } catch (_) {}
        // 방 전환: 세션 초기화 + 뷰 갱신
        sendMessage({ action: 'reset_sessions', room_id: currentRoom });
        refreshRoomViews();
        log(`채팅방 전환: ${currentRoom}`, 'info');
    });
}

if (roomSearch) {
    roomSearch.addEventListener('input', () => updateRoomListUI());
}

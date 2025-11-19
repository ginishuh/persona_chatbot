// ===== ES6 모듈 import =====
import { openModal, closeModal, toggleModal, isModalOpen } from './modules/ui/modals.js';
import { setAuthToken, clearAuthToken, setRefreshToken, login, register, logout } from './modules/auth/auth.js';
import {
    parsePathname,
    rememberPendingRoute,
    resumePendingRoute as routerResumePendingRoute,
    renderCurrentScreenFrom as routerRenderCurrentScreenFrom,
    navigate as routerNavigate,
    initRouter as routerInitRouter
} from './modules/routing/router.js';
import { showScreen, hideScreen } from './modules/ui/screens.js';
import { initA11y, enableFocusTrap, disableFocusTrap, announce, focusMainAfterRoute } from './modules/ui/a11y.js';
import { log, updateStatus, updateModelOptions } from './modules/ui/status.js';
import { initMobileUI, openMobilePanel, closeMoreMenu } from './modules/ui/mobile.js';
import { initExportModule, openBackupModal, renderBackupScreenView, downloadRoomMd } from './modules/export/export.js';
import { initAdminPanel, openAdminModal, closeAdminModal } from './modules/admin/admin.js';
import { connect, sendMessage, loadAppConfig } from './modules/websocket/connection.js';
import {
    ws, appConfig, setAppConfig,
    authRequired, setAuthRequired, isAuthenticated, setIsAuthenticated,
    authToken, setAuthTokenState,
    refreshToken, refreshTokenExpiresAt, setRefreshTokenState,
    rooms, currentRoom, setRooms, setCurrentRoom,
    participants, setParticipants,
    userRole, setUserRole,
    isReconnecting, setIsReconnecting,
    lastRequest, setLastRequest,
    autoLoginRequested, setAutoLoginRequested,
    sessionKey, setSessionKey,
    currentHistoryLimit,
    sessionSettingsLoaded,
    tokenRefreshTimeout, setTokenRefreshTimeout,
    refreshRetryCount, setRefreshRetryCount,
    refreshInProgress, setRefreshInProgress
} from './modules/core/state.js';
import {
    setPendingFileList,
    consumePendingFileList,
    setPendingTemplateSelect,
    consumePendingTemplateSelect,
    setPendingLoadType,
    getPendingLoadType,
    clearPendingLoadType,
    setPendingTemplateItem,
    consumePendingTemplateItem,
    setPendingTemplateModal,
    isPendingTemplateModal,
    setPendingAddFromTemplate,
    isPendingAddFromTemplate,
    clearPendingTemplateModal,
    clearPendingAddFromTemplate
} from './modules/files/pending.js';
import {
    refreshChatRefs, addChatMessage, addCharacterMessage,
    sendChatMessage, handleChatStream, handleChatComplete,
    bindChatEvents, updateChatInputState,
    updateTokenDisplay
} from './modules/chat/chat.js';
import {
    refreshRoomRefs, renderRoomsUI, renderRoomsRightPanelList, renderRoomsScreen,
    loadContext, collectRoomConfig, bindRoomEvents, populateRoomsModal,
    persistRooms, sanitizeRoomName
} from './modules/rooms/rooms.js';
import {
    AUTH_TOKEN_KEY, AUTH_EXP_KEY, REFRESH_TOKEN_KEY, REFRESH_EXP_KEY,
    USER_ROLE_KEY, SESSION_KEY_KEY, ROOMS_KEY, CURRENT_ROOM_KEY,
    RETRY_ACTIONS, MAX_REFRESH_RETRIES, HISTORY_LIMIT_DEFAULT
} from './modules/core/constants.js';

// router.js가 접근할 수 있도록 window에도 바인딩
window.__appConfig = appConfig;

// 컨텍스트 패널 요소 (Modules에서 관리하지 않는 나머지)
const contextContent = document.getElementById('contextContent');
const charactersList = document.getElementById('charactersList');
const addCharacterBtn = document.getElementById('addCharacterBtn');
const applyCharactersBtn = document.getElementById('applyCharactersBtn');
const saveContextBtn = document.getElementById('saveContextBtn');
const historyLengthSlider = document.getElementById('historyLengthSlider');
const historyLengthValue = document.getElementById('historyLengthValue');
const historyUnlimitedToggle = document.getElementById('historyUnlimitedToggle');

// 파일 관리 요소
const worldSelect = document.getElementById('worldSelect');
const saveWorldBtn = document.getElementById('saveWorldBtn');
const deleteWorldBtn = document.getElementById('deleteWorldBtn');
const worldInput = document.getElementById('worldInput');
const situationSelect = document.getElementById('situationSelect');
const saveSituationBtn = document.getElementById('saveSituationBtn');
const deleteSituationBtn = document.getElementById('deleteSituationBtn');
const situationInput = document.getElementById('situationInput');
const myCharacterSelect = document.getElementById('myCharacterSelect');
const saveMyCharacterBtn = document.getElementById('saveMyCharacterBtn');
const deleteMyCharacterBtn = document.getElementById('deleteMyCharacterBtn');
const userCharacterAgeInput = document.getElementById('userCharacterAge');
const userCharacterInput = document.getElementById('userCharacterInput');
const loadProfileJsonBtn = document.getElementById('loadProfileJsonBtn');
const saveProfileJsonBtn = document.getElementById('saveProfileJsonBtn');

// 채팅/세션 제어 요소
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendChatBtn = document.getElementById('sendChatBtn');
const aiProvider = document.getElementById('aiProvider');
const modelSelect = document.getElementById('modelSelect');
const narratorEnabled = document.getElementById('narratorEnabled');
const narratorMode = document.getElementById('narratorMode');
const narratorDescription = document.getElementById('narratorDescription');
const userIsNarrator = document.getElementById('userIsNarrator');
const narratorDrive = document.getElementById('narratorDrive');
const forceChoices = document.getElementById('forceChoices');
const choiceCount = document.getElementById('choiceCount');
const adultLevel = document.getElementById('adultLevel');
const narrativeSeparation = document.getElementById('narrativeSeparation');
const narratorSettings = document.getElementById('narratorSettings');
const outputLevel = document.getElementById('outputLevel');
const storyPace = document.getElementById('storyPace');
const adultConsent = document.getElementById('adultConsent');
const sessionRetentionToggle = document.getElementById('sessionRetentionToggle');

// 프리셋 관리 요소
const presetSelect = document.getElementById('presetSelect');
const savePresetBtn = document.getElementById('savePresetBtn');
const loadPresetBtn = document.getElementById('loadPresetBtn');
const deletePresetBtn = document.getElementById('deletePresetBtn');

// 헤더 버튼
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const resetSessionsBtn = document.getElementById('resetSessionsBtn');
const tokenText = document.getElementById('tokenText');
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

// 채팅방 UI (Modules에서 관리하지 않는 나머지)
const roomAddBtn = document.getElementById('roomAddBtn');
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
const backupBtn = document.getElementById('backupBtn');

// 모바일 더보기 메뉴의 로그인/로그아웃/관리 버튼
const moreLoginBtn = document.getElementById('moreLoginBtn');
const moreLogoutBtn = document.getElementById('moreLogoutBtn');
const moreAdminBtn = document.getElementById('moreAdminBtn');
const moreBackupBtn = document.getElementById('moreBackupBtn');

// 관리자 요소
const adminBtn = document.getElementById('adminBtn');
const adminModal = document.getElementById('adminModal');
const adminCloseBtn = document.getElementById('adminCloseBtn');

// 채팅방 이름 입력 모달 요소
const roomNameModal = document.getElementById('roomNameModal');
const roomNameInput = document.getElementById('roomNameInput');
const roomNameCloseBtn = document.getElementById('roomNameCloseBtn');
const roomNameCancelBtn = document.getElementById('roomNameCancelBtn');
const roomNameConfirmBtn = document.getElementById('roomNameConfirmBtn');

// Local State
let pendingConsentResend = false; // 성인 동의 직후 직전 요청 재전송
// tokenRefreshTimeout, refreshRetryCount, refreshInProgress imported from modules
// 로그인 저장 키
const LOGIN_USER_KEY = 'persona_login_user';
const LOGIN_AUTOLOGIN_KEY = 'persona_login_auto';
const LOGIN_SAVED_PW_KEY = 'persona_login_pw';
const LOGIN_ADULT_KEY = 'persona_login_adult';
// Tokens initialized in core/state.js


// buildWebSocketUrl, isTouchDevice imported from modules (if needed)


// setAuthToken, clearAuthToken, setRefreshToken imported from modules


// ===== History API Router (스켈레톤) =====
// 간단한 경로 → 화면 매핑. 현재 단계에서는 기존 화면 구조를 유지하면서 URL만 관리합니다.
// 라우팅 함수들은 router.js 모듈에서 가져옴
// handlers 객체 - router.js의 함수들에 전달할 의존성
const routingHandlers = {
    showLoginModal,
    hideScreen,
    openRoomsModal,
    openBackupModal,
    renderBackupScreenView,
    persistRooms,
    renderRoomsUI,
    refreshRoomViews,
    enableFocusTrap,
    openMobilePanel,
    focusMainAfterRoute,
    sendMessage  // router.js가 room_load/reset_sessions/get_context를 보내기 위해 필요
};

// renderCurrentScreenFrom, navigate, resumePendingRoute의 wrapper 함수
// 인라인 이벤트 핸들러와 기존 코드에서 사용할 수 있도록 handlers를 자동 주입
function renderCurrentScreenFrom(pathname) {
    routerRenderCurrentScreenFrom(pathname, routingHandlers);
}

function navigate(path) {
    routerNavigate(path, routingHandlers);
}

function resumePendingRoute() {
    routerResumePendingRoute(renderCurrentScreenFrom);
}

function initRouter(handlers) {
    routerInitRouter(handlers);
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

// ===== 전용 화면 컨테이너 토글 =====
// showScreen(), hideScreen()은 modules/ui/screens.js에서 import됨

// Rooms 화면
// `renderRoomsScreen` moved to `web/modules/rooms/rooms.js`

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
                    <button class="btn" id="roomBackBtn">← 방 목록</button>
                    <button class="btn" id="roomSettingsBtn">⚙️ 설정</button>
                    <button class="btn" id="roomHistoryBtn">📜 히스토리</button>
                </div>
      </section>`;
    showScreen(html);
        // bind navigation buttons
        document.getElementById('roomBackBtn')?.addEventListener('click', () => navigate('/'));
        document.getElementById('roomSettingsBtn')?.addEventListener('click', () => navigate(`/rooms/${encodeURIComponent(roomId)}/settings`));
        document.getElementById('roomHistoryBtn')?.addEventListener('click', () => navigate(`/rooms/${encodeURIComponent(roomId)}/history`));
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
                    <button class="btn" id="historyBackBtn">← 돌아가기</button>
                    <button class="btn" id="historyDownloadBtn">MD 다운로드</button>
          <a class="btn" href="${jsonUrl}" target="_blank">JSON</a>
          <a class="btn" href="${ndjsonUrl}" target="_blank">NDJSON</a>
        </div>
      </section>`;
    showScreen(html);
        document.getElementById('historyBackBtn')?.addEventListener('click', () => navigate(`/rooms/${encodeURIComponent(id)}`));
        document.getElementById('historyDownloadBtn')?.addEventListener('click', () => downloadRoomMd(id));
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



// ===== 방 목록(Home) 모달 =====
// `populateRoomsModal` moved to `web/modules/rooms/rooms.js`

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

// `renderRoomsRightPanelList` implementation moved to `web/modules/rooms/rooms.js`

const roomSearchInput = document.getElementById('roomSearch');
const roomSearchBtn = document.getElementById('roomSearchBtn');
if (roomSearchInput) {
    roomSearchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.isComposing) {
            renderRoomsRightPanelList();
        }
    });
}
if (roomSearchBtn) {
    roomSearchBtn.addEventListener('click', () => {
        renderRoomsRightPanelList();
    });
}

// 모델 옵션 갱신 - ui/status 모듈 사용

function startWebSocket() {
    connect({
        onConnected: () => {
            try { renderCurrentScreenFrom(location.pathname); } catch (_) {}
        },
        onMessage: (message) => handleMessage(message),
        onDisconnected: () => {
            hideLoginModal();
        },
        log,
        updateStatus
    });
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
// sanitizeRoomName, persistRooms, renderRoomsUI, updateChatInputState imported from modules


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
        setCurrentRoom(selectedValue);
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
        if (!(Array.isArray(rooms) ? rooms : []).find(x => (typeof x === 'string' ? x : x.room_id) === r)) {
            setRooms([...(Array.isArray(rooms) ? rooms : []), r]);
        }
        setCurrentRoom(r);
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
// collectRoomConfig imported from modules


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
            setAuthTokenState(data.access_token, data.access_exp);
            setRefreshTokenState(data.refresh_token, data.refresh_exp);

            localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
            localStorage.setItem(AUTH_EXP_KEY, data.access_exp);
            localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
            localStorage.setItem(REFRESH_EXP_KEY, data.refresh_exp);

            // 사용자 역할 저장
            setUserRole(data.role || 'user');
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

            setIsAuthenticated(true);
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
                setIsReconnecting(true); // 의도적인 재연결 표시
                ws.close();
            }
            startWebSocket();
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
                setAuthRequired(true);
                if (authToken) {
                    setIsAuthenticated(true);
                    hideLoginModal();
                    resumePendingRoute();
                    initializeAppData();
                } else {
                    setIsAuthenticated(false);
                    showLoginModal();
                }
            } else {
                setAuthRequired(false);
                setIsAuthenticated(true);
                hideLoginModal();
                resumePendingRoute();
                initializeAppData();
            }
            break;
        }

        case 'auth_required':
            setAuthRequired(true);
            setIsAuthenticated(false);
            if (appConfig.login_required) {
                rememberPendingRoute(location.pathname);
            }
            // refresh 토큰으로 자동 갱신 시도
            if (!refreshInProgress && refreshToken) {
                setRefreshInProgress(true);
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
                setAuthRequired(false);
                setIsAuthenticated(true);
                hideLoginModal();
                setRefreshRetryCount(0);
                if (data.token) {
                    setAuthToken(data.token, data.expires_at);
                }
                if (data.refresh_token) {
                    setRefreshToken(data.refresh_token, data.refresh_expires_at);
                }
                if (data.session_key) {
                    setSessionKey(data.session_key);
                    try { localStorage.setItem(SESSION_KEY_KEY, data.session_key); } catch (_) {}
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
                    setLastRequest(null);
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
            setRefreshInProgress(false);
            if (data.success) {
                if (data.token) setAuthToken(data.token, data.expires_at);
                if (data.refresh_token) setRefreshToken(data.refresh_token, data.refresh_expires_at);
                log('토큰 갱신 완료', 'success');
                if (lastRequest) {
                    const payload = { ...lastRequest };
                    sendMessage(payload, { skipRetry: true });
                    setLastRequest(null);
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
                setRooms(data.rooms || []);
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
                    try { console.debug('room_load: got history from server length:', Array.isArray(room.history) ? room.history.length : 0); } catch (_) {}
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
// addChatMessage, addTypingIndicator, removeTypingIndicator, sendChatMessage, handleChatStream, handleChatComplete, parseMultiCharacterResponse, getCharacterColor, addCharacterMessage imported from modules


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

// addCharacterInput imported from modules


// loadCharTemplateList, saveCharacterTemplateFromModal, slugify, composeDescription, collectCharacterFromItem imported from modules


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
        pace: storyPace ? storyPace.value : undefined,
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
            pace: storyPace ? storyPace.value : undefined,
            characters: characters,
            choice_policy: (forceChoices && forceChoices.checked) ? 'require' : 'off',
            choice_count: choiceCount ? parseInt(choiceCount.value, 10) || 3 : undefined
        });
        setTimeout(() => { applyCharactersBtn.disabled = false; }, 5000);
    });
}

// loadContext, applyContextToSettingsScreen, renderSettingsScreenView imported from modules



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
    setCurrentRoom(filename);
    try { localStorage.setItem(CURRENT_ROOM_KEY, currentRoom); } catch (_) {}
    // 서사 저장과 동시에 방 설정도 저장
    try {
        const config = collectRoomConfig(currentRoom);
        sendMessage({ action: 'room_save', room_id: currentRoom, config });
    } catch (_) {}
});

// updateHeaderTokenDisplay imported from modules (Note: module implementation might differ)


// ===== 이벤트 리스너 바인딩(동적) =====
// bindChatEvents imported from modules
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
        closeMoreMenu();
        showLoginModal();
    });
}

// 로그아웃 핸들러
function handleLogout() {
    clearAuthToken();
    setRefreshToken('', '');
    localStorage.removeItem(USER_ROLE_KEY);
    userRole = 'user';
    setIsAuthenticated(false);
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
    moreLogoutBtn.addEventListener('click', () => {
        closeMoreMenu();
        handleLogout();
    });
}

function navigateToBackupScreen() {
    try {
        navigate('/backup');
    } catch (error) {
        console.error('Failed to navigate to backup screen', error);
    }
}

if (backupBtn) {
    backupBtn.addEventListener('click', () => {
        navigateToBackupScreen();
    });
}
if (moreBackupBtn) {
    moreBackupBtn.addEventListener('click', () => {
        closeMoreMenu();
        navigateToBackupScreen();
    });
}

if (moreAdminBtn) {
    moreAdminBtn.addEventListener('click', () => closeMoreMenu());
}

// ===== 파일 관리 =====

// 파일 목록 응답 처리
function handleFileList(data) {
    const pfl = consumePendingFileList();
    if (pfl.select) {
        updateFileList(pfl.select, data.files);
    } else {
        const pts = consumePendingTemplateSelect();
        if (pts) {
            updateTemplateList(pts, data.files);
        }
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
    setPendingFileList(selectElement, fileType);
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
    const pLoadType = getPendingLoadType();
    if (pLoadType === 'world') {
        worldInput.value = content;
        worldSelect.value = filename.replace('.md', '');
    } else if (pLoadType === 'situation') {
        situationInput.value = content;
        situationSelect.value = filename.replace('.md', '');
    } else if (pLoadType === 'my_character') {
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
    } else if (pLoadType === 'char_template') {
        // 템플릿(JSON) 로드 → 모달 또는 캐릭터 아이템에 반영
        try {
            const obj = JSON.parse(content || '{}');
            if (isPendingAddFromTemplate()) {
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
            } else if (isPendingTemplateModal()) {
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
            } else {
                const pendingItem = consumePendingTemplateItem();
                if (pendingItem) {
                    const nameInput = pendingItem.querySelector('.character-name-input');
                    const genderSelect = pendingItem.querySelector('.character-gender-input');
                    const ageInput = pendingItem.querySelector('.character-age-input');
                    const descInput = pendingItem.querySelector('.character-description-input');
                    if (obj.name) nameInput.value = obj.name;
                    if (obj.gender !== undefined) genderSelect.value = obj.gender;
                    if (obj.age !== undefined) ageInput.value = obj.age;
                    if (obj.description !== undefined) descInput.value = obj.description;
                    else if (obj.summary !== undefined) descInput.value = obj.summary;
                }
            }
        } catch (e) {
            log('템플릿 JSON 파싱 실패', 'error');
        }
        clearPendingTemplateModal();
        clearPendingAddFromTemplate();
        clearPendingLoadType();
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
    setPendingLoadType(fileType);
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
        setPendingLoadType('my_profile');
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
        setPendingLoadType('char_template');
        setPendingTemplateModal(true);
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

// renderParticipantsLeftPanel, renderParticipantsManagerList imported from modules


// openParticipantEditor and event listeners imported from modules


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
        pace: storyPace ? storyPace.value : 'normal',
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
    setParticipants(Array.isArray(preset.characters) ? [...preset.characters] : []);
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
    if (storyPace && preset.pace) storyPace.value = preset.pace;
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
            const content = msg.content || '';
            if (role === 'assistant') {
                // 히스토리에서도 멀티 캐릭터 응답을 다시 파싱하여 말풍선 분리
                const parsed = parseMultiCharacterResponse(content);
                if (parsed.length > 0) {
                    parsed.forEach(p => {
                        const el = addCharacterMessage(p.character, p.text);
                        // 히스토리로부터 로드된 메시지는 영구 고정
                        el.dataset.permanent = 'true';
                    });
                    return;
                }
                const el = addChatMessage('assistant', content);
                el.dataset.permanent = 'true';
            } else {
                addChatMessage('user', content);
            }
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

// ===== 초기화 =====

window.addEventListener('load', async () => {
    await loadAppConfig();
    setAppConfig(appConfig);
    window.__appConfig = appConfig;
    initA11y();
    initExportModule();
    initAdminPanel({
        adminModal,
        adminBtn,
        moreAdminBtn,
        adminCloseBtn
    });
    initMobileUI({
        onOpenParticipants: openParticipantsModal,
        onClearHistory: () => document.getElementById('clearHistoryBtn')?.click(),
        onResetSessions: () => document.getElementById('resetSessionsBtn')?.click(),
        onLogout: handleLogout,
        onOpenBackup: navigateToBackupScreen
    });
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
        setAuthTokenState(savedToken, savedExp);
        setIsAuthenticated(true);
        setUserRole(localStorage.getItem(USER_ROLE_KEY) || 'user');
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

    // 라우터 초기화 (popstate 이벤트 리스너 등록)
    initRouter(routingHandlers);

    startWebSocket();
    // 연결 전이라도 라우트 화면을 먼저 표시(데이터는 연결 후 갱신)
    try { renderCurrentScreenFrom(location.pathname); } catch (_) {}
});
// 서사(=채팅방) 선택 시 방 전환 처리
// stories UI는 비활성화 상태이므로 관련 이벤트 없음

// ============================================================================
// ES 모듈: 핵심 API를 모듈로 export
// ============================================================================
// app.js의 내부 함수들을 모듈화된 방식으로 외부에서 사용할 수 있도록 내보냅니다.
// 전역 할당(window.*)은 `web/modules/main.js`에서 중앙 관리하도록 이전했습니다.

export {
    navigate,
    sendMessage,
    persistRooms,
    renderRoomsUI,
    sanitizeRoomName,
    collectRoomConfig,
    // UI 모달/스크린은 `web/modules/ui/*`로 분리되었으므로 더 이상 여기서 export하지 않습니다.
};

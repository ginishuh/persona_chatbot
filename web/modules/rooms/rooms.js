import { sendMessage } from '../websocket/connection.js';
import { log } from '../ui/status.js';
import { rooms, currentRoom, setRooms, setCurrentRoom, setParticipants, participants } from '../core/state.js';
import { navigate } from '../routing/router.js';
import { showScreen } from '../ui/screens.js';
import { enableFocusTrap, disableFocusTrap } from '../ui/a11y.js';
import { updateChatInputState } from '../chat/chat.js';
import { renderParticipantsLeftPanel, renderParticipantsManagerList } from '../chat/characters.js';
import { ROOMS_KEY, CURRENT_ROOM_KEY } from '../core/constants.js';
import { buildUserCharacterData } from '../utils/utils.js';

// DOM Elements
let roomSelect = null;
let roomList = null;
let roomSearch = null;
let roomSearchBtn = null;
let worldInput = null;
let situationInput = null;
let userCharacterInput = null;
let userCharacterName = null;
let narratorEnabled = null;
let narratorMode = null;
let narratorDescription = null;
let userIsNarrator = null;
let aiProvider = null;
let modelSelect = null;
let sessionRetentionToggle = null;
let adultLevel = null;
let narrativeSeparation = null;
let narratorDrive = null;
let outputLevel = null;
let storyPace = null;
let forceChoices = null;
let choiceCount = null;
let narratorSettings = null;
let conversationMode = null;
let singleSpeakerMode = null;
let autoTurnToggle = null;
let autoTurnDelay = null;
let autoTurnMax = null;
let autoSaveTimer = null;
let autoSaveBound = false;
const AUTO_SAVE_DELAY_MS = 1500;

function buildSetContextPayload(roomId) {
    const userName = userCharacterName ? userCharacterName.value.trim() : '';
    const userDesc = userCharacterInput ? userCharacterInput.value.trim() : '';
    const userCharacterData = buildUserCharacterData(userName, userDesc);

    const characters = Array.isArray(participants) ? participants : [];

    return {
        action: 'set_context',
        room_id: roomId,
        world: worldInput ? worldInput.value.trim() : '',
        situation: situationInput ? situationInput.value.trim() : '',
        user_character: userCharacterData,
        narrator_enabled: narratorEnabled ? !!narratorEnabled.checked : false,
        narrator_mode: narratorMode ? narratorMode.value : 'moderate',
        narrator_description: narratorDescription ? narratorDescription.value.trim() : '',
        user_is_narrator: userIsNarrator ? !!userIsNarrator.checked : false,
        ai_provider: aiProvider ? aiProvider.value : 'claude',
        model: modelSelect ? modelSelect.value : '',
        session_retention: sessionRetentionToggle ? !!sessionRetentionToggle.checked : false,
        adult_level: adultLevel ? adultLevel.value : 'explicit',
        conversation_mode: conversationMode && conversationMode.value ? conversationMode.value : undefined,
        single_speaker_mode: singleSpeakerMode ? !!singleSpeakerMode.checked : false,
        auto_turn_enabled: autoTurnToggle ? !!autoTurnToggle.checked : false,
        auto_turn_delay: autoTurnDelay ? (Number(autoTurnDelay.value) || 0) : 0,
        auto_turn_max: autoTurnMax ? autoTurnMax.value : '10',
        narrative_separation: narrativeSeparation ? !!narrativeSeparation.checked : false,
        narrator_drive: narratorDrive ? narratorDrive.value : undefined,
        output_level: outputLevel ? outputLevel.value : undefined,
        pace: storyPace ? storyPace.value : undefined,
        characters,
        choice_policy: (forceChoices && forceChoices.checked) ? 'require' : 'off',
        choice_count: choiceCount ? parseInt(choiceCount.value, 10) || 3 : undefined
    };
}

function triggerAutoSave(reason = 'change') {
    if (!currentRoom) return;
    if (autoSaveTimer) clearTimeout(autoSaveTimer);
    autoSaveTimer = setTimeout(() => {
        const payload = buildSetContextPayload(currentRoom);
        sendMessage(payload);
        try {
            const cfg = collectRoomConfig(currentRoom);
            sendMessage({ action: 'room_save', room_id: currentRoom, config: cfg });
        } catch (_) {}
    }, AUTO_SAVE_DELAY_MS);
}

export function refreshRoomRefs() {
    roomSelect = document.getElementById('roomSelect');
    roomList = document.getElementById('roomList');
    roomSearch = document.getElementById('roomSearch');
    roomSearchBtn = document.getElementById('roomSearchBtn');
    worldInput = document.getElementById('worldInput');
    situationInput = document.getElementById('situationInput');
    userCharacterInput = document.getElementById('userCharacterInput');
    userCharacterName = document.getElementById('userCharacterName');
    narratorEnabled = document.getElementById('narratorEnabled');
    narratorMode = document.getElementById('narratorMode');
    narratorDescription = document.getElementById('narratorDescription');
    userIsNarrator = document.getElementById('userIsNarrator');
    aiProvider = document.getElementById('aiProvider');
    modelSelect = document.getElementById('modelSelect');
    sessionRetentionToggle = document.getElementById('sessionRetentionToggle');
    adultLevel = document.getElementById('adultLevel');
    narrativeSeparation = document.getElementById('narrativeSeparation');
    narratorDrive = document.getElementById('narratorDrive');
    outputLevel = document.getElementById('outputLevel');
    storyPace = document.getElementById('storyPace');
    forceChoices = document.getElementById('forceChoices');
    choiceCount = document.getElementById('choiceCount');
    narratorSettings = document.getElementById('narratorSettings');
    conversationMode = document.getElementById('conversationMode');
    singleSpeakerMode = document.getElementById('singleSpeakerMode');
    autoTurnToggle = document.getElementById('autoTurnToggle');
    autoTurnDelay = document.getElementById('autoTurnDelay');
    autoTurnMax = document.getElementById('autoTurnMax');
    autoTurnToggle = document.getElementById('autoTurnToggle');
    autoTurnDelay = document.getElementById('autoTurnDelay');
    autoTurnMax = document.getElementById('autoTurnMax');
    singleSpeakerMode = document.getElementById('singleSpeakerMode');

    bindAutoSaveInputs();
}

function bindAutoSaveInputs() {
    if (autoSaveBound) return;
    autoSaveBound = true;

    const listen = (el, events = ['input']) => {
        if (!el) return;
        events.forEach((ev) => el.addEventListener(ev, () => triggerAutoSave(ev)));
    };

    [worldInput, situationInput, userCharacterInput, userCharacterName].forEach(el => listen(el));
    [narratorDescription].forEach(el => listen(el));
    listen(narratorEnabled, ['change']);
    listen(narratorMode, ['change']);
    listen(userIsNarrator, ['change']);
    listen(aiProvider, ['change']);
    listen(modelSelect, ['change']);
    listen(sessionRetentionToggle, ['change']);
    listen(adultLevel, ['change']);
    listen(narrativeSeparation, ['change']);
    listen(narratorDrive, ['change']);
    listen(outputLevel, ['change']);
    listen(storyPace, ['change']);
    listen(forceChoices, ['change']);
    listen(choiceCount, ['input', 'change']);
    listen(conversationMode, ['change']);
    listen(singleSpeakerMode, ['change']);
    listen(autoTurnToggle, ['change']);
    listen(autoTurnDelay, ['change']);
    listen(autoTurnMax, ['change']);
    listen(autoTurnToggle, ['change']);
    listen(autoTurnDelay, ['change']);
    listen(autoTurnMax, ['change']);
    listen(singleSpeakerMode, ['change']);

    // 캐릭터 목록 변경 시 자동 저장 (전역 이벤트)
    try {
        window.addEventListener('participants:updated', () => triggerAutoSave('participants'));
    } catch (_) {}
}

export function sanitizeRoomName(name) {
    // 한글, 영문, 숫자, 공백, 밑줄, 하이픈 허용
    const sanitized = (name || '').trim().replace(/[^\uAC00-\uD7A3A-Za-z0-9_\-\s]/g, '_');
    return sanitized || 'room_untitled';
}

export function persistRooms() {
    try {
        localStorage.setItem(ROOMS_KEY, JSON.stringify(rooms));
        localStorage.setItem(CURRENT_ROOM_KEY, currentRoom);
    } catch (_) {}
}

export function renderRoomsUI() {
    if (!roomSelect) refreshRoomRefs();
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
        // 방이 있지만 currentRoom이 없거나 유효하지 않으면 첫 번째 방 선택하고 즉시 로드
        const firstRoom = rooms[0];
        const extractedId = typeof firstRoom === 'string' ? firstRoom : (firstRoom.room_id || null);
        if (extractedId) {
            setCurrentRoom(extractedId);
            persistRooms();
            sendMessage({ action: 'room_load', room_id: extractedId });
            sendMessage({ action: 'reset_sessions', room_id: extractedId });
            try {
                // 기본 히스토리/서사 요청
                sendMessage({ action: 'get_history_snapshot', room_id: extractedId });
                sendMessage({ action: 'get_narrative', room_id: extractedId });
            } catch (_) {}
        }
        // room_id가 없으면 currentRoom을 null로 유지
    }

    roomSelect.value = currentRoom || '';
    if (currentRoom) {
        // announce(`채팅방 전환: ${currentRoom}`); // announce is global, maybe import or ignore
    }

    // 채팅 입력 상태 업데이트
    updateChatInputState(!!currentRoom);
}

export function renderRoomsScreen() {
    const items = (Array.isArray(rooms) ? rooms : []).map(r => {
        const rid = typeof r === 'string' ? r : (r.room_id || r.title || 'default');
        const title = (typeof r === 'object' && r.title) ? r.title : rid;
        return { rid, title };
    });
    const cards = items.map(it => `
            <button class="btn room-card" style="width:100%; text-align:left; margin-bottom:8px;" data-rid="${encodeURIComponent(it.rid)}">${it.title}</button>
        `).join('');
    const html = `
      <section aria-labelledby="roomsScreenTitle">
        <h1 id="roomsScreenTitle">채팅방</h1>
        <div style="max-width:720px; margin-top:0.5rem;">${cards || '<div class="empty">채팅방이 없습니다.</div>'}</div>
                <div style="margin-top:0.75rem; display:flex; gap:0.5rem;">
                    <button class="btn" id="roomsBackBtn">← 돌아가기</button>
                    <button class="btn btn-primary" id="roomsNewBtn">+ 새 채팅방</button>
                </div>
      </section>`;
    showScreen(html);
    // bind room card clicks
    document.querySelectorAll('.room-card').forEach(btn => {
        btn.addEventListener('click', () => {
            const rid = decodeURIComponent(btn.getAttribute('data-rid') || '');
            navigate(`/rooms/${encodeURIComponent(rid)}`);
        });
    });
    // back button
    document.getElementById('roomsBackBtn')?.addEventListener('click', () => {
        try { navigate(currentRoom ? `/rooms/${encodeURIComponent(currentRoom)}` : '/'); } catch (_) { navigate('/'); }
    });
    // new room button
    document.getElementById('roomsNewBtn')?.addEventListener('click', () => {
        const name = prompt('새 채팅방 이름','room_'+Math.random().toString(36).slice(2,6));
        if(!name) return;
        const r = sanitizeRoomName(name);
        if(!rooms.find(x => (typeof x === 'string' ? x : x.room_id) === r)) {
            setRooms([...(Array.isArray(rooms) ? rooms : []), r]);
        }
        setCurrentRoom(r);
        persistRooms();
        renderRoomsUI();
        try {
            const cfg = collectRoomConfig(r);
            sendMessage({ action: 'room_save', room_id: r, config: cfg });
            setTimeout(() => sendMessage({ action: 'room_list' }), 300);
        } catch (_) {}
        navigate(`/rooms/${encodeURIComponent(r)}`);
    });
}

export function populateRoomsModal() {
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
            // close modal directly (avoid cross-module function call)
            const modal = document.getElementById('roomsModal');
            if (modal) modal.classList.add('hidden');
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
            setTimeout(() => sendMessage({ action: 'room_list' }), 300);
            setRooms((Array.isArray(rooms) ? rooms : []).filter(r => (typeof r === 'string' ? r : r.room_id) !== it.rid));
            if (currentRoom === it.rid) {
                const next = (Array.isArray(rooms) && rooms.length > 0) ? (typeof rooms[0] === 'string' ? rooms[0] : rooms[0].room_id) : null;
                setCurrentRoom(next);
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

export function openRoomsModal() {
    const modal = document.getElementById('roomsModal');
    if (!modal) return;
    populateRoomsModal();
    modal.classList.remove('hidden');
    enableFocusTrap(modal);
}

export function closeRoomsModal() {
    const modal = document.getElementById('roomsModal');
    if (!modal) return;
    modal.classList.add('hidden');
    disableFocusTrap(modal);
}

export function renderRoomsRightPanelList() {
    if (!roomList) refreshRoomRefs();
    if (!roomList) return;

    const q = (roomSearch?.value || '').trim().toLowerCase();
    roomList.innerHTML = '';
    const items = (Array.isArray(rooms) ? rooms : []).map(r => {
        const rid = typeof r === 'string' ? r : (r.room_id || r.title || 'default');
        const title = (typeof r === 'object' && r.title) ? r.title : rid;
        return { rid, title };
    }).filter(x => !q || x.title.toLowerCase().includes(q) || x.rid.toLowerCase().includes(q));

    if (!items.length) {
        roomList.innerHTML = '<div class="empty">저장된 채팅방이 없습니다.</div>';
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
            const newRooms = rooms.filter(r => (typeof r === 'string' ? r : r.room_id) !== it.rid);
            setRooms(newRooms);

            if (currentRoom === it.rid) {
                const nextRoom = newRooms.length > 0 ? (typeof newRooms[0] === 'string' ? newRooms[0] : newRooms[0].room_id) : null;
                setCurrentRoom(nextRoom);
            }
            persistRooms();
            renderRoomsUI();
            renderRoomsRightPanelList();
            // refreshRoomViews(); // global function, maybe ignore or import
            log('채팅방 삭제 완료', 'success');
        });

        container.appendChild(btn);
        container.appendChild(delBtn);
        roomList.appendChild(container);
    });
}

export function loadContext(context) {
    if (!worldInput) refreshRoomRefs();

    if (worldInput) worldInput.value = context.world || '';
    if (situationInput) situationInput.value = context.situation || '';

    // 사용자 캐릭터 정보 파싱
    const userChar = context.user_character || '';
    try {
        let body = userChar;
        const lines = (userChar || '').split(/\r?\n/);
        if (lines.length && /^\s*이름\s*:\s*/.test(lines[0])) {
            const meta = lines[0];
            body = lines.slice(1).join('\n');
            const mName = meta.match(/이름\s*:\s*([^,\n]+)/);
            if (userCharacterName) userCharacterName.value = mName ? mName[1].trim() : '';
        }
        if (userCharacterInput) userCharacterInput.value = (body || '').trim();
    } catch (_) {
        if (userCharacterInput) userCharacterInput.value = userChar;
    }

    if (narratorEnabled) narratorEnabled.checked = context.narrator_enabled || false;
    if (narratorMode) narratorMode.value = context.narrator_mode || 'moderate';
    if (narratorDescription) narratorDescription.value = context.narrator_description || '';
    if (userIsNarrator) userIsNarrator.checked = context.user_is_narrator || false;
    if (aiProvider) aiProvider.value = context.ai_provider || 'claude';

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

    if (adultLevel) adultLevel.value = context.adult_level || 'explicit';
    if (narrativeSeparation) narrativeSeparation.checked = context.narrative_separation || false;
    if (narratorDrive) narratorDrive.value = context.narrator_drive || 'guide';
    if (outputLevel) outputLevel.value = context.output_level || 'normal';
    if (storyPace) storyPace.value = context.pace || 'normal';
    if (forceChoices) forceChoices.checked = (context.choice_policy || 'off') === 'require';
    if (choiceCount) choiceCount.value = String(context.choice_count || 3);
    if (conversationMode) conversationMode.value = context.conversation_mode || 'trpg_multi';
    if (singleSpeakerMode) singleSpeakerMode.checked = !!context.single_speaker_mode;
    if (autoTurnToggle) autoTurnToggle.checked = !!context.auto_turn_enabled;
    if (autoTurnDelay && context.auto_turn_delay) autoTurnDelay.value = String(context.auto_turn_delay);
    if (autoTurnMax && context.auto_turn_max !== undefined) autoTurnMax.value = String(context.auto_turn_max);

    try { window.dispatchEvent(new Event('autoTurn:updated')); } catch (_) {}
    if (autoTurnToggle) autoTurnToggle.checked = !!context.auto_turn_enabled;
    if (autoTurnDelay && context.auto_turn_delay) autoTurnDelay.value = String(context.auto_turn_delay);
    if (autoTurnMax && context.auto_turn_max !== undefined) autoTurnMax.value = String(context.auto_turn_max);

    // 진행자 설정 표시/숨김
    if (narratorEnabled && narratorEnabled.checked) {
        if (narratorSettings) narratorSettings.style.display = 'block';
    }

    // 참여자 로드 및 렌더링
    const newParticipants = Array.isArray(context.characters) ? [...context.characters] : [];
    // 로드 시에는 자동 저장을 트리거하지 않도록 silent
    setParticipants(newParticipants, { silent: true });
    renderParticipantsLeftPanel();
    renderParticipantsManagerList();
}

export function collectRoomConfig(roomId) {
    if (!userCharacterName) refreshRoomRefs();

    const userName = userCharacterName ? userCharacterName.value.trim() : '';
    const userDesc = userCharacterInput ? userCharacterInput.value.trim() : '';
    const userCharacterData = buildUserCharacterData(userName, userDesc);

    return {
        room_id: roomId,
        title: roomId,
        context: {
            world: worldInput ? worldInput.value.trim() : '',
            situation: situationInput ? situationInput.value.trim() : '',
            user_character: userCharacterData,
            characters: Array.isArray(participants) ? [...participants] : [],
            narrator_enabled: narratorEnabled ? !!narratorEnabled.checked : false,
            narrator_mode: narratorMode ? narratorMode.value : 'moderate',
            narrator_description: narratorDescription ? narratorDescription.value.trim() : '',
            user_is_narrator: userIsNarrator ? !!userIsNarrator.checked : false,
            ai_provider: aiProvider ? aiProvider.value : 'claude',
            model: modelSelect ? modelSelect.value : '',
            session_retention: sessionRetentionToggle ? !!sessionRetentionToggle.checked : false,
            adult_level: adultLevel ? adultLevel.value : 'explicit',
            narrative_separation: narrativeSeparation ? !!narrativeSeparation.checked : false,
            narrator_drive: narratorDrive ? narratorDrive.value : 'guide',
            output_level: outputLevel ? outputLevel.value : 'normal',
            pace: storyPace ? storyPace.value : 'normal',
            choice_policy: forceChoices && forceChoices.checked ? 'require' : 'off',
            choice_count: choiceCount ? parseInt(choiceCount.value, 10) : 3,
            conversation_mode: conversationMode ? conversationMode.value : 'trpg_multi',
            single_speaker_mode: singleSpeakerMode ? !!singleSpeakerMode.checked : false,
            auto_turn_enabled: autoTurnToggle ? !!autoTurnToggle.checked : false,
            auto_turn_delay: autoTurnDelay ? (Number(autoTurnDelay.value) || 0) : 0,
            auto_turn_max: autoTurnMax ? autoTurnMax.value : '10'
        }
    };
}

export function applyContextToSettingsScreen(ctx) {
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

export function renderSettingsScreenView(roomId) {
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
                        <button class="btn" id="sBackBtn">← 돌아가기</button>
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
    const back = document.getElementById('sBackBtn');

    back?.addEventListener('click', () => {
        navigate(`/rooms/${encodeURIComponent(roomId)}`);
    });

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

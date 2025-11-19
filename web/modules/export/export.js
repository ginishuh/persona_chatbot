/**
 * 백업/내보내기 모듈
 * @module export/export
 */

import { appConfig, authToken, sessionKey, rooms, currentRoom } from '../core/state.js';
import { showScreen } from '../ui/screens.js';
import { navigate } from '../routing/router.js';
import { enableFocusTrap, disableFocusTrap } from '../ui/a11y.js';

let backupModal = null;

const DEFAULT_INCLUDE = ['messages', 'context'];

function getActiveRoomId() {
    return currentRoom || window.currentRoom || '';
}

function listRoomMeta() {
    const source = Array.isArray(rooms) ? rooms : (Array.isArray(window.rooms) ? window.rooms : []);
    return source.map((entry) => {
        if (typeof entry === 'string') {
            return { id: entry, title: entry };
        }
        const id = entry?.room_id || entry?.title || 'default';
        const title = entry?.title || id;
        return { id, title };
    });
}

function appendRoomCheckbox(containerId, prefix) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    const items = listRoomMeta();
    if (!items.length) {
        container.innerHTML = '<p class="hint">저장된 방이 없습니다.</p>';
        return;
    }
    items.forEach(({ id, title }) => {
        const row = document.createElement('label');
        row.className = 'checkbox-label';
        row.innerHTML = `<input type="checkbox" value="${id}" id="${prefix}${id}"> <span>${title}</span>`;
        container.appendChild(row);
        if (id === getActiveRoomId()) {
            row.querySelector('input').checked = true;
        }
    });
}

function buildUrlFromControls(prefix) {
    const pick = (suffix) => document.getElementById(`${prefix}${suffix}`);
    const scopeFull = pick('ScopeFull');
    const scopeSelected = pick('ScopeSelected');
    const scopeSingle = pick('ScopeSingle');

    const scope = scopeFull?.checked ? 'full' : (scopeSelected?.checked ? 'selected' : 'single');
    const includeFlags = [];
    if (pick('IncMessages')?.checked ?? DEFAULT_INCLUDE.includes('messages')) includeFlags.push('messages');
    if (pick('IncContext')?.checked ?? DEFAULT_INCLUDE.includes('context')) includeFlags.push('context');
    if (pick('IncToken')?.checked) includeFlags.push('token_usage');

    const startInput = pick('Start');
    const endInput = pick('End');
    const fmtNdjson = pick('FmtNdjson');
    const fmtZip = pick('FmtZip');

    const params = new URLSearchParams();
    params.set('scope', scope);

    if (scope === 'single') {
        const active = getActiveRoomId();
        if (!active) {
            alert('내보낼 채팅방을 선택해주세요.');
            return null;
        }
        params.set('room_id', active);
    }

    if (scope === 'selected') {
        const selector = prefix === 'bk' ? '#bkRoomsWrap' : '#sbkRoomsWrap';
        const selected = Array.from(document.querySelectorAll(`${selector} input[type="checkbox"]:checked`)).map((el) => el.value);
        if (selected.length) {
            params.set('room_ids', selected.join(','));
        } else if (getActiveRoomId()) {
            params.set('room_ids', getActiveRoomId());
        } else {
            alert('내보낼 채팅방을 선택해주세요.');
            return null;
        }
    }

    if (includeFlags.length) {
        params.set('include', includeFlags.join(','));
    }

    if (startInput?.value) params.set('start', startInput.value);
    if (endInput?.value) params.set('end', endInput.value);

    const useStream = fmtNdjson?.checked;
    if (!useStream && fmtZip?.checked) {
        params.set('format', 'zip');
    }

    if (appConfig.login_required && authToken) {
        params.set('token', authToken);
    } else if (sessionKey) {
        params.set('session_key', sessionKey);
    }

    const base = useStream ? '/api/export/stream' : '/api/export';
    return `${base}?${params.toString()}`;
}

export function buildExportUrl() {
    return buildUrlFromControls('bk');
}

export function buildExportUrlFrom(prefix = 'sbk') {
    return buildUrlFromControls(prefix);
}

export function populateBackupRooms() {
    appendRoomCheckbox('bkRoomsWrap', 'bk-room-');
}

export function populateBackupRoomsScreen() {
    appendRoomCheckbox('sbkRoomsWrap', 'sbk-room-');
}

export function openBackupModal() {
    backupModal = backupModal || document.getElementById('backupModal');
    if (!backupModal) return;
    populateBackupRooms();
    backupModal.classList.remove('hidden');
    enableFocusTrap(backupModal);
}

export function closeBackupModal() {
    backupModal = backupModal || document.getElementById('backupModal');
    if (!backupModal) return;
    backupModal.classList.add('hidden');
    disableFocusTrap(backupModal);
}

export function initExportModule(options = {}) {
    backupModal = options.backupModal || document.getElementById('backupModal');
    (options.closeBtn || document.getElementById('bkCloseBtn'))?.addEventListener('click', closeBackupModal);
    (options.overlay || document.querySelector('#backupModal .settings-modal-overlay'))?.addEventListener('click', closeBackupModal);
    (options.downloadBtn || document.getElementById('bkDownloadBtn'))?.addEventListener('click', () => {
        const url = buildExportUrl();
        if (!url) return;
        try { window.open(url, '_blank'); } catch (_) { location.href = url; }
    });

    ['bkScopeSingle', 'bkScopeSelected', 'bkScopeFull'].forEach((id) => {
        document.getElementById(id)?.addEventListener('change', () => {
            const wrap = document.getElementById('bkRoomsWrap');
            if (!wrap) return;
            const show = document.getElementById('bkScopeSelected')?.checked;
            wrap.style.display = show ? 'block' : 'none';
            if (show) populateBackupRooms();
        });
    });
}

export function renderBackupScreenView() {
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
        <button class="btn" onclick="navigate(window.currentRoom ? '/rooms/${encodeURIComponent(getActiveRoomId())}' : '/')">← 돌아가기</button>
        <button id="sbkDownloadBtn" class="btn btn-primary">⬇️ 다운로드</button>
      </div>
    </section>`;
    showScreen(html);

    document.getElementById('sbkDownloadBtn')?.addEventListener('click', () => {
        const url = buildExportUrlFrom('sbk');
        if (!url) return;
        try { window.open(url, '_blank'); } catch (_) { location.href = url; }
    });

    ['sbkScopeSingle', 'sbkScopeSelected', 'sbkScopeFull'].forEach((id) => {
        document.getElementById(id)?.addEventListener('change', () => {
            const wrap = document.getElementById('sbkRoomsWrap');
            if (!wrap) return;
            const show = document.getElementById('sbkScopeSelected')?.checked;
            wrap.style.display = show ? 'block' : 'none';
            if (show) populateBackupRoomsScreen();
        });
    });
}

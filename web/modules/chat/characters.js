/**
 * 캐릭터 관리 모듈
 * @module chat/characters
 */

import { participants, setParticipants, getCharacterColor } from '../core/state.js';
import { sendMessage } from '../websocket/connection.js';
import { slugify } from '../utils/utils.js';
import { openModal, closeModal } from '../ui/modals.js';
import { enableFocusTrap, disableFocusTrap } from '../ui/a11y.js';
import { setPendingTemplateSelect } from '../files/pending.js';
import { setLastEditorTrigger, focusLastEditorTrigger } from '../ui/last_focus.js';

// DOM 요소 참조 (initCharacters에서 설정)
let charactersListEl = null;
let participantsManagerListEl = null;
let currentEditingCharacterItem = null;

/**
 * 캐릭터 모듈 초기화
 * @param {Object} elements - DOM 요소들
 */
export function initCharacters(elements) {
    charactersListEl = elements.charactersList;
    participantsManagerListEl = elements.participantsManagerList;
}

/**
 * 멀티 캐릭터 응답 파싱
 * @param {string} text - 응답 텍스트
 * @returns {Array} 메시지 객체 배열
 */
export function parseMultiCharacterResponse(text) {
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

/**
 * 캐릭터 입력 UI 추가
 * @param {string} name
 * @param {string} description
 */
export function addCharacterInput(name = '', description = '') {
    if (!charactersListEl) return;

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

    // 이름 필드 (숨김)
    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.className = 'character-name-input character-name-field';
    nameInput.placeholder = '이름';
    nameInput.value = name;
    nameInput.style.display = 'none';

    // 설명 필드 (숨김)
    const descTextarea = document.createElement('textarea');
    descTextarea.className = 'character-description-input';
    descTextarea.placeholder = '성별, 나이, 성격, 말투, 배경 등...';
    descTextarea.value = description;
    descTextarea.style.display = 'none';

    // 표시용 요약 바
    const summaryBar = document.createElement('div');
    summaryBar.className = 'character-summary';
    summaryBar.style.fontSize = '0.9rem';
    summaryBar.style.color = '#475569';
    summaryBar.style.margin = '0.25rem 0 0.5rem 0';

    function updateSummary() {
        const nm = nameInput.value || '이름 없음';
        const snip = (descTextarea.value || '').slice(0, 60).replace(/\n/g, ' ');
        summaryBar.textContent = `${nm} — ${snip}`;
    }

    characterDiv.appendChild(header);
    characterDiv.appendChild(summaryBar);
    characterDiv.appendChild(nameInput);
    characterDiv.appendChild(descTextarea);
    charactersListEl.appendChild(characterDiv);

    updateSummary();
    // 요약은 값 변경 시 갱신되도록 이벤트 연결
    [nameInput, descTextarea].forEach(el => {
        el.addEventListener('input', updateSummary);
        el.addEventListener('change', updateSummary);
    });
}

/**
 * 템플릿 목록 로드
 * @param {HTMLElement} selectElement
 */
export function loadCharTemplateList(selectElement) {
    sendMessage({ action: 'list_workspace_files', file_type: 'char_template' });
    setPendingTemplateSelect(selectElement);
}

/**
 * 캐릭터 설명 조합 (단순화: 이름 + 내용만)
 */
export function composeDescription(base) {
    return base || '';
}

/**
 * 캐릭터 아이템에서 데이터 수집 (단순화: 이름 + 내용만)
 */
export function collectCharacterFromItem(item) {
    const name = item.querySelector('.character-name-input').value.trim();
    const description = item.querySelector('.character-description-input').value.trim();
    if (!name || !description) return null;
    return { name, description };
}

// ===== 캐릭터 에디터 모달 관련 =====

export function openCharacterEditor(characterDiv) {
    currentEditingCharacterItem = characterDiv;
    const ceName = document.getElementById('ceName');
    const ceSummary = document.getElementById('ceSummary');
    const nameInput = characterDiv.querySelector('.character-name-input');
    const descInput = characterDiv.querySelector('.character-description-input');

    // 값 채우기 (이름 + 내용만)
    ceName.value = nameInput.value || '';
    ceSummary.value = descInput.value || '';

    // 템플릿 목록 갱신
    loadCharTemplateList(document.getElementById('ceTemplateSelect'));

    try { setLastEditorTrigger(document.activeElement); } catch (_) {}
    openModal('characterEditorModal', true);
}

export function closeCharacterEditor() {
    closeModal('characterEditorModal', true);
    currentEditingCharacterItem = null;
    focusLastEditorTrigger();
}

export function applyCharacterEditorToItem() {
    if (!currentEditingCharacterItem) return;
    const ceName = document.getElementById('ceName');
    const ceSummary = document.getElementById('ceSummary');

    const nameInput = currentEditingCharacterItem.querySelector('.character-name-input');
    const descInput = currentEditingCharacterItem.querySelector('.character-description-input');

    nameInput.value = ceName.value.trim();
    descInput.value = ceSummary.value.trim();

    // 요약 갱신
    const summaryBar = currentEditingCharacterItem.querySelector('.character-summary');
    if (summaryBar) {
        const nm = nameInput.value || '이름 없음';
        const snip = (descInput.value || '').slice(0, 60).replace(/\n/g, ' ');
        summaryBar.textContent = `${nm} — ${snip}`;
    }

    closeCharacterEditor();
}

export function saveCharacterTemplateFromModal() {
    const name = document.getElementById('ceName').value.trim();
    const description = document.getElementById('ceSummary').value.trim();
    if (!name) { alert('이름을 입력하세요'); return; }
    const filename = prompt('템플릿 파일명(확장자 제외):', slugify(name));
    if (!filename) return;
    const payload = { name, role: 'npc', description };
    sendMessage({ action: 'save_workspace_file', file_type: 'char_template', filename, content: JSON.stringify(payload, null, 2) });
    // 모달의 템플릿 목록 갱신
    setTimeout(() => {
        const sel = document.getElementById('ceTemplateSelect');
        if (sel) loadCharTemplateList(sel);
    }, 500);
}

// ===== 참여자 관리 (전용 모달) =====

export function openParticipantsModal() {
    // 템플릿 목록 갱신 및 참여자 목록 렌더
    loadCharTemplateList(document.getElementById('pmTemplateSelect'));
    renderParticipantsManagerList();
    openModal('participantsModal', true);
}

export function closeParticipantsModal() {
    closeModal('participantsModal', true);
}

export function renderParticipantsLeftPanel() {
    if (!charactersListEl) return;
    charactersListEl.innerHTML = '';
    if (!Array.isArray(participants) || participants.length === 0) {
        const p = document.createElement('p');
        p.className = 'placeholder';
        p.textContent = '현재 참여자가 없습니다.';
        charactersListEl.appendChild(p);
        return;
    }
    participants.forEach((c, idx) => {
        const row = document.createElement('div');
        row.className = 'character-chip';
        row.style.padding = '6px 8px';
        row.style.marginBottom = '6px';
        row.style.border = '1px solid #e8ecef';
        row.style.borderRadius = '8px';
        row.style.background = '#fff';
        const nm = c.name || '이름 없음';
        const snip = (c.description || '').slice(0, 60).replace(/\n/g, ' ');
        row.textContent = `${nm} — ${snip}`;
        charactersListEl.appendChild(row);
    });
}

export function renderParticipantsManagerList() {
    if (!participantsManagerListEl) return;
    participantsManagerListEl.innerHTML = '';
    if (!Array.isArray(participants) || participants.length === 0) {
        participantsManagerListEl.innerHTML = '<p class="placeholder">참여자가 없습니다.</p>';
        return;
    }
    participants.forEach((c, idx) => {
        const row = document.createElement('div');
        row.style.display = 'flex';
        row.style.alignItems = 'center';
        row.style.gap = '0.5rem';
        row.style.margin = '4px 0';
        const info = document.createElement('div');
        info.style.flex = '1';
        info.textContent = `${c.name || '이름 없음'} — ${(c.description || '').slice(0,60).replace(/\n/g,' ')}`;
        const edit = document.createElement('button');
        edit.className = 'btn btn-sm';
        edit.textContent = '✏️ 편집';
        edit.onclick = () => openParticipantEditor(idx);
        const del = document.createElement('button');
        del.className = 'btn btn-sm btn-remove';
        del.textContent = '🗑️';
        del.onclick = () => {
            const newParticipants = [...participants];
            newParticipants.splice(idx,1);
            setParticipants(newParticipants);
            renderParticipantsLeftPanel();
            renderParticipantsManagerList();
        };
        row.appendChild(info);
        row.appendChild(edit);
        row.appendChild(del);
        participantsManagerListEl.appendChild(row);
    });
}

export function openParticipantEditor(index) {
    // 참여자 모달이 열려 있으면 닫고(오버레이 제거) 편집 모달을 연다
    closeParticipantsModal();
    // 채우고 모달 오픈 (이름 + 내용만)
    const c = (index != null && index >=0) ? participants[index] : { name:'', description:'' };
    document.getElementById('ceName').value = c.name || '';
    document.getElementById('ceSummary').value = c.description || '';
    loadCharTemplateList(document.getElementById('ceTemplateSelect'));
    openModal('characterEditorModal', true);

    // 저장 핸들러 재바인딩
    const saveBtn = document.getElementById('ceSaveBtn');
    saveBtn.onclick = () => {
        const name = document.getElementById('ceName').value.trim();
        const description = document.getElementById('ceSummary').value.trim();
        const obj = { name, description };

        const newParticipants = [...participants];
        if (index != null && index >= 0) newParticipants[index] = obj; else newParticipants.push(obj);
        setParticipants(newParticipants);

        renderParticipantsLeftPanel();
        renderParticipantsManagerList();
        closeCharacterEditor();
    };
}

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
 * @param {string} gender
 * @param {string} description
 * @param {string} age
 */
export function addCharacterInput(name = '', gender = '', description = '', age = '') {
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
    charactersListEl.appendChild(characterDiv);

    updateSummary();
    // 요약은 값 변경 시 갱신되도록 이벤트 연결
    [nameInput, genderSelect, ageInput, descTextarea].forEach(el => {
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
 * 캐릭터 설명 조합
 */
export function composeDescription(base, gender, age, traits, goals, boundaries, examples, tags, includeMeta = true) {
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

/**
 * 캐릭터 아이템에서 데이터 수집
 */
export function collectCharacterFromItem(item) {
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

// ===== 캐릭터 에디터 모달 관련 =====

export function openCharacterEditor(characterDiv) {
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

export function saveCharacterTemplateFromModal() {
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
        p.textContent = '현재 참여자가 없습니다. “참여자 추가”를 눌러 추가하세요.';
        charactersListEl.appendChild(p);
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
    openModal('characterEditorModal', true);

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

        const newParticipants = [...participants];
        if (index != null && index >= 0) newParticipants[index] = obj; else newParticipants.push(obj);
        setParticipants(newParticipants);

        renderParticipantsLeftPanel();
        renderParticipantsManagerList();
        closeCharacterEditor();
    };
}

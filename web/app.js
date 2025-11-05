// WebSocket 연결
let ws = null;

// DOM 요소
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const logArea = document.getElementById('logArea');

// 채팅 관련 요소
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendChatBtn = document.getElementById('sendChatBtn');

// 컨텍스트 패널 요소
const toggleContextBtn = document.getElementById('toggleContextBtn');
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
const adultMode = document.getElementById('adultMode');
const saveContextBtn = document.getElementById('saveContextBtn');

// 헤더 버튼
const clearHistoryBtn = document.getElementById('clearHistoryBtn');

// 서사 패널 요소
const narrativeContent = document.getElementById('narrativeContent');
const saveNarrativeBtn = document.getElementById('saveNarrativeBtn');

let currentAssistantMessage = null;
let characterColors = {}; // 캐릭터별 색상 매핑

// ===== WebSocket 연결 =====

function connect() {
    const wsUrl = `ws://${window.location.hostname}:8765`;
    log(`연결 시도: ${wsUrl}`);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        updateStatus('connected', '연결됨');
        log('WebSocket 연결 성공', 'success');

        // 연결 시 컨텍스트 조회
        ws.send(JSON.stringify({ action: 'get_context' }));

        // 연결 시 서사 조회
        ws.send(JSON.stringify({ action: 'get_narrative' }));
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
        setTimeout(connect, 5000);
    };
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

// 메시지 처리
function handleMessage(msg) {
    const { action, data } = msg;

    switch (action) {
        case 'connected':
            log('서버 연결 완료', 'success');
            break;

        case 'get_context':
            if (data.success) {
                loadContext(data.context);
            }
            break;

        case 'set_context':
            if (data.success) {
                log('컨텍스트 저장 완료', 'success');
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

        case 'chat_stream':
            handleChatStream(data);
            break;

        case 'chat_complete':
            handleChatComplete(data);
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

    if (ws && ws.readyState === WebSocket.OPEN) {
        // 사용자 메시지 표시
        addChatMessage('user', prompt);

        // 입력 필드 초기화
        chatInput.value = '';
        chatInput.disabled = true;
        sendChatBtn.disabled = true;

        // 타이핑 인디케이터 표시
        addTypingIndicator();

        // 서버로 전송
        ws.send(JSON.stringify({
            action: 'chat',
            prompt: prompt
        }));

        const shortPrompt = prompt.length > 50 ? prompt.slice(0, 50) + '...' : prompt;
        log('Claude에게 메시지 전송: ' + shortPrompt);
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
            // 멀티 캐릭터 파싱 시도
            const parsedMessages = parseMultiCharacterResponse(textContent);

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
        log('Claude 응답 완료', 'success');
        // 스트리밍 완료 시 메시지 고정
        chatMessages.querySelectorAll('.chat-message.assistant').forEach(msg => {
            msg.dataset.permanent = 'true';
        });
    }
}

function handleChatComplete(data) {
    removeTypingIndicator();
    currentAssistantMessage = null;

    // 입력 필드 활성화
    chatInput.disabled = false;
    sendChatBtn.disabled = false;
    chatInput.focus();

    if (data.success) {
        log('응답 완료', 'success');

        // 서사 업데이트
        ws.send(JSON.stringify({ action: 'get_narrative' }));
    } else {
        log('채팅 에러: ' + data.error, 'error');
        addChatMessage('system', '에러: ' + data.error);
    }
}

// ===== 멀티 캐릭터 응답 파싱 =====

function parseMultiCharacterResponse(text) {
    const messages = [];
    const lines = text.split('\n');

    let currentChar = null;
    let currentText = [];

    for (const line of lines) {
        const match = line.match(/^\[(.+?)\]:\s*(.*)$/);
        if (match) {
            // 이전 캐릭터 메시지 저장
            if (currentChar && currentText.length > 0) {
                messages.push({
                    character: currentChar,
                    text: currentText.join('\n').trim()
                });
            }
            // 새 캐릭터 시작
            currentChar = match[1];
            currentText = [match[2]];
        } else if (currentChar) {
            // 현재 캐릭터의 메시지 계속
            currentText.push(line);
        }
    }

    // 마지막 캐릭터 메시지 저장
    if (currentChar && currentText.length > 0) {
        messages.push({
            character: currentChar,
            text: currentText.join('\n').trim()
        });
    }

    return messages;
}

function getCharacterColor(characterName) {
    if (!characterColors[characterName]) {
        const colors = ['character-0', 'character-1', 'character-2', 'character-3', 'character-4'];
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
    contentDiv.textContent = text;

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

// 컨텍스트 패널 토글
toggleContextBtn.addEventListener('click', () => {
    if (contextContent.style.display === 'none') {
        contextContent.style.display = 'block';
        toggleContextBtn.textContent = '▼';
    } else {
        contextContent.style.display = 'none';
        toggleContextBtn.textContent = '▶';
    }
});

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

// 캐릭터 추가
addCharacterBtn.addEventListener('click', () => {
    addCharacterInput();
});

function addCharacterInput(name = '', description = '') {
    const characterDiv = document.createElement('div');
    characterDiv.className = 'character-item';

    const header = document.createElement('div');
    header.className = 'character-item-header';

    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.placeholder = '캐릭터 이름';
    nameInput.value = name;
    nameInput.style.flex = '1';

    const removeBtn = document.createElement('button');
    removeBtn.className = 'btn-remove';
    removeBtn.textContent = '삭제';
    removeBtn.onclick = () => characterDiv.remove();

    header.appendChild(nameInput);
    header.appendChild(removeBtn);

    const descTextarea = document.createElement('textarea');
    descTextarea.placeholder = '캐릭터 설명 (성격, 말투, 배경 등)';
    descTextarea.value = description;

    characterDiv.appendChild(header);
    characterDiv.appendChild(descTextarea);
    charactersList.appendChild(characterDiv);
}

// 컨텍스트 저장
saveContextBtn.addEventListener('click', () => {
    const characters = [];
    const characterItems = charactersList.querySelectorAll('.character-item');

    characterItems.forEach(item => {
        const name = item.querySelector('input').value.trim();
        const description = item.querySelector('textarea').value.trim();
        if (name && description) {
            characters.push({ name, description });
        }
    });

    ws.send(JSON.stringify({
        action: 'set_context',
        world: worldInput.value.trim(),
        situation: situationInput.value.trim(),
        user_character: userCharacterInput.value.trim(),
        narrator_enabled: narratorEnabled.checked,
        narrator_mode: narratorMode.value,
        narrator_description: narratorDescription.value.trim(),
        user_is_narrator: userIsNarrator.checked,
        adult_mode: adultMode.checked,
        characters: characters
    }));
});

// 컨텍스트 로드
function loadContext(context) {
    worldInput.value = context.world || '';
    situationInput.value = context.situation || '';
    userCharacterInput.value = context.user_character || '';
    narratorEnabled.checked = context.narrator_enabled || false;
    narratorMode.value = context.narrator_mode || 'moderate';
    narratorDescription.value = context.narrator_description || '';
    userIsNarrator.checked = context.user_is_narrator || false;
    adultMode.checked = context.adult_mode || false;

    // 진행자 설정 표시/숨김
    if (narratorEnabled.checked) {
        narratorSettings.style.display = 'block';
    }

    // 캐릭터 로드
    charactersList.innerHTML = '';
    if (context.characters && context.characters.length > 0) {
        context.characters.forEach(char => {
            addCharacterInput(char.name, char.description);
        });
    } else {
        // 예시 캐릭터 하나 추가
        addCharacterInput('예시', '친근하고 활발한 성격의 캐릭터');
    }
}

// ===== 히스토리 초기화 =====

clearHistoryBtn.addEventListener('click', () => {
    if (confirm('대화 히스토리를 초기화하시겠습니까?')) {
        ws.send(JSON.stringify({ action: 'clear_history' }));
    }
});

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

saveNarrativeBtn.addEventListener('click', () => {
    // 서사 내용 가져오기
    ws.send(JSON.stringify({ action: 'get_narrative' }));

    // 잠시 후 다운로드 (서버 응답 대기)
    setTimeout(() => {
        const narrativeText = narrativeContent.innerText;

        if (!narrativeText || narrativeText.includes('대화가 진행되면')) {
            alert('저장할 서사가 없습니다.');
            return;
        }

        // 마크다운 재구성 (innerText로부터)
        let markdown = '# 서사 기록\n\n';
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

        // 다운로드
        const blob = new Blob([markdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `narrative_${new Date().toISOString().slice(0, 10)}.md`;
        a.click();
        URL.revokeObjectURL(url);

        log('서사 저장 완료', 'success');
    }, 500);
});

// ===== 이벤트 리스너 =====

sendChatBtn.addEventListener('click', sendChatMessage);

chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
    }
});

// ===== 초기화 =====

window.addEventListener('load', () => {
    connect();
});

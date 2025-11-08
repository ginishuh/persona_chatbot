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
const aiProvider = document.getElementById('aiProvider');
const adultLevel = document.getElementById('adultLevel');
const narrativeSeparation = document.getElementById('narrativeSeparation');
const saveContextBtn = document.getElementById('saveContextBtn');

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

// 프리셋 관리 요소
const presetSelect = document.getElementById('presetSelect');
const savePresetBtn = document.getElementById('savePresetBtn');
const loadPresetBtn = document.getElementById('loadPresetBtn');
const deletePresetBtn = document.getElementById('deletePresetBtn');

// 헤더 버튼
const modeSwitchBtn = document.getElementById('modeSwitchBtn');
const gitSyncBtn = document.getElementById('gitSyncBtn');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const tokenText = document.getElementById('tokenText');

// 서사 패널 요소
const narrativeContent = document.getElementById('narrativeContent');
const saveNarrativeBtn = document.getElementById('saveNarrativeBtn');
const storySelect = document.getElementById('storySelect');
const loadStoryBtn = document.getElementById('loadStoryBtn');
const deleteStoryBtn = document.getElementById('deleteStoryBtn');

// 로그인 요소
const loginModal = document.getElementById('loginModal');
const loginPasswordInput = document.getElementById('loginPassword');
const loginButton = document.getElementById('loginButton');
const loginError = document.getElementById('loginError');

let currentAssistantMessage = null;
let characterColors = {}; // 캐릭터별 색상 매핑
let authRequired = false;
let isAuthenticated = false;

// ===== WebSocket 연결 =====

function connect() {
    const wsUrl = `ws://${window.location.hostname}:8765`;
    log(`연결 시도: ${wsUrl}`);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        updateStatus('connected', '연결됨');
        log('WebSocket 연결 성공', 'success');
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

function initializeAppData() {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    ws.send(JSON.stringify({ action: 'get_context' }));
    ws.send(JSON.stringify({ action: 'get_narrative' }));

    loadFileList('world', worldSelect);
    loadFileList('situation', situationSelect);
    loadFileList('my_character', myCharacterSelect);
    loadPresetList();
    loadStoryList();
    checkGitStatus();
    checkModeStatus();
}

function showLoginModal() {
    if (!loginModal) return;
    loginModal.classList.remove('hidden');
    loginPasswordInput.value = '';
    loginError.textContent = '';
    chatInput.disabled = true;
    sendChatBtn.disabled = true;
    setTimeout(() => loginPasswordInput.focus(), 100);
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
    const password = loginPasswordInput.value.trim();
    if (!password) {
        loginError.textContent = '비밀번호를 입력하세요.';
        return;
    }
    ws.send(JSON.stringify({
        action: 'login',
        password
    }));
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

// 메시지 처리
function handleMessage(msg) {
    const { action, data } = msg;

    switch (action) {
        case 'connected':
            log('서버 연결 완료', 'success');
            if (data && data.login_required) {
                authRequired = true;
                isAuthenticated = false;
                showLoginModal();
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
            showLoginModal();
            log('로그인이 필요합니다', 'warning');
            break;

        case 'login':
            if (data.success) {
                authRequired = false;
                isAuthenticated = true;
                hideLoginModal();
                log('로그인 성공', 'success');
                initializeAppData();
            } else {
                const errorMsg = data.error || '로그인에 실패했습니다.';
                loginError.textContent = errorMsg;
                log(`로그인 실패: ${errorMsg}`, 'error');
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

        case 'list_workspace_files':
            if (data.success) {
                handleFileList(data);
            } else {
                log(`파일 목록 로드 실패: ${data.error}`, 'error');
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

        case 'git_check_status':
            handleGitStatus(data);
            break;

        case 'git_init':
            if (data.success) {
                log(data.message, 'success');
                checkGitStatus(); // 상태 재확인
            } else {
                log(`Git 초기화 실패: ${data.error}`, 'error');
            }
            break;

        case 'git_sync':
            if (data.success) {
                log(data.message, 'success');
                if (data.warning) {
                    log(data.warning, 'error');
                }
                checkGitStatus(); // 상태 재확인
            } else {
                log(`동기화 실패: ${data.error}`, 'error');
            }
            break;

        case 'git_pull':
            if (data.success) {
                log(data.message, 'success');
                checkGitStatus(); // 상태 재확인
            } else {
                log(`Pull 실패: ${data.error}`, 'error');
            }
            break;

        case 'mode_check':
            handleModeStatus(data);
            break;

        case 'mode_switch_chatbot':
            if (data.success) {
                log(data.message, 'success');
                alert('⚠️ 챗봇 전용 모드로 전환되었습니다.\n\n브라우저를 새로고침(F5 또는 Ctrl+R)하세요!');
                checkModeStatus(); // 상태 재확인
            } else {
                log(`모드 전환 실패: ${data.error}`, 'error');
            }
            break;

        case 'mode_switch_coding':
            if (data.success) {
                log(data.message, 'success');
                alert('⚠️ 에이전트 지침이 복구되었습니다.\n\n브라우저를 새로고침(F5 또는 Ctrl+R)하세요!');
                checkModeStatus(); // 상태 재확인
            } else {
                log(`모드 전환 실패: ${data.error}`, 'error');
            }
            break;

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
        log('Claude 응답 완료', 'success');
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
        log('응답 완료', 'success');

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

        // 토큰 정보 업데이트
        console.log('Token info:', data.token_info); // 디버그
        if (data.token_info) {
            updateTokenDisplay(data.token_info);
        }

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
    nameInput.className = 'character-name-input';
    nameInput.placeholder = '이름';
    nameInput.value = name;
    nameInput.style.flex = '0 1 100px';
    nameInput.style.minWidth = '60px';

    // NPC 파일 관리 버튼들
    const fileControls = document.createElement('div');
    fileControls.style.display = 'flex';
    fileControls.style.gap = '0.25rem';
    fileControls.style.alignItems = 'center';
    fileControls.style.flex = '1';
    fileControls.style.justifyContent = 'flex-end';

    const npcSelect = document.createElement('select');
    npcSelect.className = 'npc-select select-input';
    npcSelect.style.fontSize = '0.7rem';
    npcSelect.style.padding = '0.2rem 0.3rem';
    npcSelect.style.minWidth = '70px';
    npcSelect.style.maxWidth = '100px';
    npcSelect.innerHTML = '<option value="">📂</option>';

    const saveNPCBtn = document.createElement('button');
    saveNPCBtn.className = 'btn btn-sm';
    saveNPCBtn.textContent = '💾';
    saveNPCBtn.title = 'NPC 저장';
    saveNPCBtn.style.padding = '0.2rem 0.3rem';
    saveNPCBtn.onclick = () => saveNPC(characterDiv);

    const removeBtn = document.createElement('button');
    removeBtn.className = 'btn-remove';
    removeBtn.textContent = '❌';
    removeBtn.title = '제거';
    removeBtn.style.padding = '0.2rem 0.3rem';
    removeBtn.onclick = () => characterDiv.remove();

    fileControls.appendChild(npcSelect);
    fileControls.appendChild(saveNPCBtn);
    fileControls.appendChild(removeBtn);

    header.appendChild(nameInput);
    header.appendChild(fileControls);

    // NPC 선택 시 로드
    npcSelect.onchange = () => {
        if (npcSelect.value) {
            window.pendingNPCItem = characterDiv;
            loadFile('npc', npcSelect.value);
        }
    };

    const descTextarea = document.createElement('textarea');
    descTextarea.className = 'character-description-input';
    descTextarea.placeholder = '캐릭터 설명 (성격, 말투, 배경 등)';
    descTextarea.value = description;

    characterDiv.appendChild(header);
    characterDiv.appendChild(descTextarea);
    charactersList.appendChild(characterDiv);

    // NPC 목록 로드
    loadNPCList(npcSelect);
}

// NPC 저장
function saveNPC(characterDiv) {
    const nameInput = characterDiv.querySelector('.character-name-input');
    const descInput = characterDiv.querySelector('.character-description-input');

    const name = nameInput.value.trim();
    const desc = descInput.value.trim();

    if (!name) {
        alert('NPC 이름을 입력하세요');
        return;
    }
    if (!desc) {
        alert('NPC 설명을 입력하세요');
        return;
    }

    const filename = prompt('저장할 파일명:', name);
    if (!filename) return;

    ws.send(JSON.stringify({
        action: 'save_workspace_file',
        file_type: 'npc',
        filename: filename,
        content: desc
    }));

    // 저장 후 목록 새로고침
    setTimeout(() => {
        const npcSelect = characterDiv.querySelector('.npc-select');
        if (npcSelect) {
            loadNPCList(npcSelect);
        }
    }, 500);
}

// NPC 목록 로드
function loadNPCList(selectElement) {
    ws.send(JSON.stringify({ action: 'list_workspace_files', file_type: 'npc' }));
    window.pendingNPCSelect = selectElement;
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
        ai_provider: aiProvider.value,
        adult_level: adultLevel.value,
        narrative_separation: narrativeSeparation.checked,
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
    aiProvider.value = context.ai_provider || 'claude';
    adultLevel.value = context.adult_level || 'explicit';
    narrativeSeparation.checked = context.narrative_separation || false;

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
    }
    // 빈 상태로 시작 (사용자가 직접 추가)
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
    const narrativeText = narrativeContent.innerText;

    if (!narrativeText || narrativeText.includes('대화가 진행되면')) {
        alert('저장할 서사가 없습니다.');
        return;
    }

    const filename = prompt('서사 이름을 입력하세요:', `서사_${new Date().toISOString().slice(0, 10)}`);
    if (!filename) return;

    const markdown = getNarrativeMarkdown();

    ws.send(JSON.stringify({
        action: 'save_story',
        filename: filename,
        content: markdown
    }));
});

// ===== 토큰 표시 =====

function updateTokenDisplay(tokenInfo) {
    if (!tokenInfo) return;

    const total = tokenInfo.total_tokens;
    const remaining = tokenInfo.tokens_remaining;
    const contextWindow = tokenInfo.context_window;

    // 1000 단위로 쉼표 추가
    const formatNumber = (num) => num.toLocaleString('ko-KR');

    // 남은 비율 계산
    const usagePercent = ((total / contextWindow) * 100).toFixed(1);

    tokenText.textContent = `토큰: ${formatNumber(total)} / ${formatNumber(contextWindow)} (${usagePercent}%)`;
    tokenText.title = `입력: ${formatNumber(tokenInfo.input_tokens)}, 캐시 읽기: ${formatNumber(tokenInfo.cache_read_tokens)}, 캐시 생성: ${formatNumber(tokenInfo.cache_creation_tokens)}, 출력: ${formatNumber(tokenInfo.output_tokens)}`;

    // 토큰 사용량에 따라 색상 변경
    const tokenInfoDiv = document.getElementById('tokenInfo');
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

// 탭 버튼들
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.dataset.tab;

        // 모든 탭 버튼 비활성화
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        // 모든 탭 컨텐츠 숨기기
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        // 클릭한 탭 활성화
        button.classList.add('active');
        document.getElementById(`tab-${tabName}`).classList.add('active');
    });
});

// ===== 파일 관리 =====

// 파일 목록 응답 처리
function handleFileList(data) {
    if (window.pendingFileListSelect) {
        updateFileList(window.pendingFileListSelect, data.files);
        window.pendingFileListSelect = null;
        window.pendingFileListType = null;
    } else if (window.pendingNPCSelect) {
        // NPC 목록 업데이트
        updateNPCList(window.pendingNPCSelect, data.files);
        window.pendingNPCSelect = null;
    }
}

// NPC 목록 업데이트
function updateNPCList(selectElement, files) {
    const currentValue = selectElement.value;
    selectElement.innerHTML = '<option value="">불러오기...</option>';

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
    ws.send(JSON.stringify({ action: 'list_workspace_files', file_type: fileType }));
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
        userCharacterInput.value = content;
        myCharacterSelect.value = filename.replace('.md', '');
    } else if (window.pendingLoadType === 'npc') {
        // NPC 로드는 addCharacterInput 시 처리
        if (window.pendingNPCItem) {
            const nameInput = window.pendingNPCItem.querySelector('.character-name-input');
            const descInput = window.pendingNPCItem.querySelector('.character-description-input');
            const npcSelect = window.pendingNPCItem.querySelector('.npc-select');

            descInput.value = content;
            if (npcSelect) {
                npcSelect.value = filename.replace('.md', '');
            }

            window.pendingNPCItem = null;
        }
    }
}

// 파일 저장
async function saveFile(fileType, selectElement, contentGetter) {
    const filename = prompt(`파일 이름을 입력하세요 (${fileType}):`);
    if (!filename) return;

    const content = contentGetter();
    ws.send(JSON.stringify({
        action: 'save_workspace_file',
        file_type: fileType,
        filename: filename,
        content: content
    }));

    // 저장 후 목록 새로고침
    setTimeout(() => {
        loadFileList(fileType, selectElement);
    }, 500);
}

// 파일 로드
function loadFile(fileType, filename) {
    window.pendingLoadType = fileType;
    ws.send(JSON.stringify({
        action: 'load_workspace_file',
        file_type: fileType,
        filename: filename
    }));
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

    ws.send(JSON.stringify({
        action: 'delete_workspace_file',
        file_type: fileType,
        filename: filename
    }));

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
    const content = userCharacterInput.value.trim();
    if (!content) {
        alert('캐릭터 내용을 입력하세요');
        return;
    }
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

// ===== 프리셋 관리 =====

// 프리셋 목록 로드
function loadPresetList() {
    ws.send(JSON.stringify({ action: 'list_presets' }));
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

    // 현재 모든 캐릭터 수집
    const characters = [];
    document.querySelectorAll('.character-item').forEach(item => {
        const name = item.querySelector('.character-name-input').value;
        const description = item.querySelector('.character-description-input').value;
        if (name) {
            characters.push({ name, description });
        }
    });

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
        narrative_separation: narrativeSeparation.checked
    };

    ws.send(JSON.stringify({
        action: 'save_preset',
        filename: filename,
        preset: preset
    }));
}

// 프리셋 적용
function applyPreset(preset) {
    // 기본 설정
    worldInput.value = preset.world || '';
    situationInput.value = preset.situation || '';
    userCharacterInput.value = preset.user_character || '';

    // 캐릭터 초기화 및 로드
    charactersList.innerHTML = '';
    if (preset.characters && preset.characters.length > 0) {
        preset.characters.forEach(char => {
            addCharacterInput(char.name, char.description);
        });
    }

    // 진행자 설정
    narratorEnabled.checked = preset.narrator_enabled || false;
    narratorMode.value = preset.narrator_mode || 'moderate';
    narratorDescription.value = preset.narrator_description || '';
    userIsNarrator.checked = preset.user_is_narrator || false;

    // 모드 설정
    adultLevel.value = preset.adult_level || 'explicit';
    narrativeSeparation.checked = preset.narrative_separation || false;

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

    ws.send(JSON.stringify({
        action: 'delete_preset',
        filename: filename
    }));
}

// 프리셋 이벤트 리스너
savePresetBtn.addEventListener('click', savePreset);

loadPresetBtn.addEventListener('click', () => {
    const filename = presetSelect.value;
    if (!filename) {
        alert('불러올 프리셋을 선택하세요');
        return;
    }

    ws.send(JSON.stringify({
        action: 'load_preset',
        filename: filename
    }));
});

deletePresetBtn.addEventListener('click', deletePreset);

// ===== Git 관리 =====

// Git 상태 확인
function checkGitStatus() {
    ws.send(JSON.stringify({ action: 'git_check_status' }));
}

// Git 상태 처리
function handleGitStatus(data) {
    if (!data.success) {
        gitSyncBtn.textContent = '🔄 동기화';
        gitSyncBtn.title = `Git 오류: ${data.error}`;
        return;
    }

    if (!data.is_repo) {
        // Git 레포가 아님
        gitSyncBtn.textContent = '📦 Git 초기화';
        gitSyncBtn.title = '클릭하여 Git 레포지토리 초기화';
    } else if (data.has_changes) {
        // 변경사항 있음
        gitSyncBtn.textContent = '🔄 동기화 *';
        gitSyncBtn.title = '변경사항이 있습니다. 클릭하여 동기화';
    } else {
        // 변경사항 없음
        gitSyncBtn.textContent = '✓ 동기화';
        gitSyncBtn.title = '변경사항 없음';
    }
}

// Git 동기화 버튼 클릭
gitSyncBtn.addEventListener('click', () => {
    // 현재 상태 확인 후 처리
    ws.send(JSON.stringify({ action: 'git_check_status' }));

    // 잠시 후 실제 처리 (상태 확인 결과를 기다림)
    setTimeout(() => {
        const btnText = gitSyncBtn.textContent;

        if (btnText.includes('초기화')) {
            // Git 초기화
            if (confirm('persona_data를 Git 레포지토리로 초기화하시겠습니까?')) {
                ws.send(JSON.stringify({ action: 'git_init' }));
            }
        } else {
            // Git 동기화
            ws.send(JSON.stringify({ action: 'git_sync' }));
        }
    }, 100);
});

// ===== 모드 관리 (챗봇 ↔ 코딩) =====

// 모드 상태 확인
function checkModeStatus() {
    ws.send(JSON.stringify({ action: 'mode_check' }));
}

// 모드 상태 처리
function handleModeStatus(data) {
    if (!data.success) {
        modeSwitchBtn.textContent = '💬 모드';
        modeSwitchBtn.title = '모드 확인 실패';
        return;
    }

    const mode = data.mode;

    if (mode === 'chatbot') {
        // 챗봇 전용 모드
        modeSwitchBtn.textContent = '💬 챗봇';
        modeSwitchBtn.title = '현재: 챗봇 전용 모드 (클릭: 에이전트 지침 복구)';
    } else if (mode === 'coding') {
        // 코딩 모드
        modeSwitchBtn.textContent = '⚙️ 코딩';
        modeSwitchBtn.title = '현재: 코딩 모드 (클릭: 챗봇 전용 전환)';
    } else if (mode === 'none') {
        // 파일 없음
        modeSwitchBtn.textContent = '💬 모드';
        modeSwitchBtn.title = 'CLAUDE.md 파일 없음';
    } else {
        // 혼재 상태
        modeSwitchBtn.textContent = '⚠️ 혼재';
        modeSwitchBtn.title = '.md와 .md.bak가 혼재되어 있습니다';
    }
}

// 모드 전환 버튼 클릭
modeSwitchBtn.addEventListener('click', () => {
    // 현재 모드 확인
    ws.send(JSON.stringify({ action: 'mode_check' }));

    // 잠시 후 실제 처리
    setTimeout(() => {
        const btnText = modeSwitchBtn.textContent;

        if (btnText.includes('챗봇')) {
            // 챗봇 → 코딩
            if (confirm('에이전트 지침을 복구하시겠습니까?\n(CLAUDE.md 파일 복원)')) {
                ws.send(JSON.stringify({ action: 'mode_switch_coding' }));
            }
        } else if (btnText.includes('코딩')) {
            // 코딩 → 챗봇
            if (confirm('챗봇 전용 모드로 전환하시겠습니까?\n(CLAUDE.md 파일 비활성화)')) {
                ws.send(JSON.stringify({ action: 'mode_switch_chatbot' }));
            }
        } else {
            alert('모드를 확인할 수 없습니다');
        }
    }, 100);
});

// ===== 서사 관리 =====

// 서사 목록 로드
function loadStoryList() {
    ws.send(JSON.stringify({ action: 'list_stories' }));
}

// 서사 목록 업데이트
function updateStoryList(files) {
    const currentValue = storySelect.value;
    storySelect.innerHTML = '<option value="">저장된 서사...</option>';

    files.forEach(file => {
        const option = document.createElement('option');
        option.value = file.name;
        option.textContent = file.name;
        storySelect.appendChild(option);
    });

    if (currentValue && files.some(f => f.name === currentValue)) {
        storySelect.value = currentValue;
    }
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

    ws.send(JSON.stringify({
        action: 'load_story',
        filename: filename
    }));
});

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

    ws.send(JSON.stringify({
        action: 'delete_story',
        filename: filename
    }));
});

// ===== 초기화 =====

window.addEventListener('load', () => {
    connect();

    // 주기적 상태 확인 (10초마다)
    setInterval(checkGitStatus, 10000);
    setInterval(checkModeStatus, 10000);
});

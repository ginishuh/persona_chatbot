import { sendMessage } from '../websocket/connection.js';
import { isAuthenticated, authRequired, getCharacterColor } from '../core/state.js';
import { log } from '../utils/logger.js';
import { isTouchDevice } from '../utils/utils.js';
import { parseMultiCharacterResponse } from './characters.js';

// DOM Elements
let chatMessages = null;
let chatInput = null;
let sendChatBtn = null;
let aiProvider = null;
let modelSelect = null;
let tokenUsageDisplay = null;
let tokenPrompt = null;
let tokenCompletion = null;
let tokenTotal = null;

// State
let currentAssistantMessage = null;
let currentProvider = 'claude';
let isComposing = false;
let streamingText = '';

export function refreshChatRefs() {
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    sendChatBtn = document.getElementById('sendChatBtn');
    aiProvider = document.getElementById('aiProvider');
    modelSelect = document.getElementById('modelSelect');
    tokenUsageDisplay = document.getElementById('tokenUsageDisplay');
    tokenPrompt = document.getElementById('tokenPrompt');
    tokenCompletion = document.getElementById('tokenCompletion');
    tokenTotal = document.getElementById('tokenTotal');
}

export function addChatMessage(role, content) {
    if (!chatMessages) refreshChatRefs();

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

export function addCharacterMessage(characterName, text) {
    if (!chatMessages) refreshChatRefs();

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

export function addTypingIndicator() {
    if (!chatMessages) refreshChatRefs();

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

export function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

export function sendChatMessage() {
    if (!chatInput) refreshChatRefs();

    const prompt = chatInput.value.trim();

    if (!prompt) return;
    if (authRequired && !isAuthenticated) {
        log('로그인 후 이용 가능합니다.', 'error');
        return;
    }

    // WebSocket check is done inside sendMessage or we can check here if we had access to ws object.
    // Assuming sendMessage handles connection check or we rely on UI state.
    // But original code checked ws.readyState.
    // We can import isConnected from connection.js if available, or just try sending.
    // For now, let's assume sendMessage handles it or we'll add a check if needed.

    // 사용자 메시지 표시
    addChatMessage('user', prompt);

    // 입력 필드 초기화
    chatInput.value = '';
    chatInput.disabled = true;
    if (sendChatBtn) sendChatBtn.disabled = true;

    // 타이핑 인디케이터 표시
    addTypingIndicator();

    // 선택된 프로바이더 확인 및 저장
    const provider = (aiProvider && aiProvider.value) ? aiProvider.value : 'claude';
    currentProvider = provider;

    // 서버로 전송(프로바이더 명시)
    const success = sendMessage({
        action: 'chat',
        prompt: prompt,
        provider: provider,
        model: (modelSelect && modelSelect.value) ? modelSelect.value : ''
    });

    if (success) {
        const providerLabel = provider === 'gemini' ? 'Gemini' : (provider === 'droid' ? 'Droid' : 'Claude');
        const shortPrompt = prompt.length > 50 ? prompt.slice(0, 50) + '...' : prompt;
        log(`${providerLabel}에게 메시지 전송: ${shortPrompt}`);
    } else {
        log('WebSocket 연결이 끊어졌습니다', 'error');
        removeTypingIndicator();
        chatInput.disabled = false;
        if (sendChatBtn) sendChatBtn.disabled = false;
    }
}

export function handleChatStream(data) {
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
            streamingText += deltaText;
        }
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
                if (chatMessages) {
                    const existingMsgs = chatMessages.querySelectorAll('.chat-message.assistant:not(#typingIndicator)');
                    existingMsgs.forEach(msg => {
                        if (!msg.dataset.permanent) {
                            msg.remove();
                        }
                    });
                }

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
        if (chatMessages) {
            chatMessages.querySelectorAll('.chat-message.assistant').forEach(msg => {
                msg.dataset.permanent = 'true';
            });
        }
    }
}

export function handleChatComplete(response) {
    removeTypingIndicator();
    currentAssistantMessage = null;

    if (!chatInput) refreshChatRefs();

    // 입력 필드 활성화
    if (chatInput) {
        chatInput.disabled = false;
        chatInput.focus();
    }
    if (sendChatBtn) sendChatBtn.disabled = false;

    // response.data가 실제 데이터
    const data = response.data || response;

    if (data.success) {
        const used = data.provider_used || currentProvider || 'claude';
        const label = used === 'gemini' ? 'Gemini' : (used === 'droid' ? 'Droid' : 'Claude');
        log(`${label} 응답 완료`, 'success');

        // Droid/Gemini: 누적된 스트리밍 텍스트 처리
        if (streamingText) {
            console.log('=== Droid/Gemini 응답 원본 ===');
            console.log(streamingText);

            const parsedMessages = parseMultiCharacterResponse(streamingText);
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
                addChatMessage('assistant', streamingText);
            }

            // 스트리밍 텍스트 초기화
            streamingText = '';
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

export function updateTokenDisplay(tokenUsage) {
    if (!tokenUsageDisplay) refreshChatRefs();

    if (tokenUsageDisplay) {
        tokenUsageDisplay.classList.remove('hidden');
        if (tokenPrompt) tokenPrompt.textContent = tokenUsage.input_tokens || 0;
        if (tokenCompletion) tokenCompletion.textContent = tokenUsage.output_tokens || 0;
        if (tokenTotal) tokenTotal.textContent = tokenUsage.total_tokens || 0;
    }
}

export function bindChatEvents() {
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
            const __isTouch = isTouchDevice();
            try { console.debug('isTouchDevice check:', __isTouch); } catch (_) {}

            // 터치(모바일) 디바이스에서는 Enter로 전송하지 않도록
            // 캐치/캡처 단계에서 기본 동작을 막아 다른 핸들러에 의해서
            // 전송되는 것을 방지합니다.
            chatInput.addEventListener(
                'keydown',
                (e) => {
                    try { console.debug('keydown on chatInput', e.key, 'isComposing', isComposing, 'isTouchDevice', __isTouch); } catch (_) {}
                    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
                        if (__isTouch) {
                            try { console.debug('Preventing Enter on touch device'); } catch (_) {}
                            e.preventDefault();
                            e.stopImmediatePropagation();
                            return;
                        }
                        // 터치가 아닌 경우(데스크탑)만 Enter로 전송
                        e.preventDefault();
                        sendChatMessage();
                    }
                },
                { capture: true }
            );

            chatInput.dataset.bound = '1';
        }
    } catch (_) {}
}

export function updateChatInputState(enabled) {
    if (!chatInput) refreshChatRefs();
    if (chatInput) chatInput.disabled = !enabled;
    if (sendChatBtn) sendChatBtn.disabled = !enabled;
}

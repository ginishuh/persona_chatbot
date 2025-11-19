/**
 * 접근성(A11y) 보조 유틸리티
 * @module ui/a11y
 */

const focusTrapHandlers = new WeakMap();

function getFocusableElements(container) {
    return container.querySelectorAll(
        'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])'
    );
}

export function focusMainAfterRoute() {
    try {
        const chatInput = document.getElementById('chatInput');
        if (chatInput && !chatInput.disabled) {
            chatInput.focus();
            return;
        }
        const heading = document.querySelector('main h1, header h1');
        if (heading) {
            heading.tabIndex = -1;
            heading.focus();
        }
    } catch (_) {}
}

export function applyARIA() {
    const labels = [
        ['sendChatBtn', '메시지 전송'],
        ['clearHistoryBtn', '대화 히스토리 초기화'],
        ['resetSessionsBtn', '세션 초기화'],
        ['roomAddBtn', '채팅방 추가'],
        ['roomSaveBtn', '채팅방 설정 저장'],
        ['saveContextBtn', '컨텍스트 저장'],
        ['narrativeMenuBtn', '히스토리 패널 열기'],
        ['moreMenuBtn', '더보기 메뉴 열기'],
        ['participantsBtn', '참여자 관리'],
        ['settingsBtn', '설정 열기'],
        ['hamburgerBtn', '좌측 패널 토글'],
        ['loginButton', '로그인 제출'],
        ['autoLoginButton', '자동 로그인']
    ];

    labels.forEach(([id, label]) => {
        const el = document.getElementById(id);
        try { el?.setAttribute('aria-label', label); } catch (_) {}
    });

    try {
        document.getElementById('narrativeContent')?.setAttribute('aria-live', 'polite');
    } catch (_) {}
}

export function injectSkipLink() {
    try {
        const link = document.createElement('a');
        link.href = '#';
        link.className = 'skip-link';
        link.textContent = '본문으로 건너뛰기';
        link.style.position = 'absolute';
        link.style.left = '-9999px';
        link.style.top = '0';
        link.style.zIndex = '10000';
        link.addEventListener('focus', () => {
            link.style.left = '8px';
            link.style.top = '8px';
        });
        link.addEventListener('blur', () => {
            link.style.left = '-9999px';
        });
        link.addEventListener('click', (event) => {
            event.preventDefault();
            focusMainAfterRoute();
        });
        document.body.prepend(link);
    } catch (_) {}
}

export function enableFocusTrap(modalEl) {
    try {
        if (!modalEl || focusTrapHandlers.has(modalEl)) return;
        const handler = (event) => {
            if (event.key !== 'Tab') return;
            const candidates = Array.from(getFocusableElements(modalEl)).filter(
                (node) => !node.disabled && node.tabIndex !== -1
            );
            if (!candidates.length) return;
            const first = candidates[0];
            const last = candidates[candidates.length - 1];
            if (event.shiftKey) {
                if (document.activeElement === first || !modalEl.contains(document.activeElement)) {
                    event.preventDefault();
                    last.focus();
                }
            } else if (document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        };
        modalEl.addEventListener('keydown', handler);
        focusTrapHandlers.set(modalEl, handler);
        setTimeout(() => {
            const focusables = Array.from(getFocusableElements(modalEl)).filter(
                (node) => !node.disabled && node.tabIndex !== -1
            );
            (focusables[0] || modalEl).focus();
        }, 0);
    } catch (_) {}
}

export function disableFocusTrap(modalEl) {
    try {
        const handler = focusTrapHandlers.get(modalEl);
        if (handler) {
            modalEl.removeEventListener('keydown', handler);
            focusTrapHandlers.delete(modalEl);
        }
    } catch (_) {}
}

export function announce(message) {
    try {
        const live = document.getElementById('ariaLive');
        if (!live) return;
        live.textContent = '';
        setTimeout(() => { live.textContent = message; }, 10);
    } catch (_) {}
}

export function initA11y() {
    applyARIA();
    injectSkipLink();
}

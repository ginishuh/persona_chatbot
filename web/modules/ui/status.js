/**
 * 상태 표시 및 로그 유틸리티
 * @module ui/status
 */

const LOG_LIMIT = 100;

function formatTimestamp(date) {
    return date.toLocaleTimeString('ko-KR', { hour12: false });
}

function syncConnectionIndicator() {
    try {
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
    } catch (_) {}
}

export function updateStatus(status, text) {
    try {
        const indicator = document.getElementById('statusIndicator');
        const statusLabel = document.getElementById('statusText');
        if (indicator) {
            indicator.className = `status-indicator ${status}`;
        }
        if (statusLabel) {
            statusLabel.textContent = text;
        }
        syncConnectionIndicator();
    } catch (_) {}
}

export function log(message, level = 'info') {
    try {
        const logArea = document.getElementById('logArea');
        if (!logArea) return;

        const entry = document.createElement('p');
        entry.className = `log-entry log-${level}`;
        entry.textContent = `[${formatTimestamp(new Date())}] ${message}`;

        logArea.prepend(entry);
        while (logArea.childElementCount > LOG_LIMIT) {
            logArea.removeChild(logArea.lastElementChild);
        }

        if (level === 'error') {
            console.error(message);
        } else if (level === 'warning' || level === 'warn') {
            console.warn(message);
        } else {
            console.log(message);
        }
    } catch (error) {
        console.error('Log render failed:', error);
    }
}

export function updateModelOptions(provider, options = {}) {
    const selectEl = options.modelSelect || document.getElementById('modelSelect');
    if (!selectEl) return;

    const previous = selectEl.value;
    selectEl.innerHTML = '';

    const appendOption = (label, value) => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = label;
        selectEl.appendChild(option);
    };

    if (provider === 'gemini') {
        appendOption('gemini-2.5-flash', 'gemini-2.5-flash');
        appendOption('gemini-2.5-pro', 'gemini-2.5-pro');
    } else if (provider === 'claude') {
        appendOption('기본(권장)', '');
        appendOption('Sonnet (alias: sonnet)', 'sonnet');
        appendOption('Haiku (alias: haiku)', 'haiku');
    } else if (provider === 'droid') {
        appendOption('서버 기본(커스텀)', '');
    } else {
        appendOption('기본', '');
    }

    const exists = Array.from(selectEl.options).some((opt) => opt.value === previous);
    selectEl.value = exists ? previous : '';

    if (provider === 'droid') {
        selectEl.disabled = true;
        selectEl.title = 'Droid는 서버 기본(DROID_MODEL)만 사용합니다';
    } else {
        selectEl.disabled = false;
        selectEl.title = '';
    }
}

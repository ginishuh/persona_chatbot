/**
 * 모바일/햄버거 메뉴 및 더보기 메뉴 제어
 * @module ui/mobile
 */

import { enableFocusTrap } from './a11y.js';
import { syncConnectionIndicator } from './status.js';

let elements = {};
let callbacks = {};
let currentPanel = null;
let touchStartX = 0;
let touchStartY = 0;
let touchStartTime = 0;

const SWIPE_THRESHOLD = 50;
const SWIPE_VELOCITY_THRESHOLD = 0.3;
const SWIPE_MAX_VERTICAL_RATIO = 0.5;

export function initMobileUI(options = {}) {
    elements = {
        hamburgerBtn: options.hamburgerBtn || document.getElementById('hamburgerBtn'),
        narrativeMenuBtn: options.narrativeMenuBtn || document.getElementById('narrativeMenuBtn'),
        moreMenuBtn: options.moreMenuBtn || document.getElementById('moreMenuBtn'),
        moreMenuDropdown: options.moreMenuDropdown || document.getElementById('moreMenuDropdown'),
        mobileOverlay: options.mobileOverlay || document.getElementById('mobileOverlay'),
        leftPanel: options.leftPanel || document.querySelector('.left-panel'),
        rightPanel: options.rightPanel || document.querySelector('.right-panel'),
        moreSettingsBtn: options.moreSettingsBtn || document.getElementById('moreSettingsBtn'),
        moreParticipantsBtn: options.moreParticipantsBtn || document.getElementById('moreParticipantsBtn'),
        moreClearHistoryBtn: options.moreClearHistoryBtn || document.getElementById('moreClearHistoryBtn'),
        moreResetSessionsBtn: options.moreResetSessionsBtn || document.getElementById('moreResetSessionsBtn'),
        moreBackupBtn: options.moreBackupBtn || document.getElementById('moreBackupBtn')
    };

    callbacks = {
        onOpenParticipants: options.onOpenParticipants || (() => {}),
        onClearHistory: options.onClearHistory || (() => {}),
        onResetSessions: options.onResetSessions || (() => {}),
        onLogout: options.onLogout || (() => {}),
        onOpenBackup: options.onOpenBackup || (() => {})
    };

    elements.hamburgerBtn?.addEventListener('click', () => {
        if (currentPanel === 'left') {
            closeMobilePanel();
        } else {
            openMobilePanel('left');
        }
    });

    elements.narrativeMenuBtn?.addEventListener('click', () => {
        if (currentPanel === 'right') {
            closeMobilePanel();
        } else {
            openMobilePanel('right');
        }
    });

    elements.moreMenuBtn?.addEventListener('click', (event) => {
        event.stopPropagation();
        toggleMoreMenu();
    });

    elements.moreSettingsBtn?.addEventListener('click', () => {
        closeMoreMenu();
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.classList.remove('hidden');
            enableFocusTrap(modal);
        }
    });

    elements.moreParticipantsBtn?.addEventListener('click', () => {
        closeMoreMenu();
        callbacks.onOpenParticipants();
    });

    elements.moreClearHistoryBtn?.addEventListener('click', () => {
        closeMoreMenu();
        callbacks.onClearHistory();
    });

    elements.moreResetSessionsBtn?.addEventListener('click', () => {
        closeMoreMenu();
        callbacks.onResetSessions();
    });

    elements.moreBackupBtn?.addEventListener('click', () => {
        closeMoreMenu();
        callbacks.onOpenBackup();
    });

    document.addEventListener('click', (event) => {
        const { moreMenuDropdown, moreMenuBtn } = elements;
        if (!moreMenuDropdown) return;
        if (!moreMenuDropdown.contains(event.target) && event.target !== moreMenuBtn) {
            closeMoreMenu();
        }
    });

    elements.leftPanel?.addEventListener('touchstart', handleTouchStart, { passive: true });
    elements.leftPanel?.addEventListener('touchend', handleTouchEnd, { passive: true });
    elements.rightPanel?.addEventListener('touchstart', handleTouchStart, { passive: true });
    elements.rightPanel?.addEventListener('touchend', handleTouchEnd, { passive: true });
    elements.mobileOverlay?.addEventListener('click', () => closeMobilePanel());
}

export function openMobilePanel(panel) {
    closeMobilePanel();

    if (panel === 'left' && elements.leftPanel) {
        elements.leftPanel.classList.add('mobile-visible');
        elements.hamburgerBtn?.classList.add('active');
        currentPanel = 'left';
    } else if (panel === 'right' && elements.rightPanel) {
        elements.rightPanel.classList.add('mobile-visible');
        elements.narrativeMenuBtn?.classList.add('active');
        currentPanel = 'right';
    }

    elements.mobileOverlay?.classList.add('active');
}

export function closeMobilePanel() {
    elements.leftPanel?.classList.remove('mobile-visible');
    elements.rightPanel?.classList.remove('mobile-visible');
    elements.mobileOverlay?.classList.remove('active');
    elements.hamburgerBtn?.classList.remove('active');
    elements.narrativeMenuBtn?.classList.remove('active');
    currentPanel = null;
}

function toggleMoreMenu() {
    const dropdown = elements.moreMenuDropdown;
    if (!dropdown) return;
    if (dropdown.classList.contains('visible')) {
        closeMoreMenu();
    } else {
        openMoreMenu();
    }
}

function openMoreMenu() {
    const dropdown = elements.moreMenuDropdown;
    if (!dropdown) return;
    closeMoreMenu();
    dropdown.classList.remove('hidden');
    dropdown.classList.add('visible');
    elements.moreMenuBtn?.classList.add('active');
    syncMoreMenuStatus();
}

export function closeMoreMenu() {
    const dropdown = elements.moreMenuDropdown;
    if (!dropdown) return;
    dropdown.classList.remove('visible');
    dropdown.classList.add('hidden');
    elements.moreMenuBtn?.classList.remove('active');
}

function syncMoreMenuStatus() {
    try {
        syncConnectionIndicator();

        const tokenInfo = document.getElementById('tokenInfo');
        const moreTokenInfo = document.getElementById('moreTokenInfo');
        if (tokenInfo && moreTokenInfo) {
            moreTokenInfo.textContent = tokenInfo.textContent;
        }

        const sessionBadge = document.getElementById('sessionStatusBadge');
        const moreSessionBadgeText = document.getElementById('moreSessionBadgeText');
        if (sessionBadge && moreSessionBadgeText) {
            moreSessionBadgeText.textContent = sessionBadge.textContent.replace('세션: ', '');
            moreSessionBadgeText.className = sessionBadge.className;
        }
    } catch (_) {}
}

function handleTouchStart(event) {
    const touch = event.touches[0];
    touchStartX = touch.clientX;
    touchStartY = touch.clientY;
    touchStartTime = Date.now();
}

function handleTouchEnd(event) {
    if (!currentPanel) return;
    const touch = event.changedTouches[0];
    const deltaX = touch.clientX - touchStartX;
    const deltaY = touch.clientY - touchStartY;
    const deltaTime = Date.now() - touchStartTime;

    if (Math.abs(deltaY) > Math.abs(deltaX) * SWIPE_MAX_VERTICAL_RATIO) {
        return;
    }

    const distance = Math.abs(deltaX);
    const velocity = distance / Math.max(deltaTime, 1);
    if (distance < SWIPE_THRESHOLD && velocity < SWIPE_VELOCITY_THRESHOLD) {
        return;
    }

    if (currentPanel === 'left' && deltaX < 0) {
        closeMobilePanel();
    }
    if (currentPanel === 'right' && deltaX > 0) {
        closeMobilePanel();
    }
}

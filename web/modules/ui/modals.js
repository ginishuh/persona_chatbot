/**
 * 모달 관리 공통 유틸리티
 * @module ui/modals
 */

import { enableFocusTrap as a11yEnableFocusTrap, disableFocusTrap as a11yDisableFocusTrap } from './a11y.js';

// 과거 import 호환용 re-export (characters.js 등에서 사용)
export { a11yEnableFocusTrap as enableFocusTrap, a11yDisableFocusTrap as disableFocusTrap };

/**
 * 모달 열기
 * @param {string} modalId - 모달 요소 ID
 * @param {Function} enableFocusTrap - 포커스 트랩 활성화 함수 (선택)
 */
export function openModal(modalId, enableFocusTrap = null) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.warn(`Modal not found: ${modalId}`);
        return;
    }

    modal.classList.remove('hidden');

    // 포커스 트랩 활성화 (제공된 경우)
    if (enableFocusTrap && typeof enableFocusTrap === 'function') {
        enableFocusTrap(modal);
    } else {
        a11yEnableFocusTrap(modal);
    }
}

/**
 * 모달 닫기
 * @param {string} modalId - 모달 요소 ID
 * @param {Function} disableFocusTrap - 포커스 트랩 비활성화 함수 (선택)
 */
export function closeModal(modalId, disableFocusTrap = null) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.warn(`Modal not found: ${modalId}`);
        return;
    }

    modal.classList.add('hidden');

    // 포커스 트랩 비활성화 (제공된 경우)
    if (disableFocusTrap && typeof disableFocusTrap === 'function') {
        disableFocusTrap(modal);
    } else {
        a11yDisableFocusTrap(modal);
    }
}

/**
 * 모달 토글
 * @param {string} modalId - 모달 요소 ID
 * @param {Function} enableFocusTrap - 포커스 트랩 활성화 함수 (선택)
 * @param {Function} disableFocusTrap - 포커스 트랩 비활성화 함수 (선택)
 */
export function toggleModal(modalId, enableFocusTrap = null, disableFocusTrap = null) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.warn(`Modal not found: ${modalId}`);
        return;
    }

    const isHidden = modal.classList.contains('hidden');

    if (isHidden) {
        openModal(modalId, enableFocusTrap);
    } else {
        closeModal(modalId, disableFocusTrap);
    }
}

/**
 * 모달이 열려있는지 확인
 * @param {string} modalId - 모달 요소 ID
 * @returns {boolean}
 */
export function isModalOpen(modalId) {
    const modal = document.getElementById(modalId);
    return modal ? !modal.classList.contains('hidden') : false;
}

/**
 * 모든 모달 닫기
 * @param {string[]} modalIds - 모달 ID 배열
 * @param {Function} disableFocusTrap - 포커스 트랩 비활성화 함수 (선택)
 */
export function closeAllModals(modalIds = [], disableFocusTrap = null) {
    modalIds.forEach(id => closeModal(id, disableFocusTrap));
}

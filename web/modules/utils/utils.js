/**
 * 공통 유틸리티 함수
 * @module utils/utils
 */

/**
 * 터치(모바일) 디바이스 감지
 * @returns {boolean}
 */
export function isTouchDevice() {
    try {
        if (typeof window === 'undefined') return false;
        if ('ontouchstart' in window) return true;
        if (navigator.maxTouchPoints && navigator.maxTouchPoints > 0) return true;
        if (window.matchMedia && window.matchMedia('(pointer: coarse)').matches) return true;
        if (/Mobi|Android|iPhone|iPad|iPod|Windows Phone|webOS/i.test(navigator.userAgent)) return true;
    } catch (_) {}
    return false;
}

/**
 * HTML 이스케이프
 * @param {string} text
 * @returns {string}
 */
export function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * 문자열을 URL 친화적인 slug로 변환
 * @param {string} str
 * @returns {string}
 */
export function slugify(str) {
    return str
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '');
}

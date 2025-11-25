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
    // undefined/null 안전 처리
    const safe = text ?? '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return safe.replace(/[&<>"']/g, m => map[m]);
}

/**
 * 문자열을 URL 친화적인 slug로 변환
 * @param {string} str
 * @returns {string}
 */
export function slugify(str) {
    // undefined/null/빈 문자열 안전 처리 및 기본값 제공
    const safe = (str || '').trim();
    if (!safe) {
        return 'character'; // 기본값
    }

    return safe
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '') || 'character'; // 변환 후에도 빈 문자열이면 기본값
}

/**
 * 사용자 캐릭터 데이터 문자열 생성
 * @param {string} name - 캐릭터 이름
 * @param {string} description - 캐릭터 설명
 * @returns {string} - "이름: {name}\n{description}" 형식 문자열
 */
export function buildUserCharacterData(name, description) {
    const n = (name || '').trim();
    const d = (description || '').trim();
    if (n) {
        return d ? `이름: ${n}\n${d}` : `이름: ${n}`;
    }
    return d;
}

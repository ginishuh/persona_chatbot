/**
 * 전용 화면 컨테이너 관리
 * @module ui/screens
 */

/**
 * 전용 화면 표시
 * main-content를 숨기고 screenRoot에 내용을 표시
 *
 * @param {string} html - 표시할 HTML 내용
 */
export function showScreen(html) {
    const root = document.getElementById('screenRoot');
    const main = document.querySelector('.main-content');

    if (root && main) {
        root.innerHTML = html || '';
        root.classList.add('active');
        root.classList.remove('hidden');
        main.classList.add('hidden');
    }
}

/**
 * 전용 화면 숨김
 * screenRoot를 숨기고 main-content를 표시
 */
export function hideScreen() {
    const root = document.getElementById('screenRoot');
    const main = document.querySelector('.main-content');

    if (root && main) {
        root.classList.remove('active');
        root.classList.add('hidden');
        root.innerHTML = '';
        main.classList.remove('hidden');
    }
}

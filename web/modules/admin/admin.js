/**
 * 관리자 패널 모듈
 * @module admin/admin
 */

import { authToken } from '../core/state.js';
import { log } from '../ui/status.js';
import { enableFocusTrap, disableFocusTrap } from '../ui/a11y.js';
import { escapeHtml } from '../utils/utils.js';

let adminModal = null;
let pendingUsersList = null;
let emptyState = null;

export function initAdminPanel(options = {}) {
    adminModal = options.adminModal || document.getElementById('adminModal');
    pendingUsersList = options.pendingUsersList || document.getElementById('pendingUsersList');
    emptyState = options.noPendingUsers || document.getElementById('noPendingUsers');

    const openButtons = [options.adminBtn || document.getElementById('adminBtn'), options.moreAdminBtn || document.getElementById('moreAdminBtn')].filter(Boolean);
    openButtons.forEach((button) => {
        button.addEventListener('click', openAdminModal);
    });

    (options.adminCloseBtn || document.getElementById('adminCloseBtn'))?.addEventListener('click', closeAdminModal);
}

export async function openAdminModal() {
    adminModal = adminModal || document.getElementById('adminModal');
    if (!adminModal) return;
    if (!authToken) {
        log('관리자 권한이 필요합니다.', 'error');
        return;
    }
    adminModal.classList.remove('hidden');
    enableFocusTrap(adminModal);
    await fetchPendingUsers();
}

export function closeAdminModal() {
    if (!adminModal) return;
    adminModal.classList.add('hidden');
    disableFocusTrap(adminModal);
}

async function fetchPendingUsers() {
    if (!authToken) {
        log('관리자 권한이 필요합니다.', 'error');
        renderPendingUsers([]);
        closeAdminModal();
        return;
    }

    try {
        const response = await fetch('/api/admin/pending-users', {
            method: 'GET',
            headers: {
                Authorization: `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        if (response.status === 401 || response.status === 403) {
            log('세션이 만료되었습니다. 다시 로그인 해주세요.', 'error');
            renderPendingUsers([]);
            closeAdminModal();
            return;
        }
        const data = await response.json();
        if (response.ok && data.success) {
            renderPendingUsers(data.users || []);
        } else {
            log(data.error || '사용자 목록 조회 실패', 'error');
            renderPendingUsers([]);
        }
    } catch (error) {
        console.error('Fetch pending users error:', error);
        log('서버 오류가 발생했습니다.', 'error');
        renderPendingUsers([]);
    }
}

function renderPendingUsers(users) {
    if (!pendingUsersList || !emptyState) return;

    if (!users || users.length === 0) {
        pendingUsersList.style.display = 'none';
        pendingUsersList.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';
    pendingUsersList.style.display = 'block';
    pendingUsersList.innerHTML = users.map((user) => `
        <div class="pending-user-card">
            <div class="pending-user-info">
                <div class="pending-user-name">${escapeHtml(user.username)}</div>
                <div class="pending-user-email">📧 ${escapeHtml(user.email)}</div>
                <div class="pending-user-date">가입일: ${escapeHtml(formatSignupDate(user.created_at))}</div>
            </div>
            <button class="approve-user-btn btn btn-sm" data-user-id="${user.user_id}">✓ 승인</button>
        </div>
    `).join('');

    pendingUsersList.querySelectorAll('.approve-user-btn').forEach((button) => {
        button.addEventListener('click', async (event) => {
            const userId = Number(event.currentTarget.dataset.userId);
            await approveUser(userId);
        });
    });
}

async function approveUser(userId) {
    if (!authToken) {
        log('관리자 권한이 필요합니다.', 'error');
        closeAdminModal();
        return;
    }

    try {
        const response = await fetch('/api/admin/approve-user', {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: userId })
        });
        if (response.status === 401 || response.status === 403) {
            log('세션이 만료되었습니다. 다시 로그인 해주세요.', 'error');
            closeAdminModal();
            return;
        }
        const data = await response.json();
        if (response.ok && data.success) {
            log('사용자 승인이 완료되었습니다.', 'success');
            await fetchPendingUsers();
        } else {
            log(data.error || '승인 실패', 'error');
        }
    } catch (error) {
        console.error('Approve user error:', error);
        log('서버 오류가 발생했습니다.', 'error');
    }
}

function formatSignupDate(value) {
    if (!value) return '알 수 없음';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return '알 수 없음';
    }
    return date.toLocaleString('ko-KR');
}

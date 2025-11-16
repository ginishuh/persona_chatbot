"""세션/채팅방 유틸리티 (user_id 기반)

웹소켓 연결과 무관하게 사용자별 세션/방 상태를 관리합니다.
"""

from __future__ import annotations

import asyncio
import logging

from .app_context import AppContext

logger = logging.getLogger(__name__)


def get_user_id_from_token(ctx: AppContext, data: dict | None) -> int | None:
    """JWT 토큰에서 user_id 추출

    Args:
        ctx: 애플리케이션 컨텍스트
        data: WebSocket 메시지 데이터 (token 필드 포함)

    Returns:
        user_id 또는 None (인증 실패 시)
    """
    if not isinstance(data, dict):
        return None

    token = data.get("token")
    if not token:
        return None

    try:
        # JWT 검증 (ctx.auth 모듈 사용)
        from server.core.auth import verify_token as auth_verify_token

        payload, error = auth_verify_token(ctx, token, expected_type="access")
        if error or not payload:
            return None

        user_id = payload.get("user_id")
        if not (isinstance(user_id, int) and ctx and getattr(ctx, "db_handler", None)):
            # user_id가 없거나 DB 핸들러가 없으면 인증 실패
            return None

        # DB에 실제 사용자 존재 여부 확인 (동기 컨텍스트에서 안전하게 호출)
        try:
            loop = getattr(ctx, "loop", None)
            if not loop:
                # 이벤트 루프가 없으면 추가 확인 불가 -> 거부
                return None
            fut = asyncio.run_coroutine_threadsafe(ctx.db_handler.get_user_by_id(user_id), loop)
            user_row = fut.result(timeout=3)
            if not user_row:
                logger.warning("Token user_id %s not found in DB", user_id)
                return None
        except Exception as e:
            logger.warning("Error verifying user_id in DB: %s", e)
            return None

        return user_id
    except Exception as e:
        logger.warning(f"Failed to extract user_id from token: {e}")
        return None


def get_or_create_session(ctx: AppContext, websocket, user_id: int):
    """사용자 세션 가져오기 또는 생성 (user_id 기반)

    Args:
        ctx: 애플리케이션 컨텍스트
        websocket: WebSocket 연결
        user_id: 사용자 ID

    Returns:
        (user_id, session_dict)
    """
    # WebSocket에 user_id 매핑 저장
    ctx.websocket_to_session[websocket] = user_id

    # user_id 기반 세션 생성/조회
    if user_id not in ctx.sessions:
        ctx.sessions[user_id] = {
            "settings": {"adult_consent": bool(ctx.login_required)},
            "rooms": {},
        }

    return user_id, ctx.sessions[user_id]


def get_room(ctx: AppContext, session: dict, room_id: str | None):
    """세션 내 채팅방 객체 반환(없으면 생성)."""
    rid = room_id or "default"
    rooms = session.setdefault("rooms", {})
    room = rooms.get(rid)
    if not room:
        from server.handlers.history_handler import HistoryHandler

        room = {"history": HistoryHandler(max_turns=30), "provider_sessions": {}}
        rooms[rid] = room
    return rid, room


def clear_client_sessions(ctx: AppContext, websocket, room_id: str | None = None):
    """프로바이더 세션 초기화 (히스토리 유지, user_id 기반)"""
    user_id = ctx.websocket_to_session.get(websocket)
    if user_id and user_id in ctx.sessions:
        claude_session_ids = []
        if room_id:
            rid = room_id or "default"
            room = ctx.sessions[user_id].get("rooms", {}).get(rid)
            if room:
                provider_sessions = room.get("provider_sessions", {})
                if "claude" in provider_sessions:
                    claude_session_ids.append(provider_sessions["claude"])
                room["provider_sessions"] = {}
        else:
            for room in ctx.sessions[user_id].get("rooms", {}).values():
                provider_sessions = room.get("provider_sessions", {})
                if "claude" in provider_sessions:
                    claude_session_ids.append(provider_sessions["claude"])
                room["provider_sessions"] = {}

        for session_id in claude_session_ids:
            try:
                ctx.claude_handler.clear_session_tokens(session_id)
            except Exception:
                pass


def remove_client_sessions(ctx: AppContext, websocket):
    """WebSocket 연결 종료 시 매핑 제거"""
    ctx.websocket_to_session.pop(websocket, None)

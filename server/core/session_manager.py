"""세션/채팅방 유틸리티

웹소켓 연결과 무관하게 세션/방 상태를 관리합니다.
"""

from __future__ import annotations

import uuid

from .app_context import AppContext


def get_or_create_session(ctx: AppContext, websocket, data: dict | None):
    """세션키 해석 및 생성.

    username이 있으면 user:{username} 형태의 session_key 사용 (다중 기기 동기화)

    반환: (session_key, session_dict)
    """
    key = None
    username = None

    if isinstance(data, dict):
        key = data.get("session_key") or None
        username = data.get("username") or None

    # username 기반 session_key 우선 (로그인된 사용자)
    if username and ctx.login_required:
        user_key = f"user:{username}"
        if user_key in ctx.sessions:
            ctx.websocket_to_session[websocket] = user_key
            return user_key, ctx.sessions[user_key]
        # username 기반 새 세션 생성
        ctx.sessions[user_key] = {
            "settings": {"retention_enabled": False, "adult_consent": True},
            "rooms": {},
            "username": username,  # 저장해두기
        }
        ctx.websocket_to_session[websocket] = user_key
        return user_key, ctx.sessions[user_key]

    # 기존 session_key 사용 (data에 명시적으로 전달됨)
    if key and key in ctx.sessions:
        ctx.websocket_to_session[websocket] = key
    else:
        # websocket에 연결된 기존 세션 찾기
        key = ctx.websocket_to_session.get(websocket)
        if not key or key not in ctx.sessions:
            # 랜덤 UUID로 새 세션 생성 (비로그인 사용자)
            key = uuid.uuid4().hex
            ctx.sessions[key] = {
                "settings": {"retention_enabled": False, "adult_consent": bool(ctx.login_required)},
                "rooms": {},
            }
            ctx.websocket_to_session[websocket] = key
    return key, ctx.sessions[key]


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


def initialize_client_state(ctx: AppContext, websocket):
    get_or_create_session(ctx, websocket, None)


def clear_client_sessions(ctx: AppContext, websocket, room_id: str | None = None):
    """프로바이더 세션 초기화(히스토리 유지)."""
    key = ctx.websocket_to_session.get(websocket)
    if key and key in ctx.sessions:
        claude_session_ids = []
        if room_id:
            rid = room_id or "default"
            room = ctx.sessions[key].get("rooms", {}).get(rid)
            if room:
                provider_sessions = room.get("provider_sessions", {})
                if "claude" in provider_sessions:
                    claude_session_ids.append(provider_sessions["claude"])
                room["provider_sessions"] = {}
        else:
            for room in ctx.sessions[key].get("rooms", {}).values():
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
    ctx.websocket_to_session.pop(websocket, None)


def is_session_retention_enabled(ctx: AppContext, websocket, session: dict | None = None):
    sess = session or get_or_create_session(ctx, websocket, None)[1]
    settings = sess.get("settings", {})
    return settings.get("retention_enabled", False)

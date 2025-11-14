from __future__ import annotations

import json
from typing import Any

from server.core import session_manager as sm
from server.core.app_context import AppContext


async def get_token_usage(ctx: AppContext, websocket, data: dict[str, Any]):
    """토큰 사용량 요약 조회(채팅방 단위)"""
    try:
        session_key, _ = sm.get_or_create_session(ctx, websocket, data)
        room_id = data.get("room_id")
        summary = ctx.token_usage_handler.get_formatted_summary(
            session_key=session_key, room_id=room_id
        )
        await websocket.send(
            json.dumps(
                {"action": "get_token_usage", "data": {"success": True, "token_usage": summary}}
            )
        )
    except Exception as exc:
        await websocket.send(
            json.dumps({"action": "get_token_usage", "data": {"success": False, "error": str(exc)}})
        )

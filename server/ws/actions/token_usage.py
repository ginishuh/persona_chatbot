from __future__ import annotations

import json
from typing import Any

from server.core import session_manager as sm
from server.core.app_context import AppContext


async def get_token_usage(ctx: AppContext, websocket, data: dict[str, Any]):
    """토큰 사용량 요약 조회(채팅방 단위)"""
    try:
        # JWT 토큰에서 user_id 추출
        user_id = sm.get_user_id_from_token(ctx, data)
        if not user_id:
            await websocket.send(
                json.dumps(
                    {"action": "get_token_usage", "data": {"success": False, "error": "인증 필요"}}
                )
            )
            return

        room_id = data.get("room_id")
        summary = ctx.token_usage_handler.get_formatted_summary(
            session_key=str(user_id), room_id=room_id  # 레거시 호환용
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

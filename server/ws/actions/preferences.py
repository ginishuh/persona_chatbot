"""사용자 설정(preferences) 액션"""

from __future__ import annotations

import json
import logging

from server.core import session_manager as sm
from server.core.app_context import AppContext

logger = logging.getLogger(__name__)


async def get_preferences(ctx: AppContext, websocket, data: dict):
    """사용자 설정 조회"""
    # JWT 토큰에서 user_id 추출
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps(
                {"action": "get_preferences", "data": {"success": False, "error": "인증 필요"}}
            )
        )
        return

    preferences = {}
    if ctx.db_handler:
        try:
            preferences = await ctx.db_handler.get_user_preferences(user_id)
        except Exception as e:
            logger.error(f"Failed to get preferences: {e}")

    await websocket.send(
        json.dumps(
            {"action": "get_preferences", "data": {"success": True, "preferences": preferences}}
        )
    )


async def update_preferences(ctx: AppContext, websocket, data: dict):
    """사용자 설정 업데이트"""
    # JWT 토큰에서 user_id 추출
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps(
                {"action": "update_preferences", "data": {"success": False, "error": "인증 필요"}}
            )
        )
        return

    preferences = data.get("preferences", {})
    if not isinstance(preferences, dict):
        await websocket.send(
            json.dumps(
                {
                    "action": "update_preferences",
                    "data": {"success": False, "error": "잘못된 설정 형식"},
                }
            )
        )
        return

    success = False
    if ctx.db_handler:
        try:
            success = await ctx.db_handler.update_user_preferences(user_id, preferences)
        except Exception as e:
            logger.error(f"Failed to update preferences: {e}")
            await websocket.send(
                json.dumps(
                    {
                        "action": "update_preferences",
                        "data": {"success": False, "error": str(e)},
                    }
                )
            )
            return

    await websocket.send(json.dumps({"action": "update_preferences", "data": {"success": success}}))

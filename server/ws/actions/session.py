from __future__ import annotations

import json

from server.core import session_manager as sm
from server.core.app_context import AppContext


async def get_session_settings(ctx: AppContext, websocket, data: dict):
    # JWT 토큰에서 user_id 추출
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps(
                {"action": "get_session_settings", "data": {"success": False, "error": "인증 필요"}}
            )
        )
        return

    _, sess = sm.get_or_create_session(ctx, websocket, user_id)
    settings = sess.get(
        "settings", {"retention_enabled": True}
    )  # user_id 기반에서는 항상 영구 저장
    await websocket.send(
        json.dumps({"action": "get_session_settings", "data": {"success": True, **settings}})
    )


async def set_session_retention(ctx: AppContext, websocket, data: dict):
    # JWT 토큰에서 user_id 추출
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps(
                {
                    "action": "set_session_retention",
                    "data": {"success": False, "error": "인증 필요"},
                }
            )
        )
        return

    # user_id 기반에서는 retention이 항상 활성화되어 있으므로 무시
    await websocket.send(
        json.dumps(
            {
                "action": "set_session_retention",
                "data": {
                    "success": True,
                    "retention_enabled": True,
                },  # user_id 기반에서는 항상 true
            }
        )
    )

from __future__ import annotations

import json

from server.core import session_manager as sm
from server.core.app_context import AppContext


async def get_session_settings(ctx: AppContext, websocket, data: dict):
    _, sess = sm.get_or_create_session(ctx, websocket, data)
    settings = sess.get("settings", {"retention_enabled": False})
    await websocket.send(
        json.dumps({"action": "get_session_settings", "data": {"success": True, **settings}})
    )


async def set_session_retention(ctx: AppContext, websocket, data: dict):
    enabled = bool(data.get("enabled"))
    _, sess = sm.get_or_create_session(ctx, websocket, data)
    sess.setdefault("settings", {})["retention_enabled"] = enabled
    if not enabled:
        sm.clear_client_sessions(ctx, websocket)
    await websocket.send(
        json.dumps(
            {
                "action": "set_session_retention",
                "data": {"success": True, "retention_enabled": enabled},
            }
        )
    )

from __future__ import annotations

import json

from server.core.app_context import AppContext


async def load_workspace_config(ctx: AppContext, websocket, data: dict):
    result = await ctx.workspace_handler.load_config()
    await websocket.send(json.dumps({"action": "load_workspace_config", "data": result}))


async def save_workspace_config(ctx: AppContext, websocket, data: dict):
    config = data.get("config", {})
    result = await ctx.workspace_handler.save_config(config)
    await websocket.send(json.dumps({"action": "save_workspace_config", "data": result}))

from __future__ import annotations

import json

from server.core.app_context import AppContext


async def git_status(ctx: AppContext, websocket, data: dict):
    result = await ctx.git_handler.status()
    await websocket.send(json.dumps({"action": "git_status", "data": result}))


async def git_push(ctx: AppContext, websocket, data: dict):
    message = data.get("message", "Update from web app")
    result = await ctx.git_handler.commit_and_push(message)
    await websocket.send(json.dumps({"action": "git_push", "data": result}))

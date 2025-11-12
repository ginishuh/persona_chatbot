from __future__ import annotations

import json

from server.core.app_context import AppContext


async def mode_check(ctx: AppContext, websocket, data: dict):
    result = await ctx.mode_handler.check_mode()
    await websocket.send(json.dumps({"action": "mode_check", "data": result}))


async def mode_switch_chatbot(ctx: AppContext, websocket, data: dict):
    result = await ctx.mode_handler.switch_to_chatbot()
    await websocket.send(json.dumps({"action": "mode_switch_chatbot", "data": result}))


async def mode_switch_coding(ctx: AppContext, websocket, data: dict):
    result = await ctx.mode_handler.switch_to_coding()
    await websocket.send(json.dumps({"action": "mode_switch_coding", "data": result}))

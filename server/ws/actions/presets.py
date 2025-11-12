from __future__ import annotations

import json

from server.core.app_context import AppContext


async def list_presets(ctx: AppContext, websocket, data: dict):
    result = await ctx.workspace_handler.list_presets()
    await websocket.send(json.dumps({"action": "list_presets", "data": result}))


async def save_preset(ctx: AppContext, websocket, data: dict):
    filename = data.get("filename")
    preset_data = data.get("preset")
    result = await ctx.workspace_handler.save_preset(filename, preset_data)
    await websocket.send(json.dumps({"action": "save_preset", "data": result}))


async def load_preset(ctx: AppContext, websocket, data: dict):
    filename = data.get("filename")
    result = await ctx.workspace_handler.load_preset(filename)
    await websocket.send(json.dumps({"action": "load_preset", "data": result}))


async def delete_preset(ctx: AppContext, websocket, data: dict):
    filename = data.get("filename")
    result = await ctx.workspace_handler.delete_preset(filename)
    await websocket.send(json.dumps({"action": "delete_preset", "data": result}))

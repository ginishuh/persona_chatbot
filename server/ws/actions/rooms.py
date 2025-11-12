from __future__ import annotations

import json

from server.core.app_context import AppContext


async def room_list(ctx: AppContext, websocket, data: dict):
    result = await ctx.workspace_handler.list_rooms()
    await websocket.send(json.dumps({"action": "room_list", "data": result}))


async def room_save(ctx: AppContext, websocket, data: dict):
    room_id = data.get("room_id") or "default"
    conf = data.get("config")
    if not isinstance(conf, dict) or not conf:
        conf = {"room_id": room_id, "context": ctx.context_handler.get_context()}
    result = await ctx.workspace_handler.save_room(room_id, conf)
    await websocket.send(json.dumps({"action": "room_save", "data": result}))


async def room_load(ctx: AppContext, websocket, data: dict):
    room_id = data.get("room_id") or "default"
    result = await ctx.workspace_handler.load_room(room_id)
    await websocket.send(json.dumps({"action": "room_load", "data": result}))


async def room_delete(ctx: AppContext, websocket, data: dict):
    room_id = data.get("room_id") or "default"
    result = await ctx.workspace_handler.delete_room(room_id)
    await websocket.send(json.dumps({"action": "room_delete", "data": result}))

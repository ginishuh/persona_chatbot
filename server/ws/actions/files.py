from __future__ import annotations

import json

from server.core.app_context import AppContext


async def list_workspace_files(ctx: AppContext, websocket, data: dict):
    file_type = data.get("file_type")
    result = await ctx.workspace_handler.list_files(file_type)
    await websocket.send(json.dumps({"action": "list_workspace_files", "data": result}))


async def load_workspace_file(ctx: AppContext, websocket, data: dict):
    file_type = data.get("file_type")
    filename = data.get("filename")
    result = await ctx.workspace_handler.read_file(file_type, filename)
    await websocket.send(json.dumps({"action": "load_workspace_file", "data": result}))


async def save_workspace_file(ctx: AppContext, websocket, data: dict):
    file_type = data.get("file_type")
    filename = data.get("filename")
    content = data.get("content")
    result = await ctx.workspace_handler.save_file(file_type, filename, content)
    await websocket.send(json.dumps({"action": "save_workspace_file", "data": result}))


async def delete_workspace_file(ctx: AppContext, websocket, data: dict):
    file_type = data.get("file_type")
    filename = data.get("filename")
    result = await ctx.workspace_handler.delete_file(file_type, filename)
    await websocket.send(json.dumps({"action": "delete_workspace_file", "data": result}))

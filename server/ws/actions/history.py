from __future__ import annotations

import json

from server.core import session_manager as sm
from server.core.app_context import AppContext


async def get_narrative(ctx: AppContext, websocket, data: dict):
    _, sess = sm.get_or_create_session(ctx, websocket, data)
    room_id = data.get("room_id")
    _, room = sm.get_room(ctx, sess, room_id)
    narrative_md = room["history"].get_narrative_markdown()
    await websocket.send(
        json.dumps({"action": "get_narrative", "data": {"success": True, "markdown": narrative_md}})
    )


async def get_history_settings(ctx: AppContext, websocket, data: dict):
    _, sess = sm.get_or_create_session(ctx, websocket, data)
    room_id = data.get("room_id")
    _, room = sm.get_room(ctx, sess, room_id)
    await websocket.send(
        json.dumps(
            {
                "action": "get_history_settings",
                "data": {"success": True, "max_turns": room["history"].max_turns},
            }
        )
    )


async def set_history_limit(ctx: AppContext, websocket, data: dict):
    try:
        _, sess = sm.get_or_create_session(ctx, websocket, data)
        room_id = data.get("room_id")
        _, room = sm.get_room(ctx, sess, room_id)
        max_turns = data.get("max_turns")
        if max_turns is None:
            room["history"].set_max_turns(None)
        else:
            room["history"].set_max_turns(int(max_turns))
        await websocket.send(
            json.dumps(
                {
                    "action": "set_history_limit",
                    "data": {"success": True, "max_turns": room["history"].max_turns},
                }
            )
        )
    except Exception as exc:
        await websocket.send(
            json.dumps(
                {"action": "set_history_limit", "data": {"success": False, "error": str(exc)}}
            )
        )


async def clear_history(ctx: AppContext, websocket, data: dict):
    session_key, sess = sm.get_or_create_session(ctx, websocket, data)
    room_id = data.get("room_id")
    _, room = sm.get_room(ctx, sess, room_id)
    room["history"].clear()
    sm.clear_client_sessions(ctx, websocket, room_id=room_id)
    ctx.token_usage_handler.clear_usage(session_key, room_id)
    await websocket.send(
        json.dumps(
            {
                "action": "clear_history",
                "data": {"success": True, "message": "대화 히스토리가 초기화되었습니다"},
            }
        )
    )


async def reset_sessions(ctx: AppContext, websocket, data: dict):
    room_id = data.get("room_id")
    sm.clear_client_sessions(ctx, websocket, room_id=room_id)
    await websocket.send(
        json.dumps(
            {
                "action": "reset_sessions",
                "data": {"success": True, "message": "AI 세션이 초기화되었습니다."},
            }
        )
    )


async def get_history_snapshot(ctx: AppContext, websocket, data: dict):
    try:
        _, sess = sm.get_or_create_session(ctx, websocket, data)
        room_id = data.get("room_id")
        _, room = sm.get_room(ctx, sess, room_id)
        snap = room["history"].get_history()
        await websocket.send(
            json.dumps(
                {"action": "get_history_snapshot", "data": {"success": True, "history": snap}}
            )
        )
    except Exception as exc:
        await websocket.send(
            json.dumps(
                {"action": "get_history_snapshot", "data": {"success": False, "error": str(exc)}}
            )
        )

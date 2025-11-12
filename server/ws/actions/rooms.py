from __future__ import annotations

import json
from datetime import datetime

from server.core import session_manager as sm
from server.core.app_context import AppContext


async def room_list(ctx: AppContext, websocket, data: dict):
    # 파일 기반 목록
    file_result = await ctx.workspace_handler.list_rooms()
    rooms = {r["room_id"]: r for r in file_result.get("rooms", [])}

    # DB 기반 목록 병합(가능 시)
    try:
        if ctx.db_handler:
            # 세션 키 없이 전체 룸을 나열하기 어렵다. 현재 연결 세션 기준으로만 병합.
            # UI는 로컬에 rooms를 저장하므로 이 수준으로 충분.
            session_key, _ = sm.get_or_create_session(ctx, websocket, data)
            for r in await ctx.db_handler.list_rooms(session_key):
                rid = r.get("room_id")
                title = r.get("title") or rid
                updated = r.get("updated_at") or r.get("created_at")
                try:
                    modified = int(datetime.fromisoformat(str(updated)).timestamp())
                except Exception:
                    modified = 0
                rooms[rid] = {"room_id": rid, "title": title, "modified": modified}
    except Exception:
        pass

    merged = sorted(rooms.values(), key=lambda x: x.get("modified", 0), reverse=True)
    await websocket.send(
        json.dumps({"action": "room_list", "data": {"success": True, "rooms": merged}})
    )


async def room_save(ctx: AppContext, websocket, data: dict):
    room_id = data.get("room_id") or "default"
    conf = data.get("config")
    if not isinstance(conf, dict) or not conf:
        conf = {"room_id": room_id, "context": ctx.context_handler.get_context()}

    # 파일 저장(과도기 유지)
    file_result = await ctx.workspace_handler.save_room(room_id, conf)

    # DB upsert(가능 시)
    try:
        if ctx.db_handler:
            session_key, _ = sm.get_or_create_session(ctx, websocket, data)
            title = conf.get("title") or room_id
            context_json = json.dumps(conf.get("context") or {}, ensure_ascii=False)
            await ctx.db_handler.upsert_room(room_id, session_key, title, context_json)
    except Exception:
        pass

    await websocket.send(json.dumps({"action": "room_save", "data": file_result}))


async def room_load(ctx: AppContext, websocket, data: dict):
    room_id = data.get("room_id") or "default"
    # 파일 우선 로드(과도기)
    result = await ctx.workspace_handler.load_room(room_id)
    await websocket.send(json.dumps({"action": "room_load", "data": result}))


async def room_delete(ctx: AppContext, websocket, data: dict):
    room_id = data.get("room_id") or "default"
    # 파일 설정 삭제(폴더는 보존)
    result = await ctx.workspace_handler.delete_room(room_id)
    await websocket.send(json.dumps({"action": "room_delete", "data": result}))

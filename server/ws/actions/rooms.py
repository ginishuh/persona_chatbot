from __future__ import annotations

import json
from datetime import datetime

from server.core import session_manager as sm
from server.core.app_context import AppContext


async def room_list(ctx: AppContext, websocket, data: dict):
    import logging

    logger = logging.getLogger(__name__)

    # JWT 토큰에서 user_id 추출
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps({"action": "room_list", "data": {"success": False, "error": "인증 필요"}})
        )
        return

    logger.info(f"[DEBUG] room_list - user_id: {user_id}")
    rows = await ctx.db_handler.list_rooms(user_id) if ctx.db_handler else []
    logger.info(f"[DEBUG] room_list - DB에서 조회된 방: {len(rows)}개")

    def to_item(r):
        rid = r.get("room_id")
        title = r.get("title") or rid
        updated = r.get("updated_at") or r.get("created_at")
        try:
            modified = int(datetime.fromisoformat(str(updated)).timestamp())
        except Exception:
            modified = 0
        return {"room_id": rid, "title": title, "modified": modified}

    items = [to_item(r) for r in rows]
    await websocket.send(
        json.dumps({"action": "room_list", "data": {"success": True, "rooms": items}})
    )


async def room_save(ctx: AppContext, websocket, data: dict):
    import logging

    logger = logging.getLogger(__name__)
    logger.info("[DEBUG] room_save 시작")

    if not ctx.db_handler:
        await websocket.send(
            json.dumps(
                {
                    "action": "room_save",
                    "data": {"success": False, "error": "DB를 사용할 수 없습니다"},
                }
            )
        )
        return

    # JWT 토큰에서 user_id 추출
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps({"action": "room_save", "data": {"success": False, "error": "인증 필요"}})
        )
        return

    room_id = data.get("room_id") or "default"
    conf = data.get("config")
    if not isinstance(conf, dict) or not conf:
        conf = {"room_id": room_id, "context": ctx.context_handler.get_context()}

    logger.info(f"[DEBUG] room_id={room_id}, user_id={user_id}, conf 타입={type(conf)}")

    title = conf.get("title") or room_id
    context_json = json.dumps(conf.get("context") or {}, ensure_ascii=False)
    logger.info("[DEBUG] upsert_room 호출 전")
    await ctx.db_handler.upsert_room(room_id, user_id, title, context_json)
    logger.info("[DEBUG] upsert_room 완료")

    await websocket.send(
        json.dumps({"action": "room_save", "data": {"success": True, "room_id": room_id}})
    )
    logger.info("[DEBUG] room_save 응답 전송 완료")


async def room_load(ctx: AppContext, websocket, data: dict):
    """채팅방 로드 (DB에서, user_id 기반)

    - 채팅방 정보를 DB에서 로드
    - context가 있으면 ContextHandler에 자동 적용
    """
    if not ctx.db_handler:
        await websocket.send(
            json.dumps({"action": "room_load", "data": {"success": False, "error": "DB 없음"}})
        )
        return

    # JWT 토큰에서 user_id 추출
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps({"action": "room_load", "data": {"success": False, "error": "인증 필요"}})
        )
        return

    room_id = data.get("room_id") or "default"

    # user_id로 방 조회
    db_row = await ctx.db_handler.get_room(room_id, user_id)
    if not db_row:
        await websocket.send(
            json.dumps(
                {"action": "room_load", "data": {"success": False, "error": "room not found"}}
            )
        )
        return
    try:
        ctx_obj = json.loads(db_row.get("context") or "{}")
    except Exception:
        ctx_obj = {}

    # ContextHandler에 자동 적용 (채팅방별 독립 설정)
    if ctx_obj and ctx.context_handler:
        ctx.context_handler.load_from_dict(ctx_obj)

    await websocket.send(
        json.dumps(
            {
                "action": "room_load",
                "data": {
                    "success": True,
                    "room": {
                        "room_id": room_id,
                        "title": db_row.get("title") or room_id,
                        "context": ctx_obj,
                    },
                },
            }
        )
    )


async def room_delete(ctx: AppContext, websocket, data: dict):
    """채팅방 삭제 (user_id 기반)"""
    if not ctx.db_handler:
        await websocket.send(
            json.dumps(
                {
                    "action": "room_delete",
                    "data": {"success": False, "error": "DB를 사용할 수 없습니다"},
                }
            )
        )
        return

    # JWT 토큰에서 user_id 추출
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps({"action": "room_delete", "data": {"success": False, "error": "인증 필요"}})
        )
        return

    room_id = data.get("room_id") or "default"

    # user_id로 방 삭제
    await ctx.db_handler.delete_room(room_id, user_id)
    await websocket.send(
        json.dumps({"action": "room_delete", "data": {"success": True, "room_id": room_id}})
    )

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime

from server.core import session_manager as sm
from server.core.app_context import AppContext

logger = logging.getLogger(__name__)


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

    logger.debug(f"room_list - user_id: {user_id}")
    rows = await ctx.db_handler.list_rooms(user_id) if ctx.db_handler else []
    logger.debug(f"room_list - DB에서 조회된 방: {len(rows)}개")

    def to_item(r):
        rid = r.get("room_id")
        title = r.get("title") or rid
        updated = r.get("updated_at") or r.get("created_at")
        try:
            modified = int(datetime.fromisoformat(str(updated)).timestamp())
        except (ValueError, TypeError):
            modified = 0
        return {"room_id": rid, "title": title, "modified": modified}

    items = [to_item(r) for r in rows]
    await websocket.send(
        json.dumps({"action": "room_list", "data": {"success": True, "rooms": items}})
    )


async def room_save(ctx: AppContext, websocket, data: dict):
    import logging

    logger = logging.getLogger(__name__)
    logger.debug("room_save 시작")

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

    # Support both shapes: top-level `room_id`/`config` or nested under `data` key
    payload = data.get("data") if isinstance(data.get("data"), dict) else {}
    room_id = data.get("room_id") or payload.get("room_id") or "default"
    conf = data.get("config") or payload.get("config")
    if not isinstance(conf, dict) or not conf:
        conf = {"room_id": room_id, "context": ctx.context_handler.get_context()}

    logger.debug(f"room_id={room_id}, user_id={user_id}, conf 타입={type(conf)}")
    logger.debug(f"room_save - about to upsert room for user_id={user_id} room_id={room_id}")

    title = conf.get("title") or room_id
    context_json = json.dumps(conf.get("context") or {}, ensure_ascii=False)
    logger.debug("upsert_room 호출 전")
    await ctx.db_handler.upsert_room(room_id, user_id, title, context_json)
    logger.debug("upsert_room 완료")
    logger.debug(f"room_save - upserted room: user_id={user_id} room_id={room_id} title={title}")
    logger.debug(f"room_save - upsert_room completed for user_id={user_id} room_id={room_id}")

    await websocket.send(
        json.dumps({"action": "room_save", "data": {"success": True, "room_id": room_id}})
    )
    logger.debug("room_save 응답 전송 완료")


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
    logger.debug(
        f"room_load - get_room result for user_id={user_id} room_id={room_id}: {bool(db_row)}"
    )
    logger.debug(f"room_load - db_row for user_id={user_id} room_id={room_id}: {db_row}")
    if not db_row:
        await websocket.send(
            json.dumps(
                {"action": "room_load", "data": {"success": False, "error": "room not found"}}
            )
        )
        return
    try:
        ctx_obj = json.loads(db_row.get("context") or "{}")
    except (json.JSONDecodeError, TypeError) as exc:
        logger.debug("room_load - context JSON 파싱 실패, 빈 컨텍스트로 대체", exc_info=exc)
        ctx_obj = {}

    # ContextHandler에 자동 적용 (채팅방별 독립 설정)
    if ctx_obj and ctx.context_handler:
        ctx.context_handler.load_from_dict(ctx_obj)

    # 페이지네이션: 최근 50개만 로드 (성능 최적화)
    MESSAGE_LIMIT = 50

    # 가능한 경우, DB에 저장된 메시지를 읽어와 세션의 room 히스토리에 복원
    try:
        _, sess = sm.get_or_create_session(ctx, websocket, user_id)
        rid, room = sm.get_room(ctx, sess, room_id)
        if ctx.db_handler:
            try:
                rows = await ctx.db_handler.list_messages(room_id, user_id, limit=MESSAGE_LIMIT)
            except sqlite3.Error as exc:
                logger.debug("room_load - DB에서 메시지 조회 실패", exc_info=exc)
                rows = []

            logger.debug(
                f"room_load - fetched {len(rows)} messages from DB for room={room_id} user_id={user_id}"
            )
            try:
                room["history"].clear()
                for m in rows:
                    role = m.get("role")
                    content = m.get("content") or ""
                    if role == "user":
                        room["history"].add_user_message(content)
                    else:
                        room["history"].add_assistant_message(content)
            except (KeyError, AttributeError, TypeError) as exc:
                logger.debug("room_load - 히스토리 복원 중 문제 발생", exc_info=exc)
    except (sqlite3.Error, RuntimeError) as exc:
        # 세션 생성 또는 DB 오류 시 복원 시도만 하고 계속 진행
        logger.debug("room_load - 세션 생성 또는 DB 접근 중 오류", exc_info=exc)

    # 응답에 히스토리(있을 경우)를 포함시켜 클라이언트가 바로 렌더링
    history_rows = []
    has_more = False
    try:
        if ctx.db_handler:
            history_rows = await ctx.db_handler.list_messages(room_id, user_id, limit=MESSAGE_LIMIT)
            # 더 이전 메시지가 있는지 확인
            if history_rows:
                oldest_id = history_rows[0].get("message_id")
                if oldest_id:
                    older = await ctx.db_handler.list_messages(
                        room_id, user_id, limit=1, before_id=oldest_id
                    )
                    has_more = len(older) > 0
            logger.debug(
                f"room_load - including {len(history_rows)} history rows in response for room={room_id} user_id={user_id}, has_more={has_more}"
            )
    except sqlite3.Error as exc:
        logger.debug("room_load - 응답에 포함할 히스토리 조회 실패", exc_info=exc)
        history_rows = []

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
                        "history": history_rows,
                        "has_more": has_more,
                    },
                },
            }
        )
    )


async def load_more_messages(ctx: AppContext, websocket, data: dict):
    """이전 메시지 추가 로드 (페이지네이션)

    Args:
        room_id: 채팅방 ID
        before_id: 이 message_id 이전 메시지 로드
    """
    if not ctx.db_handler:
        await websocket.send(
            json.dumps(
                {"action": "load_more_messages", "data": {"success": False, "error": "DB 없음"}}
            )
        )
        return

    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps(
                {"action": "load_more_messages", "data": {"success": False, "error": "인증 필요"}}
            )
        )
        return

    room_id = data.get("room_id") or "default"
    before_id = data.get("before_id")

    if not before_id:
        await websocket.send(
            json.dumps(
                {
                    "action": "load_more_messages",
                    "data": {"success": False, "error": "before_id 필요"},
                }
            )
        )
        return

    MESSAGE_LIMIT = 50

    try:
        messages = await ctx.db_handler.list_messages(
            room_id, user_id, limit=MESSAGE_LIMIT, before_id=before_id
        )

        # 더 이전 메시지가 있는지 확인
        has_more = False
        if messages:
            oldest_id = messages[0].get("message_id")
            if oldest_id:
                older = await ctx.db_handler.list_messages(
                    room_id, user_id, limit=1, before_id=oldest_id
                )
                has_more = len(older) > 0

        await websocket.send(
            json.dumps(
                {
                    "action": "load_more_messages",
                    "data": {
                        "success": True,
                        "room_id": room_id,
                        "messages": messages,
                        "has_more": has_more,
                    },
                }
            )
        )
    except sqlite3.Error as exc:
        logger.error(f"load_more_messages - DB 오류: {exc}")
        await websocket.send(
            json.dumps(
                {"action": "load_more_messages", "data": {"success": False, "error": "DB 오류"}}
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

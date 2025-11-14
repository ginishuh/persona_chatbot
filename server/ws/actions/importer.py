from __future__ import annotations

import json
import time
import uuid
from typing import Any

from server.core import session_manager as sm
from server.core.app_context import AppContext


def _gen_room_id(prefix: str = "imported") -> str:
    return f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:6]}"


async def _import_single_room(
    ctx: AppContext,
    session_key: str,
    room_obj: dict,
    *,
    target_room_id: str | None,
    duplicate_policy: str,
) -> tuple[str, int]:
    """단일 방 import 처리. 반환: (room_id, messages_imported)"""
    rid = target_room_id or room_obj.get("room_id") or _gen_room_id("room")
    title = room_obj.get("title") or rid
    context = room_obj.get("context") or {}

    # DB upsert
    if ctx.db_handler:
        try:
            await ctx.db_handler.upsert_room(
                rid, session_key, title, json.dumps(context, ensure_ascii=False)
            )
        except Exception:
            pass

    # 메모리 세션 방 핸들
    _, sess = sm.get_or_create_session(ctx, None, {"session_key": session_key})
    _, room = sm.get_room(ctx, sess, rid)

    # 메시지 삽입(간단 정책)
    messages = room_obj.get("messages") or []
    imported = 0

    # 중복 방지: 최근 메시지 몇 개를 메모리에서 읽어 간단 비교(역할+내용)
    recent = set()
    try:
        for m in room["history"].get_history()[-50:]:
            recent.add((m.get("role"), m.get("content")))
    except Exception:
        pass

    for m in messages:
        role = m.get("role") or "assistant"
        content = m.get("content") or ""
        if duplicate_policy == "skip" and (role, content) in recent:
            continue
        # 메모리 추가
        if role == "user":
            room["history"].add_user_message(content)
        else:
            room["history"].add_assistant_message(content)
        # DB 저장
        try:
            if ctx.db_handler:
                await ctx.db_handler.save_message(rid, role, content)
        except Exception:
            pass
        imported += 1

    return rid, imported


async def import_data(ctx: AppContext, websocket, data: dict[str, Any]):
    """WS Import(최소 구현)

    입력
    - import_mode: "new" | "merge"
    - target_room_id: (merge일 때)
    - duplicate_policy: "skip" | "add"
    - json_data: export JSON 객체(single_room or full_backup)
    """
    try:
        import_mode = (data.get("import_mode") or "new").lower()
        duplicate_policy = (data.get("duplicate_policy") or "skip").lower()
        if duplicate_policy not in {"skip", "add"}:
            duplicate_policy = "skip"
        target_room_id = data.get("target_room_id") if import_mode == "merge" else None
        payload = data.get("json_data") or {}

        # 세션키 확보
        session_key, _ = sm.get_or_create_session(ctx, websocket, data)

        exported_type = (payload.get("export_type") or "").lower()
        new_room_ids: list[str] = []
        messages_imported = 0

        if exported_type == "single_room":
            room = payload.get("room") or {}
            rid, cnt = await _import_single_room(
                ctx,
                session_key,
                room,
                target_room_id=target_room_id,
                duplicate_policy=duplicate_policy,
            )
            new_room_ids.append(rid)
            messages_imported += cnt
        elif exported_type in {"full_backup", "selected"}:
            rooms = payload.get("rooms") or []
            for r in rooms:
                rid, cnt = await _import_single_room(
                    ctx, session_key, r, target_room_id=None, duplicate_policy=duplicate_policy
                )
                new_room_ids.append(rid)
                messages_imported += cnt
        else:
            # 포맷이 명시되지 않았거나 알 수 없는 경우: room/messages 예상
            room = payload.get("room") or payload
            rid, cnt = await _import_single_room(
                ctx,
                session_key,
                room,
                target_room_id=target_room_id,
                duplicate_policy=duplicate_policy,
            )
            new_room_ids.append(rid)
            messages_imported += cnt

        await websocket.send(
            json.dumps(
                {
                    "action": "import_data",
                    "data": {
                        "success": True,
                        "rooms_imported": len(new_room_ids),
                        "messages_imported": messages_imported,
                        "new_room_ids": new_room_ids,
                    },
                }
            )
        )
    except Exception as exc:
        await websocket.send(
            json.dumps({"action": "import_data", "data": {"success": False, "error": str(exc)}})
        )

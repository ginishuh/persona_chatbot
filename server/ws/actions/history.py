from __future__ import annotations

import json
import logging

from server.core import session_manager as sm
from server.core.app_context import AppContext

logger = logging.getLogger(__name__)

NARRATIVE_PAGE_SIZE = 50


def _messages_to_narrative_markdown(messages: list[dict], start_index: int = 1) -> str:
    """메시지 목록을 서사 마크다운으로 변환"""
    if not messages:
        return ""

    md = ""
    for i, msg in enumerate(messages, start_index):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        if role == "user":
            md += f"## {i}. 사용자\n\n{content}\n\n"
        else:
            md += f"## {i}. AI 응답\n\n{content}\n\n---\n\n"
    return md


async def get_narrative(ctx: AppContext, websocket, data: dict):
    """서사 조회 (페이지네이션 지원, 최신 50개부터)"""
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps(
                {"action": "get_narrative", "data": {"success": False, "error": "인증 필요"}}
            )
        )
        return

    room_id = data.get("room_id") or "default"

    if not ctx.db_handler:
        await websocket.send(
            json.dumps({"action": "get_narrative", "data": {"success": False, "error": "DB 없음"}})
        )
        return

    # DB에서 최신 메시지 조회
    messages = await ctx.db_handler.list_messages(room_id, user_id, limit=NARRATIVE_PAGE_SIZE)

    if not messages:
        await websocket.send(
            json.dumps(
                {
                    "action": "get_narrative",
                    "data": {
                        "success": True,
                        "markdown": "# 서사 기록\n\n아직 대화가 없습니다.\n",
                        "has_more": False,
                        "oldest_id": None,
                        "total_count": 0,
                    },
                }
            )
        )
        return

    # 전체 메시지 수 조회 (시작 인덱스 계산용)
    all_messages = await ctx.db_handler.list_messages(room_id, user_id, limit=None)
    total_count = len(all_messages)

    # 더 이전 메시지가 있는지 확인
    has_more = False
    oldest_id = messages[0].get("message_id") if messages else None
    if oldest_id:
        older = await ctx.db_handler.list_messages(room_id, user_id, limit=1, before_id=oldest_id)
        has_more = len(older) > 0

    # 시작 인덱스 계산 (전체에서 현재 로드된 위치)
    start_index = total_count - len(messages) + 1

    # 마크다운 생성
    narrative_md = "# 서사 기록\n\n"
    narrative_md += _messages_to_narrative_markdown(messages, start_index)

    await websocket.send(
        json.dumps(
            {
                "action": "get_narrative",
                "data": {
                    "success": True,
                    "markdown": narrative_md,
                    "has_more": has_more,
                    "oldest_id": oldest_id,
                    "total_count": total_count,
                },
            }
        )
    )


async def load_more_narrative(ctx: AppContext, websocket, data: dict):
    """이전 서사 추가 로드 (페이지네이션)"""
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps(
                {"action": "load_more_narrative", "data": {"success": False, "error": "인증 필요"}}
            )
        )
        return

    room_id = data.get("room_id") or "default"
    before_id = data.get("before_id")

    if not before_id:
        await websocket.send(
            json.dumps(
                {
                    "action": "load_more_narrative",
                    "data": {"success": False, "error": "before_id 필요"},
                }
            )
        )
        return

    if not ctx.db_handler:
        await websocket.send(
            json.dumps(
                {"action": "load_more_narrative", "data": {"success": False, "error": "DB 없음"}}
            )
        )
        return

    # DB에서 이전 메시지 조회
    messages = await ctx.db_handler.list_messages(
        room_id, user_id, limit=NARRATIVE_PAGE_SIZE, before_id=before_id
    )

    if not messages:
        await websocket.send(
            json.dumps(
                {
                    "action": "load_more_narrative",
                    "data": {"success": True, "markdown": "", "has_more": False, "oldest_id": None},
                }
            )
        )
        return

    # 더 이전 메시지가 있는지 확인
    has_more = False
    oldest_id = messages[0].get("message_id") if messages else None
    if oldest_id:
        older = await ctx.db_handler.list_messages(room_id, user_id, limit=1, before_id=oldest_id)
        has_more = len(older) > 0

    # 시작 인덱스 계산
    if has_more and oldest_id:
        older_all = await ctx.db_handler.list_messages(
            room_id, user_id, before_id=oldest_id, limit=None
        )
        start_index = len(older_all) + 1
    else:
        start_index = 1

    # 마크다운 생성 (헤더 없이)
    narrative_md = _messages_to_narrative_markdown(messages, start_index)

    await websocket.send(
        json.dumps(
            {
                "action": "load_more_narrative",
                "data": {
                    "success": True,
                    "markdown": narrative_md,
                    "has_more": has_more,
                    "oldest_id": oldest_id,
                },
            }
        )
    )


async def get_full_narrative(ctx: AppContext, websocket, data: dict):
    """전체 서사 조회 (내보내기용)"""
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps(
                {"action": "get_full_narrative", "data": {"success": False, "error": "인증 필요"}}
            )
        )
        return

    room_id = data.get("room_id") or "default"

    if not ctx.db_handler:
        await websocket.send(
            json.dumps(
                {"action": "get_full_narrative", "data": {"success": False, "error": "DB 없음"}}
            )
        )
        return

    # DB에서 전체 메시지 조회
    messages = await ctx.db_handler.list_messages(room_id, user_id, limit=None)

    if not messages:
        await websocket.send(
            json.dumps(
                {
                    "action": "get_full_narrative",
                    "data": {
                        "success": True,
                        "markdown": "# 서사 기록\n\n아직 대화가 없습니다.\n",
                    },
                }
            )
        )
        return

    # 마크다운 생성
    narrative_md = "# 서사 기록\n\n"
    narrative_md += _messages_to_narrative_markdown(messages, 1)

    await websocket.send(
        json.dumps(
            {"action": "get_full_narrative", "data": {"success": True, "markdown": narrative_md}}
        )
    )


async def get_history_settings(ctx: AppContext, websocket, data: dict):
    # JWT 토큰에서 user_id 추출
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps(
                {"action": "get_history_settings", "data": {"success": False, "error": "인증 필요"}}
            )
        )
        return

    _, sess = sm.get_or_create_session(ctx, websocket, user_id)
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
        # JWT 토큰에서 user_id 추출
        user_id = sm.get_user_id_from_token(ctx, data)
        if not user_id:
            await websocket.send(
                json.dumps(
                    {
                        "action": "set_history_limit",
                        "data": {"success": False, "error": "인증 필요"},
                    }
                )
            )
            return

        _, sess = sm.get_or_create_session(ctx, websocket, user_id)
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
    # JWT 토큰에서 user_id 추출
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps(
                {"action": "clear_history", "data": {"success": False, "error": "인증 필요"}}
            )
        )
        return

    _, sess = sm.get_or_create_session(ctx, websocket, user_id)
    room_id = data.get("room_id")
    _, room = sm.get_room(ctx, sess, room_id)
    room["history"].clear()
    sm.clear_client_sessions(ctx, websocket, room_id=room_id)
    ctx.token_usage_handler.clear_usage(str(user_id), room_id)  # 레거시 호환용
    await websocket.send(
        json.dumps(
            {
                "action": "clear_history",
                "data": {"success": True, "message": "대화 히스토리가 초기화되었습니다"},
            }
        )
    )


async def reset_sessions(ctx: AppContext, websocket, data: dict):
    # JWT 토큰에서 user_id 추출
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps(
                {"action": "reset_sessions", "data": {"success": False, "error": "인증 필요"}}
            )
        )
        return

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
        # JWT 토큰에서 user_id 추출
        user_id = sm.get_user_id_from_token(ctx, data)
        if not user_id:
            await websocket.send(
                json.dumps(
                    {
                        "action": "get_history_snapshot",
                        "data": {"success": False, "error": "인증 필요"},
                    }
                )
            )
            return

        _, sess = sm.get_or_create_session(ctx, websocket, user_id)
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

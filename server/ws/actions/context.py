from __future__ import annotations

import json
import logging
from typing import Any

from server.core import session_manager as sm
from server.core.app_context import AppContext

logger = logging.getLogger(__name__)


async def set_context(ctx: AppContext, websocket, data: dict[str, Any]):
    """컨텍스트 설정 (History/API 라우팅 이후 공용 액션)

    - room_id가 있으면 해당 채팅방의 context를 DB에 저장
    - room_id가 없으면 전역 context만 업데이트 (기존 동작)
    - 컨텍스트 변경 시 핵심 프롬프트 관련 키 변화가 있으면 프로바이더 세션을 리셋합니다.
    """
    ch = ctx.context_handler
    if ch is None:
        await websocket.send(
            json.dumps(
                {
                    "action": "set_context",
                    "data": {"success": False, "error": "context handler missing"},
                }
            )
        )
        return

    room_id = data.get("room_id")
    world = data.get("world", "")
    situation = data.get("situation", "")
    user_character = data.get("user_character", "")
    characters = data.get("characters", [])
    narrator_enabled = data.get("narrator_enabled", False)
    narrator_mode = data.get("narrator_mode", "moderate")
    narrator_description = data.get("narrator_description", "")
    user_is_narrator = data.get("user_is_narrator", False)
    adult_level = data.get("adult_level", "explicit")
    narrative_separation = data.get("narrative_separation", False)
    ai_provider = data.get("ai_provider", "claude")
    output_level = data.get("output_level")
    pace = data.get("pace")
    narrator_drive = data.get("narrator_drive")
    choice_policy = data.get("choice_policy")
    choice_count = data.get("choice_count")
    conversation_mode = data.get("conversation_mode")

    prev_ctx = ch.get_context()
    ch.set_world(world)
    ch.set_situation(situation)
    ch.set_user_character(user_character)
    ch.set_narrator(narrator_enabled, narrator_mode, narrator_description, user_is_narrator)
    ch.set_adult_level(adult_level)
    ch.set_narrative_separation(narrative_separation)
    ch.set_ai_provider(ai_provider)
    ch.set_characters(characters)
    if output_level is not None:
        ch.set_output_level(output_level)
    if pace is not None:
        ch.set_pace(pace)
    if narrator_drive is not None:
        ch.set_narrator_drive(narrator_drive)
    if choice_policy is not None:
        ch.set_choice_policy(choice_policy)
    if choice_count is not None:
        ch.set_choice_count(choice_count)
    if conversation_mode is not None:
        ch.set_conversation_mode(conversation_mode)

    # room_id가 있으면 DB에 저장 (user_id 기반)
    if room_id and ctx.db_handler:
        try:
            # JWT 토큰에서 user_id 추출
            user_id = sm.get_user_id_from_token(ctx, data)
            if not user_id:
                logger.warning("No user_id found in token, skipping DB save")
            else:
                # 기존 room 정보 가져오기 (title 유지)
                existing_room = await ctx.db_handler.get_room(room_id, user_id)
                title = existing_room["title"] if existing_room else room_id

                # context를 JSON으로 변환하여 저장
                context_json = json.dumps(ch.get_context(), ensure_ascii=False)
                await ctx.db_handler.upsert_room(room_id, user_id, title, context_json)
                logger.info(f"Room context saved to DB: room_id={room_id}, user_id={user_id}")
        except Exception as e:
            logger.error(f"Failed to save room context to DB: {e}")

    await websocket.send(
        json.dumps(
            {"action": "set_context", "data": {"success": True, "context": ch.get_context()}}
        )
    )

    # 중요 키 변경 시 세션 리셋(프롬프트 재적용)
    try:
        new_ctx = ch.get_context()
        keys = [
            "adult_level",
            "narrative_separation",
            "output_level",
            "pace",
            "narrator_drive",
            "narrator_enabled",
            "narrator_mode",
            "choice_policy",
            "choice_count",
        ]
        if any(prev_ctx.get(k) != new_ctx.get(k) for k in keys):
            sm.clear_client_sessions(ctx, websocket)
            logger.info("Context changed; provider sessions reset for fresh prompt application")
    except Exception:
        pass


async def get_context(ctx: AppContext, websocket, data: dict[str, Any]):
    """컨텍스트 가져오기

    - room_id가 있으면 DB에서 해당 채팅방의 context를 로드하여 ContextHandler에 적용
    - room_id가 없으면 현재 ContextHandler의 context 반환 (기존 동작)
    """
    ch = ctx.context_handler
    if ch is None:
        await websocket.send(
            json.dumps(
                {
                    "action": "get_context",
                    "data": {"success": False, "error": "context handler missing"},
                }
            )
        )
        return

    room_id = data.get("room_id")

    # room_id가 있으면 DB에서 로드 (user_id 기반)
    if room_id and ctx.db_handler:
        try:
            # JWT 토큰에서 user_id 추출
            user_id = sm.get_user_id_from_token(ctx, data)
            if not user_id:
                logger.warning("No user_id found in token, skipping DB load")
            else:
                # user_id로 방 조회
                room = await ctx.db_handler.get_room(room_id, user_id)
                if room and room.get("context"):
                    # JSON 문자열을 dict로 파싱
                    context_dict = json.loads(room["context"])
                    # ContextHandler에 적용
                    ch.load_from_dict(context_dict)
                    logger.info(
                        f"Room context loaded from DB: room_id={room_id}, user_id={user_id}"
                    )
        except Exception as e:
            logger.error(f"Failed to load room context from DB: {e}")

    await websocket.send(
        json.dumps(
            {"action": "get_context", "data": {"success": True, "context": ch.get_context()}}
        )
    )

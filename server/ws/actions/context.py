from __future__ import annotations

import json
import logging
from typing import Any

from server.core import session_manager as sm
from server.core.app_context import AppContext

logger = logging.getLogger(__name__)


async def set_context(ctx: AppContext, websocket, data: dict[str, Any]):
    """컨텍스트 설정 (History/API 라우팅 이후 공용 액션)

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
    narrator_drive = data.get("narrator_drive")
    choice_policy = data.get("choice_policy")
    choice_count = data.get("choice_count")

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
    if narrator_drive is not None:
        ch.set_narrator_drive(narrator_drive)
    if choice_policy is not None:
        ch.set_choice_policy(choice_policy)
    if choice_count is not None:
        ch.set_choice_count(choice_count)

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


async def get_context(ctx: AppContext, websocket, _data: dict[str, Any]):
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
    await websocket.send(
        json.dumps(
            {"action": "get_context", "data": {"success": True, "context": ch.get_context()}}
        )
    )

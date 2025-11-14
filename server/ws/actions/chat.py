from __future__ import annotations

import json
from typing import Any

from server.core import session_manager as sm
from server.core.app_context import AppContext


async def chat(ctx: AppContext, websocket, data: dict):
    """주요 채팅 액션(스트리밍 포함). 기존 로직을 모듈로 분리.

    입력 데이터 예:
        {
          action: 'chat',
          prompt: '...',
          provider: 'claude' | 'droid' | 'gemini',
          model?: string,
          room_id?: string
        }
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.info("[DEBUG] chat 핸들러 시작")

    prompt = data.get("prompt", "")
    provider = data.get("provider", ctx.context_handler.get_context().get("ai_provider", "claude"))
    logger.info(f"[DEBUG] provider={provider}, prompt 길이={len(prompt)}")

    # 세션/채팅방
    session_key, sess = sm.get_or_create_session(ctx, websocket, data)
    rid, room = sm.get_room(ctx, sess, data.get("room_id"))
    provider_sessions: dict[str, Any] = room.setdefault("provider_sessions", {})
    retention_enabled = sm.is_session_retention_enabled(ctx, websocket, sess)
    provider_session_id = provider_sessions.get(provider) if retention_enabled else None

    # 성인 동의 확인
    try:
        level = (ctx.context_handler.get_context().get("adult_level") or "").lower()
        consent = sess.get("settings", {}).get("adult_consent", False)
        if level in {"enhanced", "extreme"} and not consent:
            await websocket.send(
                json.dumps(
                    {
                        "action": "consent_required",
                        "data": {
                            "required": True,
                            "message": "성인 전용 기능입니다. 본인은 성인이며 이용에 따른 모든 책임은 사용자 본인에게 있음을 동의해야 합니다.",
                        },
                    }
                )
            )
            return
    except Exception:
        pass

    # 사용자 메시지 추가 + DB에 세션/방 보장 후 저장
    room["history"].add_user_message(prompt)
    try:
        if ctx.db_handler:
            await ctx.db_handler.upsert_session(session_key)
            await ctx.db_handler.upsert_room(rid, session_key, rid, None)
            await ctx.db_handler.save_message(rid, "user", prompt, session_key)
    except Exception:
        pass

    # 히스토리 텍스트 주입 여부 결정
    provider_supports_session = provider in ("claude", "droid")
    if retention_enabled and provider_supports_session and provider_session_id:
        history_text = ""
    else:
        history_text = room["history"].get_history_text()

    # 시스템 프롬프트
    system_prompt = ctx.context_handler.build_system_prompt(history_text)

    async def stream_callback(json_data):
        await websocket.send(json.dumps({"action": "chat_stream", "data": json_data}))

    # 제공자별 처리
    model = data.get("model")
    if provider == "droid":
        handler = ctx.droid_handler
        result = await handler.send_message(
            prompt,
            system_prompt=system_prompt,
            callback=stream_callback,
            session_id=provider_session_id,
            model=None,  # 서버 기본 사용
        )
    elif provider == "gemini":
        handler = ctx.gemini_handler
        result = await handler.send_message(
            prompt,
            system_prompt=system_prompt,
            callback=stream_callback,
            session_id=provider_session_id,
            model=model,
        )
    else:
        handler = ctx.claude_handler
        logger.info(f"[DEBUG] Claude handler 호출 전 - handler={handler}")
        result = await handler.send_message(
            prompt,
            system_prompt=system_prompt,
            callback=stream_callback,
            session_id=provider_session_id,
            model=model,
        )
        logger.info(
            f"[DEBUG] Claude handler 호출 후 - result={result.get('success') if result else None}"
        )

    # 응답 히스토리 반영
    if result.get("success") and result.get("message"):
        msg = result["message"]
        room["history"].add_assistant_message(msg)
        try:
            if ctx.db_handler:
                await ctx.db_handler.save_message(rid, "assistant", msg, session_key)
        except Exception:
            pass

    # 토큰 사용량 집계
    token_info = result.get("token_info")
    if token_info is not None:
        ctx.token_usage_handler.add_usage(
            session_key=session_key,
            room_id=rid,
            provider=provider,
            token_info=token_info,
        )
        # DB에도 저장 (export용)
        if ctx.db_handler:
            try:
                await ctx.db_handler.save_token_usage(
                    session_key=session_key,
                    room_id=rid,
                    provider=provider,
                    token_info=token_info,
                )
            except Exception as e:
                logger.error(f"Failed to save token usage to DB: {e}")

    token_summary = ctx.token_usage_handler.get_formatted_summary(
        session_key=session_key, room_id=rid
    )

    # 세션 유지 시 세션ID 업데이트
    new_session_id = result.get("session_id")
    if retention_enabled and new_session_id:
        provider_sessions[provider] = new_session_id
    elif not retention_enabled:
        provider_sessions.pop(provider, None)

    await websocket.send(
        json.dumps(
            {
                "action": "chat_complete",
                "data": {**result, "provider_used": provider, "token_usage": token_summary},
            }
        )
    )

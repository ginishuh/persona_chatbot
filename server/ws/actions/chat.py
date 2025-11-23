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

    # JWT 토큰에서 user_id 추출
    user_id = sm.get_user_id_from_token(ctx, data)
    if not user_id:
        await websocket.send(
            json.dumps(
                {"action": "chat_complete", "data": {"success": False, "error": "인증 필요"}}
            )
        )
        return

    # 사용자 세션/채팅방
    user_id, sess = sm.get_or_create_session(ctx, websocket, user_id)
    rid, room = sm.get_room(ctx, sess, data.get("room_id"))
    provider_sessions: dict[str, Any] = room.setdefault("provider_sessions", {})

    speaker = data.get("speaker")

    def get_provider_session_id():
        # 캐릭터별 세션 지원: provider별 dict로 세션 분리
        sess = provider_sessions.get(provider)
        if speaker:
            if isinstance(sess, dict):
                return sess.get(speaker)
            return None
        return sess if not isinstance(sess, dict) else None

    provider_session_id = get_provider_session_id()

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

    # 사용자 메시지 추가 + DB에 방/메시지 저장
    room["history"].add_user_message(prompt)
    try:
        if ctx.db_handler:
            # 방이 없으면 최소 정보로 생성, 이미 있으면 기존 컨텍스트/제목 유지
            existing_room = await ctx.db_handler.get_room(rid, user_id)
            if existing_room is None:
                await ctx.db_handler.upsert_room(rid, user_id, rid, None)
            await ctx.db_handler.save_message(rid, "user", prompt, user_id)
    except Exception:
        pass

    # 히스토리 텍스트: 세션이 있어도 최근 윈도우를 항상 포함
    history_text = room["history"].get_history_text()

    # 시스템 프롬프트
    system_prompt = ctx.context_handler.build_system_prompt(history_text)
    if data.get("speaker"):
        sp = data.get("speaker")
        # 화자 캐릭터 프로필을 찾아 추가
        try:
            char_profile = None
            ctx_chars = ctx.context_handler.get_context().get("characters", [])
            for ch in ctx_chars:
                if isinstance(ch, dict) and ch.get("name") == sp:
                    char_profile = ch
                    break
            profile_str = ""
            if char_profile:
                desc = char_profile.get("description") or ""
                gender = char_profile.get("gender") or ""
                age = char_profile.get("age") or ""
                meta = ", ".join(filter(None, [gender, age]))
                if meta:
                    profile_str += f"{meta}. "
                if desc:
                    profile_str += desc
            system_prompt = (
                f"[현재 화자: {sp}. 이번 턴에는 {sp}만 발화합니다. 다른 캐릭터나 내레이터는 말하지 않습니다. 짧게 말하세요."
                + (f" {profile_str}" if profile_str else "")
                + "]\n"
                + system_prompt
            )
        except Exception:
            system_prompt = (
                f"[현재 화자: {sp}. 이번 턴에는 {sp}만 발화합니다. 다른 캐릭터나 내레이터는 말하지 않습니다. 짧게 말하세요.]\n"
                + system_prompt
            )

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
                await ctx.db_handler.save_message(rid, "assistant", msg, user_id)
        except Exception:
            pass

    # 토큰 사용량 집계
    token_info = result.get("token_info")
    if token_info is not None:
        ctx.token_usage_handler.add_usage(
            session_key=str(user_id),  # token_usage_handler는 레거시 호환용
            room_id=rid,
            provider=provider,
            token_info=token_info,
        )
        # DB에도 저장 (export용)
        if ctx.db_handler:
            try:
                await ctx.db_handler.save_token_usage(
                    user_id=user_id,
                    room_id=rid,
                    provider=provider,
                    token_info=token_info,
                )
            except Exception as e:
                logger.error(f"Failed to save token usage to DB: {e}")

    token_summary = ctx.token_usage_handler.get_formatted_summary(
        session_key=str(user_id), room_id=rid  # 레거시 호환용
    )

    # 프로바이더 세션ID 업데이트
    new_session_id = result.get("session_id")
    if new_session_id:
        if speaker:
            # provider별 dict로 관리
            if not isinstance(provider_sessions.get(provider), dict):
                provider_sessions[provider] = {}
            provider_sessions[provider][speaker] = new_session_id
        else:
            provider_sessions[provider] = new_session_id
    else:
        if speaker and isinstance(provider_sessions.get(provider), dict):
            provider_sessions[provider].pop(speaker, None)
        else:
            provider_sessions.pop(provider, None)

    await websocket.send(
        json.dumps(
            {
                "action": "chat_complete",
                "data": {**result, "provider_used": provider, "token_usage": token_summary},
            }
        )
    )

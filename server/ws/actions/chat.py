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

    # 세션유지 설정 확인 (방 컨텍스트에서)
    session_retention = ctx.context_handler.get_context().get("session_retention", False)
    logger.debug(f"session_retention={session_retention}")

    def get_provider_session_id():
        # 세션유지가 OFF면 항상 None 반환 (새 세션)
        if not session_retention:
            return None
        # 캐릭터별 세션 지원: provider별 dict로 세션 분리
        sess = provider_sessions.get(provider)
        if speaker:
            if isinstance(sess, dict):
                return sess.get(speaker)
            return None
        return sess if not isinstance(sess, dict) else None

    provider_session_id = get_provider_session_id()

    # 세션 ON인데 현재 프로바이더 세션이 없으면 DB에서 해당 프로바이더만 복원
    # (다른 프로바이더 세션이 있어도 현재 프로바이더는 복원해야 함)
    if session_retention and provider_session_id is None and ctx.db_handler:
        try:
            db_room = await ctx.db_handler.get_room(rid, user_id)
            if db_room:
                ps_json = db_room.get("provider_sessions") or "{}"
                db_sessions = json.loads(ps_json)
                db_provider_sess = db_sessions.get(provider)
                if db_provider_sess:
                    provider_sessions[provider] = db_provider_sess
                    provider_session_id = get_provider_session_id()
                    logger.info(f"chat - 세션 복원 (DB→메모리): provider={provider}")
        except Exception as exc:
            logger.debug(f"chat - 세션 복원 실패: {exc}")
    logger.debug(f"provider_session_id={provider_session_id[:8] if provider_session_id else None}")

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

    # 히스토리 텍스트: 세션 연동 시 생략 (CLI가 이미 기억하고 있음)
    if session_retention and provider_session_id:
        # 세션 이어가기 - CLI가 대화 기록을 자체 관리하므로 히스토리 생략
        history_text = ""
        logger.debug(f"세션 연동 중 - 히스토리 생략 (session_id={provider_session_id[:8]}...)")
    else:
        # 새 세션 또는 세션 연동 OFF - 히스토리 포함
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

            single_speaker_guard = (
                f"[현재 화자: {sp}. 이번 턴에는 {sp}만 발화합니다. 다른 캐릭터나 내레이터는 말하지 않습니다. "
                "반드시 한 캐릭터 한 줄만 말하세요. 다른 사람 이름이나 대사를 쓰지 말고, 대괄호/콜론 없이 순수 대사만 출력하세요."
            )
            if profile_str:
                single_speaker_guard += f" {profile_str}"
            single_speaker_guard += "]\n"

            system_prompt = single_speaker_guard + system_prompt
        except Exception:
            system_prompt = (
                f"[현재 화자: {sp}. 이번 턴에는 {sp}만 발화합니다. 다른 캐릭터나 내레이터는 말하지 않습니다. 한 줄만, 다른 이름 없이 말하세요.]\n"
                + system_prompt
            )

    # 스트리밍 시작 시 취소 플래그 초기화
    ctx.cancel_flags[websocket] = False

    class StreamCancelled(Exception):
        """스트림 취소 예외"""

        pass

    async def stream_callback(json_data):
        # 취소 플래그 확인
        if ctx.cancel_flags.get(websocket, False):
            raise StreamCancelled("Stream cancelled by user")
        await websocket.send(json.dumps({"action": "chat_stream", "data": json_data}))

    # 제공자별 처리
    model = data.get("model")
    try:
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
    except StreamCancelled:
        logger.info("Stream cancelled by user")
        result = {"success": False, "error": "cancelled", "cancelled": True}
        await websocket.send(json.dumps({"action": "chat_complete", "data": result}))
        return

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
    should_save_to_db = False

    if session_retention and new_session_id:
        # 세션유지 ON + 새 세션 → 메모리 및 DB 저장
        if speaker:
            if not isinstance(provider_sessions.get(provider), dict):
                provider_sessions[provider] = {}
            provider_sessions[provider][speaker] = new_session_id
        else:
            provider_sessions[provider] = new_session_id
        should_save_to_db = True
    elif not session_retention:
        # 세션유지 OFF → 메모리만 비움, DB는 건드리지 않음 (토글 실수 방지)
        if speaker and isinstance(provider_sessions.get(provider), dict):
            provider_sessions[provider].pop(speaker, None)
        else:
            provider_sessions.pop(provider, None)
        # should_save_to_db = False (DB 보존)

    # 프로바이더가 세션 에러 반환 시 해당 세션만 DB에서 삭제
    # (실제로 죽은 세션만 정리 - 만료/인증 에러)
    session_error = result.get("session_expired") or result.get("session_invalid")
    if session_error and provider_session_id:
        logger.info(f"세션 에러 감지 - DB에서 세션 삭제: provider={provider}")
        if speaker and isinstance(provider_sessions.get(provider), dict):
            provider_sessions[provider].pop(speaker, None)
        else:
            provider_sessions.pop(provider, None)
        should_save_to_db = True

    # provider_sessions를 DB에 저장 (세션 ON 저장 또는 세션 에러 정리 시만)
    if ctx.db_handler and should_save_to_db:
        try:
            provider_sessions_json = json.dumps(provider_sessions, ensure_ascii=False)
            existing_room = await ctx.db_handler.get_room(rid, user_id)
            if existing_room:
                await ctx.db_handler.upsert_room(
                    rid,
                    user_id,
                    existing_room.get("title") or rid,
                    existing_room.get("context"),
                    provider_sessions_json,
                )
                logger.debug(f"chat - provider_sessions DB 저장 완료: {rid}")
        except Exception as exc:
            logger.debug(f"chat - provider_sessions DB 저장 실패: {exc}")

    await websocket.send(
        json.dumps(
            {
                "action": "chat_complete",
                "data": {**result, "provider_used": provider, "token_usage": token_summary},
            }
        )
    )

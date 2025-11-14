"""인증/JWT 유틸리티 (검증/요구 메시지)"""

from __future__ import annotations

import json

import jwt

from .app_context import AppContext


def verify_token(ctx: AppContext, token: str | None, expected_type: str = "access"):
    """JWT 검증: (payload, error_code) 반환."""
    if not ctx.jwt_secret:
        return None, "jwt_disabled"
    if not token:
        return None, "missing_token"
    try:
        payload = jwt.decode(token, ctx.jwt_secret, algorithms=[ctx.jwt_algorithm])
        typ = payload.get("typ", "access")
        if expected_type and typ != expected_type:
            return None, "invalid_token_type"
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "token_expired"
    except jwt.InvalidTokenError:
        return None, "invalid_token"


async def send_auth_required(ctx: AppContext, websocket, reason: str = "missing_token"):
    await websocket.send(
        json.dumps({"action": "auth_required", "data": {"required": True, "reason": reason}})
    )

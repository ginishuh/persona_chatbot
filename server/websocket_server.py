import asyncio
import json
import logging
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path

import jwt
import websockets

from server.core import session_manager as sm
from server.core.app_context import AppContext
from server.core.auth import send_auth_required as auth_send_auth_required
from server.core.auth import verify_token as auth_verify_token
from server.handlers.claude_handler import ClaudeCodeHandler
from server.handlers.context_handler import ContextHandler
from server.handlers.db_handler import DBHandler
from server.handlers.droid_handler import DroidHandler
from server.handlers.file_handler import FileHandler
from server.handlers.gemini_handler import GeminiHandler
from server.handlers.git_handler import GitHandler
from server.handlers.history_handler import HistoryHandler
from server.handlers.mode_handler import ModeHandler
from server.handlers.token_usage_handler import TokenUsageHandler
from server.handlers.workspace_handler import WorkspaceHandler
from server.http.server import run_http_server as run_http_server_external
from server.ws.router import dispatch as ws_dispatch

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 핸들러 초기화
# 프로젝트 루트 경로 (server/ 폴더의 상위 디렉토리)
project_root = Path(__file__).parent.parent
# HTTP JWT 인증만 사용 (WebSocket 레거시 인증 제거됨)
JWT_SECRET = os.getenv("APP_JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("APP_JWT_ALGORITHM", "HS256")
ACCESS_TTL_SECONDS = int(os.getenv("APP_ACCESS_TTL", "604800"))
REFRESH_TTL_SECONDS = int(os.getenv("APP_REFRESH_TTL", "2592000"))  # 30일
BIND_HOST = os.getenv("APP_BIND_HOST", "127.0.0.1")

file_handler = FileHandler()
git_handler = GitHandler()
claude_handler = ClaudeCodeHandler()
droid_handler = DroidHandler()
gemini_handler = GeminiHandler()
context_handler = ContextHandler()
# 레거시 단일 히스토리(기본값). 채팅방 도입으로 방별 히스토리를 별도로 관리합니다.
history_handler = HistoryHandler(max_turns=30)
workspace_handler = WorkspaceHandler(str(project_root / "persona_data"))
mode_handler = ModeHandler(project_root=str(project_root))
token_usage_handler = TokenUsageHandler()
DB_PATH = os.getenv("DB_PATH", str(project_root / "data" / "chatbot.db"))
db_handler: DBHandler | None = None
APP_CTX: AppContext | None = None

# 연결된 클라이언트들
connected_clients = set()
login_attempts = {}

# 세션/채팅방 상태 관리 (웹소켓 분리, 재연결 내구성)
# - websocket_to_session: 웹소켓 → 세션키
# - sessions: 세션키 → { settings, rooms }
#   - settings: { retention_enabled: bool, adult_consent: bool }
#   - rooms: room_id → { history: HistoryHandler, provider_sessions: { provider: session_id } }
websocket_to_session: dict = {}
sessions: dict = {}


def _get_or_create_session(websocket, data: dict | None):
    if APP_CTX is None:
        raise RuntimeError("App context not initialized")
    return sm.get_or_create_session(APP_CTX, websocket, data)


def _get_room(session: dict, room_id: str | None):
    if APP_CTX is None:
        raise RuntimeError("App context not initialized")
    return sm.get_room(APP_CTX, session, room_id)


def initialize_client_state(websocket):
    if APP_CTX is None:
        raise RuntimeError("App context not initialized")
    sm.initialize_client_state(APP_CTX, websocket)


def clear_client_sessions(websocket, room_id: str | None = None):
    if APP_CTX is None:
        raise RuntimeError("App context not initialized")
    sm.clear_client_sessions(APP_CTX, websocket, room_id)


def remove_client_sessions(websocket):
    if APP_CTX is None:
        raise RuntimeError("App context not initialized")
    sm.remove_client_sessions(APP_CTX, websocket)


def is_session_retention_enabled(websocket, session: dict | None = None):
    if APP_CTX is None:
        raise RuntimeError("App context not initialized")
    return sm.is_session_retention_enabled(APP_CTX, websocket, session)


## stories 파서는 제거되었습니다(스토리 기능 비활성화).


def _issue_token(
    ttl_seconds: int, typ: str, session_key: str | None = None, user_id: int | None = None
):
    """JWT 생성 공통 함수

    Args:
        ttl_seconds: 토큰 유효 시간 (초)
        typ: 토큰 타입 ("access" 또는 "refresh")
        session_key: 세션 키 (세션별 데이터 격리용)
        user_id: 사용자 ID (회원제 시스템용)
    """
    if not JWT_SECRET:
        return None, None
    now = datetime.utcnow()
    exp = now + timedelta(seconds=ttl_seconds)
    payload = {
        "sub": "persona_chat_user",
        "iat": now,
        "exp": exp,
        "typ": typ,
    }
    if session_key:
        payload["session_key"] = session_key
    if user_id is not None:
        payload["user_id"] = user_id
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, exp.isoformat() + "Z"


def issue_access_token(session_key: str | None = None, user_id: int | None = None):
    """Access 토큰 발급

    Args:
        session_key: 세션 키 (세션별 데이터 격리용)
        user_id: 사용자 ID (회원제 시스템용)
    """
    return _issue_token(ACCESS_TTL_SECONDS, "access", session_key, user_id)


def issue_refresh_token(session_key: str | None = None, user_id: int | None = None):
    """Refresh 토큰 발급

    Args:
        session_key: 세션 키 (세션별 데이터 격리용)
        user_id: 사용자 ID (회원제 시스템용)
    """
    return _issue_token(REFRESH_TTL_SECONDS, "refresh", session_key, user_id)


def verify_token(token, expected_type: str = "access"):
    if APP_CTX is None:
        raise RuntimeError("App context not initialized")
    return auth_verify_token(APP_CTX, token, expected_type)


async def send_auth_required(websocket, reason="missing_token"):
    if APP_CTX is None:
        raise RuntimeError("App context not initialized")
    await auth_send_auth_required(APP_CTX, websocket, reason)


async def handle_login_action(websocket, data):
    """WebSocket 로그인 액션 (레거시 - HTTP API 사용 권장)

    HTTP API (/api/login)로 로그인하여 JWT 토큰을 받은 후 사용하세요.
    WebSocket에서는 더 이상 로그인 처리를 하지 않습니다.
    """
    await websocket.send(
        json.dumps(
            {
                "action": "login",
                "data": {
                    "success": False,
                    "error": "HTTP API(/api/login)로 로그인하세요. WebSocket 로그인은 더 이상 지원되지 않습니다.",
                    "code": "deprecated",
                },
            }
        )
    )


async def handle_token_refresh_action(websocket, data):
    """리프레시 토큰으로 액세스 토큰 갱신/회전"""
    refresh_token = data.get("refresh_token")
    payload, error = verify_token(refresh_token, expected_type="refresh")
    if error:
        await websocket.send(
            json.dumps({"action": "token_refresh", "data": {"success": False, "error": error}})
        )
        return

    # 기존 refresh 토큰의 session_key와 user_id 유지
    token_session_key = payload.get("session_key") if payload else None
    token_user_id = payload.get("user_id") if payload else None
    new_access, access_exp = issue_access_token(token_session_key, token_user_id)
    # 선택: refresh 토큰도 회전(보안 강화)
    rotate = bool(int(os.getenv("APP_REFRESH_ROTATE", "1")))
    if rotate:
        new_refresh, refresh_exp = issue_refresh_token(token_session_key, token_user_id)
    else:
        new_refresh, refresh_exp = refresh_token, None

    await websocket.send(
        json.dumps(
            {
                "action": "token_refresh",
                "data": {
                    "success": True,
                    "token": new_access,
                    "expires_at": access_exp,
                    "refresh_token": new_refresh,
                    "refresh_expires_at": refresh_exp,
                },
            }
        )
    )


async def handle_message(websocket, message):
    """메시지 처리"""
    try:
        data = json.loads(message)
        action = data.get("action")

        logger.info(f"Received action: {action}")

        if action == "login":
            await handle_login_action(websocket, data)
            return
        if action == "token_refresh":
            await handle_token_refresh_action(websocket, data)
            return

        # HTTP JWT 인증만 사용 (WebSocket에서는 토큰 검증하지 않음)
        # login_required=False이므로 모든 액션 허용

        # 라우터 우선 위임(등록된 액션이면 여기서 종료)
        try:
            logger.info(f"[DEBUG] ws_dispatch 호출 전 - action={action}")
            result = await ws_dispatch(APP_CTX, websocket, data)
            logger.info(f"[DEBUG] ws_dispatch 결과: {result}")
            if result:
                return
        except Exception:
            logger.exception("Router dispatch error")

        # 파일(레거시 STORIES) 관련 액션은 제거되었습니다.
        if action in {"list_files", "read_file", "write_file"}:
            await websocket.send(
                json.dumps(
                    {
                        "action": action,
                        "data": {"success": False, "error": "legacy API removed"},
                    }
                )
            )
            return

        # 나머지 등록 액션들은 라우터가 처리합니다.

        # 컨텍스트 관련 액션은 라우터에서 처리

        # history 관련 액션은 라우터에서만 처리합니다.

        # stories/rooms/history/presets/git/config/mode/session/token 등은 라우터 처리

        # 히스토리 관련 액션은 라우터 처리

        # AI 채팅 (컨텍스트 + 히스토리 포함, 채팅방 단위)
        elif action == "chat":
            logger.info(f"chat 액션 처리 시작 - prompt 길이: {len(data.get('prompt', ''))}")
            prompt = data.get("prompt", "")
            # provider 파라미터 (없으면 컨텍스트의 기본값 사용)
            provider = data.get(
                "provider", context_handler.get_context().get("ai_provider", "claude")
            )
            logger.info(f"provider 선택: {provider}")
            # 세션/채팅방 해석
            key, sess = _get_or_create_session(websocket, data)
            rid, room = _get_room(sess, data.get("room_id"))
            provider_sessions = room.setdefault("provider_sessions", {})
            retention_enabled = is_session_retention_enabled(websocket, sess)
            provider_session_id = provider_sessions.get(provider) if retention_enabled else None

            # 성인 모드 동의 확인(세션)
            try:
                ctx = context_handler.get_context()
                level = (ctx.get("adult_level") or "").lower()
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

            # 사용자 메시지를 히스토리에 추가(채팅방) + DB 영속화(가능 시)
            room["history"].add_user_message(prompt)
            try:
                if APP_CTX and APP_CTX.db_handler:
                    # 세션/방이 DB에 없을 수 있으므로 방 upsert 보장(컨텍스트는 room_save에서 관리)
                    await APP_CTX.db_handler.upsert_room(rid, key, rid, None)
                    await APP_CTX.db_handler.save_message(rid, "user", prompt, key)
            except Exception:
                logger.exception("DB save (user message) failed; continuing without DB persistence")

            # 히스토리 텍스트 가져오기(채팅방)
            # 제공자별 세션 지원 여부 확인
            provider_supports_session = provider in ("claude", "droid")
            # 세션 유지가 활성화되어 있고, 제공자가 세션을 지원하고, 기존 세션이 있으면 히스토리 주입 불필요
            # (세션으로 기억하므로 토큰 절약)
            if retention_enabled and provider_supports_session and provider_session_id:
                history_text = ""
            else:
                history_text = room["history"].get_history_text()

            # System prompt 생성 (히스토리 포함 여부는 위에서 결정)
            system_prompt = context_handler.build_system_prompt(history_text)

            # 스트리밍 콜백: 각 JSON 라인을 클라이언트에 전송
            async def stream_callback(json_data):
                await websocket.send(json.dumps({"action": "chat_stream", "data": json_data}))

            # AI 제공자 선택
            if provider == "droid":
                handler = droid_handler
            elif provider == "gemini":
                handler = gemini_handler
            else:  # claude (기본값)
                handler = claude_handler

            # 단일 시도 (폴백 없음)
            # 선택 모델(프로바이더별 사용)
            model = data.get("model")
            if provider == "gemini":
                result = await gemini_handler.send_message(
                    prompt,
                    system_prompt=system_prompt,
                    callback=stream_callback,
                    session_id=provider_session_id,
                    model=model,
                )
            elif provider == "droid":
                # 혼선 방지를 위해 서버 기본 모델(DROID_MODEL)만 사용
                result = await droid_handler.send_message(
                    prompt,
                    system_prompt=system_prompt,
                    callback=stream_callback,
                    session_id=provider_session_id,
                    model=None,
                )
            elif provider == "claude":
                result = await claude_handler.send_message(
                    prompt,
                    system_prompt=system_prompt,
                    callback=stream_callback,
                    session_id=provider_session_id,
                    model=model,
                )
            else:
                result = {"success": False, "error": f"Unknown provider: {provider}"}

            # AI 응답을 히스토리에 추가(채팅방) + DB 영속화
            if result.get("success") and result.get("message"):
                room["history"].add_assistant_message(result["message"])
                try:
                    if APP_CTX and APP_CTX.db_handler:
                        await APP_CTX.db_handler.save_message(
                            rid, "assistant", result["message"], key
                        )
                except Exception:
                    logger.exception("DB save (assistant message) failed; continuing")

            # 토큰 사용량 수집 및 누적
            token_info = result.get("token_info")
            if token_info is not None:
                token_usage_handler.add_usage(
                    session_key=key,
                    room_id=rid,
                    provider=provider,
                    token_info=token_info,
                )
                try:
                    if APP_CTX and APP_CTX.db_handler:
                        await APP_CTX.db_handler.save_token_usage(
                            session_key=key,
                            room_id=rid,
                            provider=provider,
                            token_info=token_info,
                        )
                except Exception:
                    logger.exception("DB save (token usage) failed; continuing")

            # 토큰 사용량 요약 생성
            token_summary = token_usage_handler.get_formatted_summary(
                session_key=key,
                room_id=rid,
            )

            # 최종 결과 전송
            new_session_id = result.get("session_id")
            if retention_enabled and new_session_id:
                provider_sessions[provider] = new_session_id
            elif not retention_enabled:
                provider_sessions.pop(provider, None)

            await websocket.send(
                json.dumps(
                    {
                        "action": "chat_complete",
                        "data": {
                            **result,
                            "provider_used": provider,
                            "token_usage": token_summary,
                        },
                    }
                )
            )

        else:
            await websocket.send(
                json.dumps(
                    {
                        "action": "error",
                        "data": {"success": False, "error": f"Unknown action: {action}"},
                    }
                )
            )

    except json.JSONDecodeError:
        logger.exception("Invalid JSON received")
        await websocket.send(
            json.dumps({"action": "error", "data": {"success": False, "error": "Invalid JSON"}})
        )
    except Exception as e:
        logger.exception("Error handling message")
        await websocket.send(
            json.dumps({"action": "error", "data": {"success": False, "error": str(e)}})
        )


async def websocket_handler(websocket):
    """WebSocket 연결 핸들러"""
    connected_clients.add(websocket)
    initialize_client_state(websocket)
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    logger.info(f"Client connected: {client_ip} (Total: {len(connected_clients)})")

    try:
        # 환영 메시지
        await websocket.send(
            json.dumps(
                {
                    "action": "connected",
                    "data": {
                        "success": True,
                        "message": "Connected to Persona Chat WebSocket Server",
                        "login_required": False,  # HTTP API로 로그인 필요
                    },
                }
            )
        )

        # 메시지 수신 루프
        async for message in websocket:
            await handle_message(websocket, message)

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_ip}")
    finally:
        connected_clients.discard(websocket)
        remove_client_sessions(websocket)
        logger.info(f"Total connected clients: {len(connected_clients)}")


def run_http_server():
    """외부 HTTP 서버 모듈 호출 래퍼"""
    if APP_CTX is None:
        raise RuntimeError("App context is not initialized")
    return run_http_server_external(APP_CTX)


async def main():
    """메인 함수"""
    logger.info("Starting Persona Chat WebSocket Server...")

    # DB 초기화
    global db_handler
    db_handler = DBHandler(DB_PATH)
    try:
        await db_handler.initialize()
        logger.info(f"SQLite initialized at: {DB_PATH}")
    except Exception:
        logger.exception("DB initialization failed; continuing without DB")
        db_handler = None  # 실패 시 None으로 설정

    # 컨텍스트 구성 (HTTP 서버 등 외부 모듈에 전달)
    global APP_CTX
    APP_CTX = AppContext(
        project_root=project_root,
        bind_host=BIND_HOST,
        login_required=False,  # HTTP API 로그인만 사용
        jwt_secret=JWT_SECRET,
        jwt_algorithm=JWT_ALGORITHM,
        access_ttl_seconds=ACCESS_TTL_SECONDS,
        refresh_ttl_seconds=REFRESH_TTL_SECONDS,
        login_username="",  # 레거시 제거됨
        login_rate_limit_max_attempts=int(os.getenv("APP_LOGIN_MAX_ATTEMPTS", "5")),
        login_rate_limit_window_seconds=int(os.getenv("APP_LOGIN_LOCK_MINUTES", "15")) * 60,
        token_expired_grace_seconds=int(os.getenv("APP_JWT_GRACE_MINUTES", "60")) * 60,
    )
    APP_CTX.sessions = sessions
    APP_CTX.websocket_to_session = websocket_to_session
    APP_CTX.connected_clients = connected_clients
    APP_CTX.login_attempts = login_attempts
    # 핸들러 주입
    APP_CTX.file_handler = file_handler
    APP_CTX.git_handler = git_handler
    APP_CTX.claude_handler = claude_handler
    APP_CTX.droid_handler = droid_handler
    APP_CTX.gemini_handler = gemini_handler
    APP_CTX.context_handler = context_handler
    APP_CTX.workspace_handler = workspace_handler
    APP_CTX.mode_handler = mode_handler
    APP_CTX.token_usage_handler = token_usage_handler
    APP_CTX.db_handler = db_handler

    # HTTP 서버를 별도 스레드에서 실행 (외부 모듈)
    http_thread = threading.Thread(
        target=run_http_server_external, kwargs={"ctx": APP_CTX}, daemon=True
    )
    http_thread.start()

    # WebSocket 서버 시작
    ws_port = int(os.getenv("WS_PORT", "8765"))
    # 현재 이벤트 루프를 AppContext에 보관(HTTP 스레드에서 DB 접근에 사용)
    if APP_CTX is not None:
        APP_CTX.loop = asyncio.get_running_loop()
    async with websockets.serve(websocket_handler, BIND_HOST, ws_port):
        logger.info(f"WebSocket server started on port {ws_port}")
        logger.info("Server is ready!")
        await asyncio.Future()  # 계속 실행


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")

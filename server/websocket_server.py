import asyncio
import json
import logging
import os
import secrets
from datetime import datetime, timedelta
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import TCPServer
import threading

import jwt
import websockets

from handlers.file_handler import FileHandler
from handlers.git_handler import GitHandler
from handlers.claude_handler import ClaudeCodeHandler
from handlers.droid_handler import DroidHandler
from handlers.gemini_handler import GeminiHandler
from handlers.context_handler import ContextHandler
from handlers.history_handler import HistoryHandler
from handlers.workspace_handler import WorkspaceHandler
from handlers.mode_handler import ModeHandler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 핸들러 초기화
# 프로젝트 루트 경로 (server/ 폴더의 상위 디렉토리)
project_root = Path(__file__).parent.parent
LOGIN_PASSWORD = os.getenv("APP_LOGIN_PASSWORD", "")
LOGIN_REQUIRED = bool(LOGIN_PASSWORD)
JWT_SECRET = os.getenv("APP_JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("APP_JWT_ALGORITHM", "HS256")
# 기존 APP_JWT_TTL 호환: 설정 시 access TTL로 사용
ACCESS_TTL_SECONDS = int(os.getenv("APP_ACCESS_TTL", os.getenv("APP_JWT_TTL", "604800")))
REFRESH_TTL_SECONDS = int(os.getenv("APP_REFRESH_TTL", "2592000"))  # 30일
BIND_HOST = os.getenv("APP_BIND_HOST", "127.0.0.1")
LOGIN_USERNAME = os.getenv("APP_LOGIN_USERNAME", "")
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = int(os.getenv("APP_LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_RATE_LIMIT_WINDOW = timedelta(minutes=int(os.getenv("APP_LOGIN_LOCK_MINUTES", "15")))
TOKEN_EXPIRED_GRACE = timedelta(minutes=int(os.getenv("APP_JWT_GRACE_MINUTES", "60")))

if LOGIN_REQUIRED and not JWT_SECRET:
    raise RuntimeError("APP_JWT_SECRET must be set when APP_LOGIN_PASSWORD is enabled")

file_handler = FileHandler()
git_handler = GitHandler()
claude_handler = ClaudeCodeHandler()
droid_handler = DroidHandler()
gemini_handler = GeminiHandler()
context_handler = ContextHandler()
history_handler = HistoryHandler(max_turns=30)  # 세션 지원에 맞춰 30턴만 유지
workspace_handler = WorkspaceHandler(str(project_root / "persona_data"))
mode_handler = ModeHandler(project_root=str(project_root))

# 연결된 클라이언트들
connected_clients = set()
login_attempts = {}
client_sessions: dict = {}
client_session_settings: dict = {}


def initialize_client_state(websocket):
    """클라이언트별 세션/설정 초기값"""
    client_sessions[websocket] = {}
    client_session_settings[websocket] = {"retention_enabled": False}


def clear_client_sessions(websocket):
    """특정 클라이언트의 세션 정보를 초기화"""
    if websocket in client_sessions:
        client_sessions[websocket].clear()
    else:
        client_sessions[websocket] = {}


def remove_client_sessions(websocket):
    """클라이언트 연결 종료 시 세션/설정 제거"""
    client_sessions.pop(websocket, None)
    client_session_settings.pop(websocket, None)


def is_session_retention_enabled(websocket):
    settings = client_session_settings.get(websocket, {})
    return settings.get("retention_enabled", False)


def _parse_story_markdown(md: str) -> list[dict]:
    """서사(.md)에서 히스토리 리스트로 변환

    포맷 가정:
    - "## n. 사용자" 섹션과 "## n. <이름>" 섹션이 번갈아 등장
    - 섹션 본문은 다음 '## ' 전까지의 텍스트(--- 구분선은 무시)
    반환: [{"role":"user"|"assistant","content":str}, ...]
    """
    try:
        lines = md.splitlines()
        items: list[dict] = []
        i = 0
        current_role = None
        buf: list[str] = []

        def flush():
            nonlocal buf, current_role
            if current_role and buf:
                # 구분선 제거
                text = "\n".join([ln for ln in buf if ln.strip() != '---']).strip()
                if text:
                    items.append({"role": current_role, "content": text})
            buf = []

        import re
        header_re = re.compile(r"^##\s+\d+\.\s*(.+?)\s*$")

        while i < len(lines):
            m = header_re.match(lines[i])
            if m:
                # 이전 섹션 flush
                flush()
                title = m.group(1)
                if "사용자" in title:
                    current_role = "user"
                else:
                    current_role = "assistant"
                buf = []
                i += 1
                continue
            else:
                if current_role:
                    buf.append(lines[i])
                i += 1

        flush()
        return items
    except Exception:
        # 파싱 실패 시 빈 배열
        return []

def _issue_token(ttl_seconds: int, typ: str):
    """JWT 생성 공통 함수"""
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
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, exp.isoformat() + "Z"


def issue_access_token():
    """Access 토큰 발급"""
    return _issue_token(ACCESS_TTL_SECONDS, "access")


def issue_refresh_token():
    """Refresh 토큰 발급"""
    return _issue_token(REFRESH_TTL_SECONDS, "refresh")


def verify_token(token, expected_type: str = "access"):
    """JWT 검증: (payload, error_code) 반환. expected_type: 'access' | 'refresh'"""
    if not JWT_SECRET:
        return None, "jwt_disabled"
    if not token:
        return None, "missing_token"
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        typ = payload.get("typ", "access")
        if expected_type and typ != expected_type:
            return None, "invalid_token_type"
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "token_expired"
    except jwt.InvalidTokenError:
        return None, "invalid_token"


async def send_auth_required(websocket, reason="missing_token"):
    await websocket.send(json.dumps({
        "action": "auth_required",
        "data": {"required": True, "reason": reason}
    }))


async def handle_login_action(websocket, data):
    """로그인/토큰 검증 처리"""
    if not LOGIN_REQUIRED:
        await websocket.send(json.dumps({
            "action": "login",
            "data": {"success": True, "token": None}
        }))
        return

    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    now = datetime.utcnow()
    attempts = login_attempts.setdefault(client_ip, [])
    attempts[:] = [(ts, success) for ts, success in attempts if now - ts < LOGIN_RATE_LIMIT_WINDOW]
    recent_failures = sum(1 for ts, success in attempts if not success)

    if recent_failures >= LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
        await websocket.send(json.dumps({
            "action": "login",
            "data": {"success": False, "error": "로그인 시도가 너무 많습니다. 잠시 후 다시 시도하세요.", "code": "rate_limited"}
        }))
        return

    def record_attempt(success: bool):
        attempts.append((datetime.utcnow(), success))

    token = data.get("token")
    username = data.get("username", "")
    password = data.get("password", "")

    if token:
        # Access 토큰으로 재인증/갱신 (웹소켓 keep-alive용)
        payload, error = verify_token(token, expected_type="access")
        if error:
            if error == "token_expired":
                try:
                    unverified = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
                    exp = datetime.fromtimestamp(unverified.get("exp"))
                    if datetime.utcnow() - exp < TOKEN_EXPIRED_GRACE:
                        new_token, expires_at = issue_access_token()
                        # refresh 토큰은 회전하지 않음(명시적 refresh에서 회전)
                        await websocket.send(json.dumps({
                            "action": "login",
                            "data": {"success": True, "token": new_token, "expires_at": expires_at, "renewed": True}
                        }))
                        record_attempt(True)
                        return
                except Exception:
                    pass

            await websocket.send(json.dumps({
                "action": "login",
                "data": {"success": False, "error": "토큰이 유효하지 않습니다.", "code": error}
            }))
            record_attempt(False)
            return

        new_token, expires_at = issue_access_token()
        await websocket.send(json.dumps({
            "action": "login",
            "data": {"success": True, "token": new_token, "expires_at": expires_at, "renewed": True}
        }))
        record_attempt(True)
        return

    # 사용자명 검사(설정된 경우)
    if LOGIN_USERNAME:
        if not username or username != LOGIN_USERNAME:
            await websocket.send(json.dumps({
                "action": "login",
                "data": {"success": False, "error": "아이디가 일치하지 않습니다.", "code": "invalid_username"}
            }))
            record_attempt(False)
            return

    if password and password == LOGIN_PASSWORD:
        issued, expires_at = issue_access_token()
        refresh, refresh_exp = issue_refresh_token()
        await websocket.send(json.dumps({
            "action": "login",
            "data": {"success": True, "token": issued, "expires_at": expires_at, "refresh_token": refresh, "refresh_expires_at": refresh_exp, "renewed": False}
        }))
        record_attempt(True)
        return

    await websocket.send(json.dumps({
        "action": "login",
        "data": {"success": False, "error": "비밀번호가 일치하지 않습니다.", "code": "invalid_password"}
    }))
    record_attempt(False)


async def handle_token_refresh_action(websocket, data):
    """리프레시 토큰으로 액세스 토큰 갱신/회전"""
    refresh_token = data.get("refresh_token")
    payload, error = verify_token(refresh_token, expected_type="refresh")
    if error:
        await websocket.send(json.dumps({
            "action": "token_refresh",
            "data": {"success": False, "error": error}
        }))
        return

    new_access, access_exp = issue_access_token()
    # 선택: refresh 토큰도 회전(보안 강화)
    rotate = bool(int(os.getenv("APP_REFRESH_ROTATE", "1")))
    if rotate:
        new_refresh, refresh_exp = issue_refresh_token()
    else:
        new_refresh, refresh_exp = refresh_token, None

    await websocket.send(json.dumps({
        "action": "token_refresh",
        "data": {
            "success": True,
            "token": new_access,
            "expires_at": access_exp,
            "refresh_token": new_refresh,
            "refresh_expires_at": refresh_exp
        }
    }))


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

        if LOGIN_REQUIRED:
            token = data.get("token")
            _, token_error = verify_token(token, expected_type="access")
            if token_error:
                await send_auth_required(websocket, token_error)
                return

        # 파일 목록 조회
        if action == "list_files":
            result = await file_handler.list_files()
            await websocket.send(json.dumps({"action": "list_files", "data": result}))

        # 파일 읽기
        elif action == "read_file":
            file_path = data.get("path")
            result = await file_handler.read_file(file_path)
            await websocket.send(json.dumps({"action": "read_file", "data": result}))

        # 파일 쓰기
        elif action == "write_file":
            file_path = data.get("path")
            content = data.get("content")
            result = await file_handler.write_file(file_path, content)
            await websocket.send(json.dumps({"action": "write_file", "data": result}))

        # Git 상태
        elif action == "git_status":
            result = await git_handler.status()
            await websocket.send(json.dumps({"action": "git_status", "data": result}))

        # Git 커밋/푸시
        elif action == "git_push":
            message = data.get("message", "Update from web app")
            result = await git_handler.commit_and_push(message)
            await websocket.send(json.dumps({"action": "git_push", "data": result}))

        # 컨텍스트 설정
        elif action == "set_context":
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

            context_handler.set_world(world)
            context_handler.set_situation(situation)
            context_handler.set_user_character(user_character)
            context_handler.set_narrator(narrator_enabled, narrator_mode, narrator_description, user_is_narrator)
            context_handler.set_adult_level(adult_level)
            context_handler.set_narrative_separation(narrative_separation)
            context_handler.set_ai_provider(ai_provider)
            context_handler.set_characters(characters)

            await websocket.send(json.dumps({
                "action": "set_context",
                "data": {"success": True, "context": context_handler.get_context()}
            }))

        # 컨텍스트 조회
        elif action == "get_context":
            await websocket.send(json.dumps({
                "action": "get_context",
                "data": {"success": True, "context": context_handler.get_context()}
            }))

        # 히스토리 초기화
        elif action == "clear_history":
            history_handler.clear()
            clear_client_sessions(websocket)
            await websocket.send(json.dumps({
                "action": "clear_history",
                "data": {"success": True, "message": "대화 히스토리가 초기화되었습니다"}
            }))

        # 히스토리 설정 조회
        elif action == "get_history_settings":
            await websocket.send(json.dumps({
                "action": "get_history_settings",
                "data": {
                    "success": True,
                    "max_turns": history_handler.max_turns
                }
            }))

        # 세션 리셋
        elif action == "reset_sessions":
            clear_client_sessions(websocket)
            await websocket.send(json.dumps({
                "action": "reset_sessions",
                "data": {"success": True, "message": "프로바이더 세션이 초기화되었습니다."}
            }))

        # 히스토리 길이 조정
        elif action == "set_history_limit":
            requested = data.get("max_turns")
            try:
                if requested is None:
                    new_limit = None
                else:
                    new_limit = int(requested)
                    if new_limit < 5 or new_limit > 1000:
                        raise ValueError(f"맥락 길이는 5~1000 사이여야 합니다 (입력값: {new_limit})")

                history_handler.set_max_turns(new_limit)
                await websocket.send(json.dumps({
                    "action": "set_history_limit",
                    "data": {"success": True, "max_turns": history_handler.max_turns}
                }))
            except (ValueError, TypeError) as exc:
                await websocket.send(json.dumps({
                    "action": "set_history_limit",
                    "data": {
                        "success": False,
                        "error": str(exc) if isinstance(exc, ValueError) else "올바른 숫자(5~1000) 또는 null을 입력하세요."
                    }
                }))

        # 세션 설정 조회
        elif action == "get_session_settings":
            settings = client_session_settings.get(websocket, {"retention_enabled": False})
            await websocket.send(json.dumps({
                "action": "get_session_settings",
                "data": {"success": True, **settings}
            }))

        # 세션 유지 토글
        elif action == "set_session_retention":
            enabled = bool(data.get("enabled"))
            client_session_settings.setdefault(websocket, {})["retention_enabled"] = enabled
            if not enabled:
                clear_client_sessions(websocket)
            await websocket.send(json.dumps({
                "action": "set_session_retention",
                "data": {"success": True, "retention_enabled": enabled}
            }))

        # 서사 가져오기 (마크다운)
        elif action == "get_narrative":
            narrative_md = history_handler.get_narrative_markdown()
            await websocket.send(json.dumps({
                "action": "get_narrative",
                "data": {"success": True, "markdown": narrative_md}
            }))

        # 워크스페이스 파일 목록
        elif action == "list_workspace_files":
            file_type = data.get("file_type")
            result = await workspace_handler.list_files(file_type)
            await websocket.send(json.dumps({"action": "list_workspace_files", "data": result}))

        # 워크스페이스 파일 읽기
        elif action == "load_workspace_file":
            file_type = data.get("file_type")
            filename = data.get("filename")
            result = await workspace_handler.read_file(file_type, filename)
            await websocket.send(json.dumps({"action": "load_workspace_file", "data": result}))

        # 워크스페이스 파일 저장
        elif action == "save_workspace_file":
            file_type = data.get("file_type")
            filename = data.get("filename")
            content = data.get("content")
            result = await workspace_handler.save_file(file_type, filename, content)
            await websocket.send(json.dumps({"action": "save_workspace_file", "data": result}))

        # 워크스페이스 파일 삭제
        elif action == "delete_workspace_file":
            file_type = data.get("file_type")
            filename = data.get("filename")
            result = await workspace_handler.delete_file(file_type, filename)
            await websocket.send(json.dumps({"action": "delete_workspace_file", "data": result}))

        # 워크스페이스 설정 로드
        elif action == "load_workspace_config":
            result = await workspace_handler.load_config()
            await websocket.send(json.dumps({"action": "load_workspace_config", "data": result}))

        # 워크스페이스 설정 저장
        elif action == "save_workspace_config":
            config = data.get("config", {})
            result = await workspace_handler.save_config(config)
            await websocket.send(json.dumps({"action": "save_workspace_config", "data": result}))

        # 프리셋 목록
        elif action == "list_presets":
            result = await workspace_handler.list_presets()
            await websocket.send(json.dumps({"action": "list_presets", "data": result}))

        # 프리셋 저장
        elif action == "save_preset":
            filename = data.get("filename")
            preset_data = data.get("preset")
            result = await workspace_handler.save_preset(filename, preset_data)
            await websocket.send(json.dumps({"action": "save_preset", "data": result}))

        # 프리셋 로드
        elif action == "load_preset":
            filename = data.get("filename")
            result = await workspace_handler.load_preset(filename)
            await websocket.send(json.dumps({"action": "load_preset", "data": result}))

        # 프리셋 삭제
        elif action == "delete_preset":
            filename = data.get("filename")
            result = await workspace_handler.delete_preset(filename)
            await websocket.send(json.dumps({"action": "delete_preset", "data": result}))

        # Git 상태 확인
        elif action == "git_check_status":
            result = await workspace_handler.git_check_status()
            await websocket.send(json.dumps({"action": "git_check_status", "data": result}))

        # Git 초기화
        elif action == "git_init":
            result = await workspace_handler.git_init()
            await websocket.send(json.dumps({"action": "git_init", "data": result}))

        # Git 동기화
        elif action == "git_sync":
            commit_message = data.get("message")
            result = await workspace_handler.git_sync(commit_message)
            await websocket.send(json.dumps({"action": "git_sync", "data": result}))

        # Git Pull
        elif action == "git_pull":
            result = await workspace_handler.git_pull()
            await websocket.send(json.dumps({"action": "git_pull", "data": result}))

        # 모드 확인
        elif action == "mode_check":
            result = await mode_handler.check_mode()
            await websocket.send(json.dumps({"action": "mode_check", "data": result}))

        # 챗봇 모드 전환
        elif action == "mode_switch_chatbot":
            result = await mode_handler.switch_to_chatbot()
            await websocket.send(json.dumps({"action": "mode_switch_chatbot", "data": result}))

        # 코딩 모드 전환
        elif action == "mode_switch_coding":
            result = await mode_handler.switch_to_coding()
            await websocket.send(json.dumps({"action": "mode_switch_coding", "data": result}))

        # 서사 목록
        elif action == "list_stories":
            result = await workspace_handler.list_stories()
            await websocket.send(json.dumps({"action": "list_stories", "data": result}))

        # 서사 저장 (append/use_server 옵션 지원)
        elif action == "save_story":
            filename = data.get("filename")
            content = data.get("content")
            use_server = bool(data.get("use_server", False))
            append = bool(data.get("append", False))
            if use_server:
                # 서버 원본 서사 사용
                content = history_handler.get_narrative_markdown()
            result = await workspace_handler.save_story(filename, content, append=append)
            await websocket.send(json.dumps({"action": "save_story", "data": result}))

        # 서사 로드
        elif action == "load_story":
            filename = data.get("filename")
            result = await workspace_handler.load_story(filename)
            await websocket.send(json.dumps({"action": "load_story", "data": result}))

        # 서사 삭제
        elif action == "delete_story":
            filename = data.get("filename")
            result = await workspace_handler.delete_story(filename)
            await websocket.send(json.dumps({"action": "delete_story", "data": result}))

        # 서사에서 이어하기 (히스토리 주입)
        elif action == "resume_from_story":
            filename = data.get("filename")
            turns_req = data.get("turns")
            summarize = bool(data.get("summarize", False))
            try:
                # 서사 로드
                loaded = await workspace_handler.load_story(filename)
                if not loaded.get("success"):
                    raise ValueError(loaded.get("error") or "서사를 불러오지 못했습니다")

                md = loaded.get("content", "")
                all_msgs = _parse_story_markdown(md)
                if not all_msgs:
                    raise ValueError("서사에서 대화를 파싱하지 못했습니다")

                # 불러올 턴 수 계산
                try:
                    if turns_req is None:
                        turns = history_handler.max_turns or 30
                    else:
                        turns = int(turns_req)
                except Exception:
                    turns = history_handler.max_turns or 30

                if turns <= 0:
                    turns = 10

                # 최근 N턴
                inject = all_msgs[-turns:]

                # 이전 구간 요약(옵션, 간단 요약)
                summary_text = None
                if summarize and len(all_msgs) > len(inject):
                    prev = all_msgs[:len(all_msgs) - len(inject)]
                    # 매우 단순한 요약: 각 메시지 첫 줄의 앞부분 1문장씩 최대 15줄
                    bullets = []
                    import re
                    for m in prev:
                        text = (m.get("content") or '').splitlines()[0]
                        # 문장 단위로 자르기
                        parts = re.split(r"[\.\!\?。？！]", text)
                        first = parts[0].strip() if parts else text.strip()
                        if first:
                            bullets.append(f"- {('사용자' if m['role']=='user' else 'AI')}: {first}")
                        if len(bullets) >= 15:
                            break
                    if bullets:
                        summary_text = "요약:\n" + "\n".join(bullets)

                # 히스토리 교체
                history_handler.clear()
                if summary_text:
                    history_handler.add_assistant_message(summary_text)
                for m in inject:
                    if m["role"] == "user":
                        history_handler.add_user_message(m["content"])
                    else:
                        history_handler.add_assistant_message(m["content"])

                # 대략 토큰 추정
                total_chars = sum(len(m["content"]) for m in inject) + (len(summary_text) if summary_text else 0)
                approx_tokens = int(total_chars / 4)

                await websocket.send(json.dumps({
                    "action": "resume_from_story",
                    "data": {
                        "success": True,
                        "injected_turns": len(inject),
                        "summarized": bool(summary_text),
                        "approx_tokens": approx_tokens
                    }
                }))
            except Exception as exc:
                await websocket.send(json.dumps({
                    "action": "resume_from_story",
                    "data": {"success": False, "error": str(exc)}
                }))

        # 히스토리 스냅샷 반환
        elif action == "get_history_snapshot":
            try:
                snap = history_handler.get_history()
                await websocket.send(json.dumps({
                    "action": "get_history_snapshot",
                    "data": {"success": True, "history": snap}
                }))
            except Exception as exc:
                await websocket.send(json.dumps({
                    "action": "get_history_snapshot",
                    "data": {"success": False, "error": str(exc)}
                }))

        # AI 채팅 (컨텍스트 + 히스토리 포함)
        elif action == "chat":
            prompt = data.get("prompt", "")
            # provider 파라미터 (없으면 컨텍스트의 기본값 사용)
            provider = data.get("provider", context_handler.get_context().get("ai_provider", "claude"))
            provider_sessions = client_sessions.setdefault(websocket, {})
            retention_enabled = is_session_retention_enabled(websocket)
            provider_session_id = provider_sessions.get(provider) if retention_enabled else None

            # 사용자 메시지를 히스토리에 추가
            history_handler.add_user_message(prompt)

            # 히스토리 텍스트 가져오기
            history_text = history_handler.get_history_text()

            # System prompt 생성 (히스토리 포함)
            system_prompt = context_handler.build_system_prompt(history_text)

            # 스트리밍 콜백: 각 JSON 라인을 클라이언트에 전송
            async def stream_callback(json_data):
                await websocket.send(json.dumps({
                    "action": "chat_stream",
                    "data": json_data
                }))

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
                    model=model
                )
            elif provider == "droid":
                # 혼선 방지를 위해 서버 기본 모델(DROID_MODEL)만 사용
                result = await droid_handler.send_message(
                    prompt,
                    system_prompt=system_prompt,
                    callback=stream_callback,
                    session_id=provider_session_id,
                    model=None
                )
            elif provider == "claude":
                result = await claude_handler.send_message(
                    prompt,
                    system_prompt=system_prompt,
                    callback=stream_callback,
                    session_id=provider_session_id,
                    model=model
                )
            else:
                result = {"success": False, "error": f"Unknown provider: {provider}"}

            # AI 응답을 히스토리에 추가
            if result.get("success") and result.get("message"):
                history_handler.add_assistant_message(result["message"])

            # 최종 결과 전송
            new_session_id = result.get("session_id")
            if retention_enabled and new_session_id:
                provider_sessions[provider] = new_session_id
            elif not retention_enabled:
                provider_sessions.pop(provider, None)

            await websocket.send(json.dumps({
                "action": "chat_complete",
                "data": {**result, "provider_used": provider}
            }))

        else:
            await websocket.send(json.dumps({
                "action": "error",
                "data": {"success": False, "error": f"Unknown action: {action}"}
            }))

    except json.JSONDecodeError:
        logger.exception("Invalid JSON received")
        await websocket.send(json.dumps({
            "action": "error",
            "data": {"success": False, "error": "Invalid JSON"}
        }))
    except Exception as e:
        logger.exception("Error handling message")
        await websocket.send(json.dumps({
            "action": "error",
            "data": {"success": False, "error": str(e)}
        }))


async def websocket_handler(websocket):
    """WebSocket 연결 핸들러"""
    connected_clients.add(websocket)
    initialize_client_state(websocket)
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    logger.info(f"Client connected: {client_ip} (Total: {len(connected_clients)})")

    try:
        # 환영 메시지
        await websocket.send(json.dumps({
            "action": "connected",
            "data": {
                "success": True,
                "message": "Connected to Persona Chat WebSocket Server",
                "login_required": LOGIN_REQUIRED
            }
        }))

        if LOGIN_REQUIRED:
            await send_auth_required(websocket)

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
    """HTTP 서버 실행 (정적 파일 서빙)"""
    import os
    # 현재 위치에서 상위 디렉토리의 web 폴더로 이동
    web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
    os.chdir(web_dir)

    app_config = {
        "ws_url": os.getenv("APP_PUBLIC_WS_URL", ""),
        "ws_port": int(os.getenv("WS_PORT", "8765")),
        "login_required": LOGIN_REQUIRED
    }

    class CustomHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            logger.info(f"HTTP: {format % args}")

        def do_GET(self):
            if self.path == "/app-config.json":
                payload = json.dumps(app_config).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            return super().do_GET()

    http_port = int(os.getenv("HTTP_PORT", "9000"))
    with TCPServer((BIND_HOST, http_port), CustomHandler) as httpd:
        logger.info(f"HTTP server started on port {http_port}")
        httpd.serve_forever()


async def main():
    """메인 함수"""
    logger.info("Starting Persona Chat WebSocket Server...")

    # HTTP 서버를 별도 스레드에서 실행
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    # WebSocket 서버 시작
    ws_port = int(os.getenv("WS_PORT", "8765"))
    async with websockets.serve(websocket_handler, BIND_HOST, ws_port):
        logger.info(f"WebSocket server started on port {ws_port}")
        logger.info("Server is ready!")
        await asyncio.Future()  # 계속 실행


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")

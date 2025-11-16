"""WebSocket 서버 통합 테스트

실제 WebSocket 서버를 띄우고 클라이언트로 연결하여
전체 시스템의 통합 동작을 테스트합니다.
"""

import json
import os

import pytest
import pytest_asyncio
import websockets

# 테스트용 환경변수 설정 (서버 import 전에 설정)
os.environ["APP_LOGIN_PASSWORD"] = ""  # 로그인 비활성화
os.environ["APP_JWT_SECRET"] = "ws_test_secret"  # pragma: allowlist secret
os.environ["DB_PATH"] = ":memory:"  # 인메모리 DB 사용


def _with_token(token: str, payload: dict) -> str:
    msg = dict(payload)
    msg["token"] = token
    return json.dumps(msg)


@pytest_asyncio.fixture
async def ws_server(tmp_path):
    """WebSocket 서버 fixture"""
    # 임시 데이터 디렉토리
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    persona_dir = tmp_path / "persona_data"
    persona_dir.mkdir()

    os.environ["DB_PATH"] = str(data_dir / "test.db")

    # 서버 모듈을 동적으로 import (환경변수 설정 후)
    import importlib

    from server import websocket_server as _ws_mod

    websocket_server = importlib.reload(_ws_mod)

    # 프로젝트 루트 경로 오버라이드
    websocket_server.project_root = tmp_path
    websocket_server.workspace_handler.base_path = persona_dir

    # DB 초기화
    websocket_server.db_handler = websocket_server.DBHandler(os.environ["DB_PATH"])
    await websocket_server.db_handler.initialize()

    # AppContext 초기화
    from server.core.app_context import AppContext

    websocket_server.APP_CTX = AppContext(
        project_root=tmp_path,
        bind_host="127.0.0.1",
        login_required=False,
        jwt_secret=os.environ["APP_JWT_SECRET"],  # pragma: allowlist secret
        jwt_algorithm="HS256",
        access_ttl_seconds=3600,
        refresh_ttl_seconds=86400,
        login_username="",
        login_rate_limit_max_attempts=5,
        login_rate_limit_window_seconds=900,
        token_expired_grace_seconds=3600,
    )
    # 핸들러 주입
    websocket_server.APP_CTX.db_handler = websocket_server.db_handler
    websocket_server.APP_CTX.workspace_handler = websocket_server.workspace_handler
    websocket_server.APP_CTX.context_handler = websocket_server.context_handler
    websocket_server.APP_CTX.file_handler = websocket_server.file_handler
    websocket_server.APP_CTX.git_handler = websocket_server.git_handler
    websocket_server.APP_CTX.mode_handler = websocket_server.mode_handler
    websocket_server.APP_CTX.token_usage_handler = websocket_server.token_usage_handler
    websocket_server.APP_CTX.claude_handler = websocket_server.claude_handler
    websocket_server.APP_CTX.droid_handler = websocket_server.droid_handler
    websocket_server.APP_CTX.gemini_handler = websocket_server.gemini_handler

    # 테스트용 사용자/토큰 생성
    test_user_id = await websocket_server.db_handler.create_user(
        "ws_tester", "ws_tester@example.com", "hash"
    )
    await websocket_server.db_handler.approve_user(test_user_id, test_user_id)
    token, _ = websocket_server.issue_access_token(
        session_key="user:ws_tester", user_id=test_user_id
    )

    # 서버 시작
    port = 18765  # 테스트용 포트
    server = await websockets.serve(websocket_server.websocket_handler, "127.0.0.1", port)

    yield {"url": f"ws://127.0.0.1:{port}", "token": token, "ws_mod": websocket_server}

    # 서버 종료
    server.close()
    await server.wait_closed()
    if websocket_server.db_handler:
        await websocket_server.db_handler.close()


@pytest.mark.asyncio
async def test_server_connection(ws_server):
    """서버 연결 및 환영 메시지 테스트"""
    async with websockets.connect(ws_server["url"]) as websocket:
        # 환영 메시지 수신
        response = await websocket.recv()
        data = json.loads(response)

        assert data["action"] == "connected"
        assert data["data"]["success"] is True
        assert "Connected to Persona Chat" in data["data"]["message"]


@pytest.mark.asyncio
async def test_context_get_set(ws_server):
    """Context 설정 테스트"""
    async with websockets.connect(ws_server["url"]) as websocket:
        # 환영 메시지 스킵
        await websocket.recv()

        # Context 설정
        await websocket.send(
            _with_token(
                ws_server["token"],
                {
                    "action": "set_context",
                    "data": {
                        "world": "테스트 세계",
                        "situation": "테스트 상황",
                        "characters": [
                            {"name": "테스트2", "description": "설명2"},
                        ],
                    },
                },
            )
        )

        response = await websocket.recv()
        data = json.loads(response)
        # 기본적으로 성공 응답을 받으면 OK
        assert data["data"]["success"] is True


@pytest.mark.asyncio
async def test_history_management(ws_server):
    """History 관리 테스트 (clear_history, get_history_settings)"""
    async with websockets.connect(ws_server["url"]) as websocket:
        await websocket.recv()  # 환영 메시지 스킵

        # History 설정 조회
        await websocket.send(_with_token(ws_server["token"], {"action": "get_history_settings"}))
        response = await websocket.recv()
        data = json.loads(response)
        assert "max_turns" in data["data"]

        # History limit 설정
        await websocket.send(
            _with_token(
                ws_server["token"],
                {"action": "set_history_limit", "data": {"limit": 20}},
            )
        )
        response = await websocket.recv()
        data = json.loads(response)
        assert data["data"]["success"] is True

        # History 초기화
        await websocket.send(_with_token(ws_server["token"], {"action": "clear_history"}))
        response = await websocket.recv()
        data = json.loads(response)
        assert data["data"]["success"] is True
        # (no-op) ensure room_save completed — DB checks removed


@pytest.mark.asyncio
async def test_room_management(ws_server):
    """채팅방 생성/로드/삭제 테스트"""
    async with websockets.connect(ws_server["url"]) as websocket:
        await websocket.recv()  # 환영 메시지 스킵

        # 방 목록 조회 (초기 상태)
        await websocket.send(_with_token(ws_server["token"], {"action": "room_list"}))
        response = await websocket.recv()
        data = json.loads(response)
        assert data["data"]["success"] is True
        initial_count = len(data["data"]["rooms"])

        # 방 저장
        await websocket.send(
            _with_token(
                ws_server["token"],
                {
                    "action": "room_save",
                    "data": {"room_id": "test-room-1", "room_name": "테스트 방"},
                },
            )
        )
        response = await websocket.recv()
        data = json.loads(response)
        assert data["data"]["success"] is True

        # 방 목록 재조회
        await websocket.send(_with_token(ws_server["token"], {"action": "room_list"}))
        response = await websocket.recv()
        data = json.loads(response)
        assert len(data["data"]["rooms"]) == initial_count + 1

        # 방 로드
        await websocket.send(
            _with_token(ws_server["token"], {"action": "room_load", "room_id": "test-room-1"})
        )
        response = await websocket.recv()
        data = json.loads(response)
        assert data["data"]["success"] is True


@pytest.mark.asyncio
async def test_room_load_includes_history(ws_server):
    """room_load 응답에 DB에 저장된 메시지가 포함되어 있는지 확인합니다."""
    async with websockets.connect(ws_server["url"]) as websocket:
        await websocket.recv()  # 환영 메시지 스킵

        # 방 저장
        await websocket.send(
            _with_token(
                ws_server["token"],
                {
                    "action": "room_save",
                    "data": {"room_id": "test-room-history", "room_name": "Test"},
                },
            )
        )
        await websocket.recv()

        # DB에 메시지 저장 (직접 호출)
        # 테스트 환경에서 DB 핸들러는 ws_server fixture의 websocket_server에 보관되어 있음
        # 사용자 id 조회 (fixture로 전달된 모듈을 사용)
        ws_mod = ws_server.get("ws_mod")
        assert ws_mod is not None
        user = await ws_mod.db_handler.get_user_by_username("ws_tester")
        assert user is not None
        user_id = user["user_id"]
        # 방이 DB에 확실히 존재하도록 upsert 후 메시지 저장 (사용자/AI)
        await ws_mod.db_handler.upsert_room("test-room-history", user_id, "Test", "{}")
        await ws_mod.db_handler.save_message(
            "test-room-history", "user", "Hello from user", user_id
        )
        await ws_mod.db_handler.save_message(
            "test-room-history", "assistant", "Hello from AI", user_id
        )

        # DB에 메시지가 들어갔는지 확인
        msgs = await ws_mod.db_handler.list_messages("test-room-history", user_id)
        print("DB messages:", msgs)
        assert len(msgs) >= 2

        # room_load 호출
        await websocket.send(
            _with_token(ws_server["token"], {"action": "room_load", "room_id": "test-room-history"})
        )
        response = await websocket.recv()
        data = json.loads(response)
        assert data["data"]["success"] is True
        room = data["data"].get("room") or {}
        print("room response:", room)
        assert isinstance(room.get("history"), list)
        # 저장한 메시지들이 history에 포함된 것 확인
        contents = [m.get("content") for m in room.get("history", [])]
        assert "Hello from user" in contents
        assert "Hello from AI" in contents

        # 방 삭제 (테스트에서 생성한 방만 삭제)
        try:
            await websocket.send(
                _with_token(
                    ws_server["token"], {"action": "room_delete", "room_id": "test-room-history"}
                )
            )
            await websocket.recv()
        except Exception:
            pass
    # end of test: deletion response already handled above (if present)


@pytest.mark.asyncio
async def test_room_session_retention_saved_and_restored(ws_server):
    """room_save에 포함된 session_retention 설정이 room_load로 복원되는지 확인합니다."""
    async with websockets.connect(ws_server["url"]) as websocket:
        await websocket.recv()  # 환영 메시지 스킵

        # 방 저장: 세션 유지 false
        await websocket.send(
            _with_token(
                ws_server["token"],
                {
                    "action": "room_save",
                    "data": {
                        "room_id": "test-room-session",
                        "config": {"context": {"session_retention": False}},
                    },
                },
            )
        )
        response = await websocket.recv()
        data = json.loads(response)
        assert data["data"]["success"] is True

        # room_load 호출
        await websocket.send(
            _with_token(
                ws_server["token"], {"action": "room_load", "room_id": "test-room-session"}
            ),
        )
        response = await websocket.recv()
        print("raw room_load response for session retention:", response)
        data = json.loads(response)
        print("parsed room_load response for session retention:", data)
        assert data["data"]["success"] is True
        room = data["data"].get("room") or {}
        ctx = room.get("context") or {}
        assert "session_retention" in ctx
        assert ctx["session_retention"] is False


@pytest.mark.asyncio
async def test_session_settings(ws_server):
    """세션 설정 테스트"""
    async with websockets.connect(ws_server["url"]) as websocket:
        await websocket.recv()  # 환영 메시지 스킵

        # 세션 설정 조회
        await websocket.send(_with_token(ws_server["token"], {"action": "get_session_settings"}))
        response = await websocket.recv()
        data = json.loads(response)
        assert data["data"]["success"] is True
        assert "adult_consent" in data["data"]

        # 세션 retention 설정
        await websocket.send(
            _with_token(
                ws_server["token"],
                {"action": "set_session_retention", "data": {"enabled": True}},
            )
        )
        response = await websocket.recv()
        data = json.loads(response)
        assert data["data"]["success"] is True


@pytest.mark.asyncio
async def test_unknown_action(ws_server):
    """알 수 없는 액션 처리 테스트"""
    async with websockets.connect(ws_server["url"]) as websocket:
        await websocket.recv()  # 환영 메시지 스킵

        # 존재하지 않는 액션
        await websocket.send(_with_token(ws_server["token"], {"action": "nonexistent_action"}))
        response = await websocket.recv()
        data = json.loads(response)
        assert data["action"] == "error"
        assert "Unknown action" in data["data"]["error"]


@pytest.mark.asyncio
async def test_invalid_json(ws_server):
    """잘못된 JSON 처리 테스트"""
    async with websockets.connect(ws_server["url"]) as websocket:
        await websocket.recv()  # 환영 메시지 스킵

        # 잘못된 JSON 전송
        await websocket.send("invalid json{{{")
        response = await websocket.recv()
        data = json.loads(response)
        assert data["action"] == "error"
        assert "Invalid JSON" in data["data"]["error"]


@pytest.mark.asyncio
@pytest.mark.skip(reason="Chat 액션은 실제 AI 호출이 필요하므로 통합 테스트에서 제외")
async def test_chat_action_mock(ws_server):
    """Chat 액션 테스트 (실제 AI 호출 필요)"""
    pass


@pytest.mark.asyncio
async def test_multiple_clients(ws_server):
    """다중 클라이언트 동시 연결 테스트"""
    clients = []

    # 3개의 클라이언트 동시 연결
    for _ in range(3):
        client = await websockets.connect(ws_server["url"])
        response = await client.recv()  # 환영 메시지 수신
        data = json.loads(response)
        assert data["action"] == "connected"
        clients.append(client)

    # 각 클라이언트에서 간단한 액션 테스트 (room_list)
    for client in clients:
        await client.send(_with_token(ws_server["token"], {"action": "room_list"}))
        response = await client.recv()
        data = json.loads(response)
        assert data["data"]["success"] is True

    # 모든 클라이언트 종료
    for client in clients:
        await client.close()

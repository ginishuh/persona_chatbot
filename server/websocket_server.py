import asyncio
import json
import logging
import websockets
from pathlib import Path
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import threading

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

file_handler = FileHandler()
git_handler = GitHandler()
claude_handler = ClaudeCodeHandler()
droid_handler = DroidHandler()
gemini_handler = GeminiHandler()
context_handler = ContextHandler()
history_handler = HistoryHandler(max_turns=None)  # 무제한 히스토리
workspace_handler = WorkspaceHandler(str(project_root / "persona_data"))
mode_handler = ModeHandler(project_root=str(project_root))

# 연결된 클라이언트들
connected_clients = set()


async def handle_message(websocket, message):
    """메시지 처리"""
    try:
        data = json.loads(message)
        action = data.get("action")

        logger.info(f"Received action: {action}")

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
            await websocket.send(json.dumps({
                "action": "clear_history",
                "data": {"success": True, "message": "대화 히스토리가 초기화되었습니다"}
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

        # 서사 저장
        elif action == "save_story":
            filename = data.get("filename")
            content = data.get("content")
            result = await workspace_handler.save_story(filename, content)
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

        # AI 채팅 (컨텍스트 + 히스토리 포함)
        elif action == "chat":
            prompt = data.get("prompt", "")
            # provider 파라미터 (없으면 컨텍스트의 기본값 사용)
            provider = data.get("provider", context_handler.get_context().get("ai_provider", "claude"))

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

            result = await handler.send_message(
                prompt,
                system_prompt=system_prompt,
                callback=stream_callback
            )

            # AI 응답을 히스토리에 추가
            if result.get("success") and result.get("message"):
                history_handler.add_assistant_message(result["message"])

            # 최종 결과 전송
            await websocket.send(json.dumps({
                "action": "chat_complete",
                "data": result
            }))

        else:
            await websocket.send(json.dumps({
                "action": "error",
                "data": {"success": False, "error": f"Unknown action: {action}"}
            }))

    except json.JSONDecodeError:
        logger.error("Invalid JSON received")
        await websocket.send(json.dumps({
            "action": "error",
            "data": {"success": False, "error": "Invalid JSON"}
        }))
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await websocket.send(json.dumps({
            "action": "error",
            "data": {"success": False, "error": str(e)}
        }))


async def websocket_handler(websocket):
    """WebSocket 연결 핸들러"""
    connected_clients.add(websocket)
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    logger.info(f"Client connected: {client_ip} (Total: {len(connected_clients)})")

    try:
        # 환영 메시지
        await websocket.send(json.dumps({
            "action": "connected",
            "data": {"success": True, "message": "Connected to Persona Chat WebSocket Server"}
        }))

        # 메시지 수신 루프
        async for message in websocket:
            await handle_message(websocket, message)

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_ip}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Total connected clients: {len(connected_clients)}")


def run_http_server():
    """HTTP 서버 실행 (정적 파일 서빙)"""
    import os
    # 현재 위치에서 상위 디렉토리의 web 폴더로 이동
    web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
    os.chdir(web_dir)

    class CustomHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            logger.info(f"HTTP: {format % args}")

    with TCPServer(("0.0.0.0", 9000), CustomHandler) as httpd:
        logger.info("HTTP server started on port 9000")
        httpd.serve_forever()


async def main():
    """메인 함수"""
    logger.info("Starting Persona Chat WebSocket Server...")

    # HTTP 서버를 별도 스레드에서 실행
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    # WebSocket 서버 시작
    async with websockets.serve(websocket_handler, "0.0.0.0", 8765):
        logger.info("WebSocket server started on port 8765")
        logger.info("Server is ready!")
        await asyncio.Future()  # 계속 실행


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")

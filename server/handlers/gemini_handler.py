import asyncio
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class GeminiHandler:
    """Gemini CLI 프로세스 관리 및 통신"""

    def __init__(self, gemini_path=None):
        # 환경 변수 또는 기본값 사용
        self.gemini_path = gemini_path or os.getenv("GEMINI_PATH", "gemini")
        self.process = None
        self.session_id = None
        # 챗봇 전용 작업 디렉토리
        self.chatbot_workspace = Path(__file__).parent.parent.parent / "chatbot_workspace"
        self.chatbot_workspace.mkdir(exist_ok=True)

    async def start(self, system_prompt=None):
        """Gemini 프로세스 시작"""
        if self.process is not None:
            logger.warning("Gemini process already running")
            return

        try:
            args = [
                self.gemini_path,
                "--output-format", "stream-json"
            ]

            # System prompt와 프롬프트를 stdin으로 전달

            self.process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.chatbot_workspace)  # 챗봇 전용 디렉토리에서 실행
            )
            logger.info(f"Gemini process started (cwd: {self.chatbot_workspace})")
        except Exception as e:
            logger.error(f"Failed to start Gemini: {e}")
            raise

    async def stop(self):
        """Gemini 프로세스 종료"""
        if self.process is None:
            return

        try:
            self.process.terminate()
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
            logger.info("Gemini process stopped")
        except asyncio.TimeoutError:
            self.process.kill()
            await self.process.wait()
            logger.warning("Gemini process killed (timeout)")
        finally:
            self.process = None
            self.session_id = None

    async def send_message(self, prompt, system_prompt=None, callback=None):
        """
        Gemini에 메시지 전송 및 스트리밍 응답 수신

        Args:
            prompt: 전송할 프롬프트
            system_prompt: 시스템 프롬프트 (캐릭터 설정 등) - 프롬프트에 포함됨
            callback: 각 JSON 라인을 받을 때 호출될 async 콜백 함수

        Returns:
            최종 결과 딕셔너리
        """
        if self.process is None:
            await self.start()

        try:
            # System prompt를 프롬프트 앞에 추가
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n=== 사용자 메시지 ===\n{prompt}"

            # 프롬프트 전송
            prompt_with_newline = full_prompt + "\n"
            self.process.stdin.write(prompt_with_newline.encode('utf-8'))
            await self.process.stdin.drain()
            self.process.stdin.close()  # stdin 닫기 (중요!)

            # 응답 수신 (스트리밍)
            assistant_message = ""

            # stderr를 비동기로 읽어서 버퍼 막힘 방지
            async def read_stderr():
                while True:
                    line = await self.process.stderr.readline()
                    if not line:
                        break
                    logger.debug(f"Gemini stderr: {line.decode('utf-8').strip()}")

            stderr_task = asyncio.create_task(read_stderr())

            try:
                # stdout 읽기 (타임아웃 추가)
                while True:
                    try:
                        line = await asyncio.wait_for(
                            self.process.stdout.readline(),
                            timeout=120.0  # 2분 타임아웃
                        )

                        if not line:
                            break

                        try:
                            data = json.loads(line.decode('utf-8').strip())

                            # 세션 ID 저장 (있는 경우)
                            if 'session_id' in data:
                                self.session_id = data.get('session_id')
                                logger.info(f"Gemini Session ID: {self.session_id}")

                            # 콜백 호출 (Claude 형식으로 변환)
                            if callback:
                                # Gemini 형식: {"type":"message","role":"assistant","content":"...","delta":true}
                                if data.get('type') == 'message' and data.get('role') == 'assistant':
                                    content = data.get('content', '')
                                    if content and data.get('delta'):
                                        # Claude 형식으로 변환: content_block_delta
                                        claude_format = {
                                            "type": "content_block_delta",
                                            "delta": {"text": content}
                                        }
                                        await callback(claude_format)
                                        assistant_message += content

                        except json.JSONDecodeError as e:
                            # JSON이 아닌 일반 텍스트일 수 있음
                            line_text = line.decode('utf-8').strip()
                            if line_text and callback:
                                claude_format = {
                                    "type": "content_block_delta",
                                    "delta": {"text": line_text}
                                }
                                await callback(claude_format)
                                assistant_message += line_text
                            logger.debug(f"Non-JSON output: {line_text}")
                            continue

                    except asyncio.TimeoutError:
                        logger.error("Timeout waiting for Gemini response")
                        break

            finally:
                stderr_task.cancel()

            # 프로세스 종료 대기
            await self.process.wait()
            self.process = None

            # Gemini는 토큰 정보를 제공하지 않으므로 None으로 반환
            return {
                "success": True,
                "message": assistant_message,
                "token_info": None
            }

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await self.stop()
            return {
                "success": False,
                "error": str(e)
            }

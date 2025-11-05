import asyncio
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ClaudeCodeHandler:
    """Claude Code 프로세스 관리 및 통신"""

    def __init__(self, claude_path="/home/ginis/.nvm/versions/node/v22.17.1/bin/claude"):
        self.claude_path = claude_path
        self.process = None
        self.session_id = None

    async def start(self, system_prompt=None):
        """Claude Code 프로세스 시작"""
        if self.process is not None:
            logger.warning("Claude Code process already running")
            return

        try:
            args = [
                self.claude_path,
                "--print",
                "--verbose",
                "--output-format", "stream-json"
            ]

            # System prompt 추가
            if system_prompt:
                args.extend(["--system-prompt", system_prompt])

            self.process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info("Claude Code process started")
        except Exception as e:
            logger.error(f"Failed to start Claude Code: {e}")
            raise

    async def stop(self):
        """Claude Code 프로세스 종료"""
        if self.process is None:
            return

        try:
            self.process.terminate()
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
            logger.info("Claude Code process stopped")
        except asyncio.TimeoutError:
            self.process.kill()
            await self.process.wait()
            logger.warning("Claude Code process killed (timeout)")
        finally:
            self.process = None
            self.session_id = None

    async def send_message(self, prompt, system_prompt=None, callback=None):
        """
        Claude Code에 메시지 전송 및 스트리밍 응답 수신

        Args:
            prompt: 전송할 프롬프트
            system_prompt: 시스템 프롬프트 (캐릭터 설정 등)
            callback: 각 JSON 라인을 받을 때 호출될 async 콜백 함수

        Returns:
            최종 결과 딕셔너리
        """
        if self.process is None:
            await self.start(system_prompt)

        try:
            # 프롬프트 전송
            prompt_with_newline = prompt + "\n"
            self.process.stdin.write(prompt_with_newline.encode('utf-8'))
            await self.process.stdin.drain()
            self.process.stdin.close()  # stdin 닫기 (중요!)

            # 응답 수신 (스트리밍)
            result = None
            assistant_message = ""

            # stderr를 비동기로 읽어서 버퍼 막힘 방지
            async def read_stderr():
                while True:
                    line = await self.process.stderr.readline()
                    if not line:
                        break
                    logger.debug(f"Claude stderr: {line.decode('utf-8').strip()}")

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

                            # 세션 ID 저장
                            if 'session_id' in data and self.session_id is None:
                                self.session_id = data['session_id']
                                logger.info(f"Session ID: {self.session_id}")

                            # 콜백 호출
                            if callback:
                                await callback(data)

                            # assistant 메시지 수집
                            if data.get('type') == 'assistant':
                                message = data.get('message', {})
                                content = message.get('content', [])
                                for item in content:
                                    if item.get('type') == 'text':
                                        assistant_message = item.get('text', '')

                            # 최종 결과
                            if data.get('type') == 'result':
                                result = data
                                break

                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON: {e}")
                            continue

                    except asyncio.TimeoutError:
                        logger.error("Timeout waiting for Claude response")
                        break

            finally:
                stderr_task.cancel()

            # 프로세스 종료 대기
            await self.process.wait()
            self.process = None

            return {
                "success": True,
                "message": assistant_message,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await self.stop()
            return {
                "success": False,
                "error": str(e)
            }

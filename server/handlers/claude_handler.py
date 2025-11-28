import asyncio
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class ClaudeCodeHandler:
    """Claude Code 프로세스 관리 및 통신"""

    def __init__(self, claude_path=None):
        # 환경 변수 또는 기본값 사용
        self.claude_path = claude_path or os.getenv("CLAUDE_PATH", "claude")
        self.process = None
        # 챗봇 전용 작업 디렉토리 (chatbot_workspace/CLAUDE.md 읽기 위해)
        self.chatbot_workspace = Path(__file__).parent.parent.parent / "chatbot_workspace"
        self.chatbot_workspace.mkdir(exist_ok=True)
        # 세션별 누적 토큰 추적 (중복 누적 방지)
        self.session_cumulative_tokens = {}

    async def start(self, system_prompt=None, resume_session_id=None, model: str | None = None):
        """Claude Code 프로세스 시작"""
        if self.process is not None:
            logger.warning("Claude Code process already running")
            return

        try:
            args = [
                self.claude_path,
                "--print",
                "--verbose",
                "--output-format",
                "stream-json",
                "--setting-sources",
                "user,local",  # chatbot_workspace/CLAUDE.md만 읽기 (project 제외)
            ]

            if resume_session_id:
                args.extend(["--resume", str(resume_session_id)])
            if model:
                args.extend(["--model", str(model)])

            # System prompt 추가
            if system_prompt:
                args.extend(["--system-prompt", system_prompt])

            self.process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(
                    self.chatbot_workspace
                ),  # 챗봇 전용 디렉토리에서 실행 (CLAUDE.md 읽기 위해)
            )
            logger.info(f"Claude Code process started (cwd: {self.chatbot_workspace})")
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
        except TimeoutError:
            self.process.kill()
            await self.process.wait()
            logger.warning("Claude Code process killed (timeout)")
        finally:
            self.process = None

    async def send_message(
        self, prompt, system_prompt=None, callback=None, session_id=None, model: str | None = None
    ):
        """
        Claude Code에 메시지 전송 및 스트리밍 응답 수신

        Args:
            prompt: 전송할 프롬프트
            system_prompt: 시스템 프롬프트 (캐릭터 설정 등)
            callback: 각 JSON 라인을 받을 때 호출될 async 콜백 함수
            session_id: 이어서 사용할 세션 ID (있다면 --resume으로 전달)

        Returns:
            최종 결과 딕셔너리
        """
        if self.process is None:
            await self.start(system_prompt, resume_session_id=session_id, model=model)

        try:
            # 프롬프트 전송
            prompt_with_newline = prompt + "\n"
            self.process.stdin.write(prompt_with_newline.encode("utf-8"))
            await self.process.stdin.drain()
            self.process.stdin.close()  # stdin 닫기 (중요!)

            # 응답 수신 (스트리밍)
            result = None
            assistant_message = ""
            current_session_id = session_id

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
                            self.process.stdout.readline(), timeout=120.0  # 2분 타임아웃
                        )

                        if not line:
                            break

                        try:
                            data = json.loads(line.decode("utf-8").strip())

                            # 세션 ID 저장
                            if "session_id" in data:
                                current_session_id = data["session_id"]
                                logger.info(f"Session ID: {current_session_id}")

                            # 콜백 호출
                            if callback:
                                await callback(data)

                            # assistant 메시지 수집
                            if data.get("type") == "assistant":
                                message = data.get("message", {})
                                content = message.get("content", [])
                                for item in content:
                                    if item.get("type") == "text":
                                        assistant_message = item.get("text", "")

                            # 최종 결과
                            if data.get("type") == "result":
                                result = data
                                break

                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON: {e}")
                            continue

                    except TimeoutError:
                        logger.error("Timeout waiting for Claude response")
                        break

            finally:
                stderr_task.cancel()

            # 프로세스 종료 대기
            await self.process.wait()
            self.process = None

            # 토큰 사용량 계산 (세션 모드에서 중복 누적 방지)
            token_info = None
            if result and result.get("usage"):
                usage = result.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                cache_read = usage.get("cache_read_input_tokens", 0)
                cache_creation = usage.get("cache_creation_input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)

                total_input = input_tokens + cache_read + cache_creation
                total_tokens = total_input + output_tokens

                # 세션 모드: Claude CLI가 누적값을 반환하므로 delta만 계산
                if current_session_id:
                    prev_total = self.session_cumulative_tokens.get(current_session_id, 0)
                    delta_tokens = total_tokens - prev_total

                    # 델타가 음수면 (새 세션이거나 리셋) 전체값 사용
                    if delta_tokens < 0:
                        delta_tokens = total_tokens

                    # 현재 누적값 저장
                    self.session_cumulative_tokens[current_session_id] = total_tokens

                    # 델타값만 반환 (token_usage_handler에서 누적)
                    token_info = {
                        "input_tokens": delta_tokens,  # 간단화: 전체 델타만 반환
                        "cache_read_tokens": 0,
                        "cache_creation_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": delta_tokens,
                        "context_window": 200000,
                        "tokens_remaining": 200000 - total_tokens,
                    }
                    logger.info(
                        f"Session {current_session_id[:8]}... - "
                        f"Cumulative: {total_tokens}, Delta: {delta_tokens}"
                    )
                else:
                    # 비세션 모드: 그대로 반환
                    token_info = {
                        "input_tokens": input_tokens,
                        "cache_read_tokens": cache_read,
                        "cache_creation_tokens": cache_creation,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens,
                        "context_window": 200000,
                        "tokens_remaining": 200000 - total_tokens,
                    }

            return {
                "success": True,
                "message": assistant_message,
                "result": result,
                "token_info": token_info,
                "session_id": current_session_id,
            }

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await self.stop()
            error_msg = str(e).lower()
            session_error = any(
                kw in error_msg for kw in ("session", "expired", "invalid", "resume")
            )
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "session_expired": session_error,
            }

    def clear_session_tokens(self, session_id: str | None = None):
        """세션별 누적 토큰 초기화

        Args:
            session_id: 초기화할 세션 ID (None이면 전체 초기화)
        """
        if session_id:
            if session_id in self.session_cumulative_tokens:
                del self.session_cumulative_tokens[session_id]
                logger.info(f"Cleared cumulative tokens for session {session_id[:8]}...")
        else:
            self.session_cumulative_tokens.clear()
            logger.info("Cleared all cumulative tokens")

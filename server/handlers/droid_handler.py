import asyncio
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class DroidHandler:
    """Droid (Z.ai) CLI 프로세스 관리 및 통신

    - 환경 변수로 모델/타임아웃/자율성 레벨을 설정 가능하게 함.
    - 응답이 오지 않는 경우를 명확히 실패로 반환하여 상위 레벨에서 폴백 처리 가능.
    """

    def __init__(self, droid_path=None):
        # 환경 변수 또는 기본값 사용
        self.droid_path = droid_path or os.getenv("DROID_PATH", "droid")
        self.primary_model = os.getenv("DROID_MODEL", "custom:glm-4.6")
        # 콤마로 구분된 폴백 모델 목록 (예: "glm-4.6,glm-4")
        self.fallback_models = [
            m.strip() for m in os.getenv("DROID_FALLBACK_MODELS", "").split(",") if m.strip()
        ]
        self.auto_level = os.getenv("DROID_AUTO", "low")
        # 컨테이너 환경(비상호작용)에서는 권한 확인이 block되므로 옵션으로 건너뛰기 허용
        self.skip_permissions_unsafe = os.getenv(
            "DROID_SKIP_PERMISSIONS_UNSAFE", "false"
        ).lower() in ("1", "true", "yes", "on")
        # 실행 방식: exec | direct | auto
        # Factory 공식 권장은 headless `droid exec` 경로
        self.exec_style = os.getenv("DROID_EXEC_STYLE", "exec").lower()
        self.extra_args = [a for a in os.getenv("DROID_EXTRA_ARGS", "").split() if a]
        # 읽기 타임아웃(초) 및 첫 토큰 타임아웃(초)
        self.read_timeout = float(os.getenv("DROID_READ_TIMEOUT", "120"))
        self.first_token_timeout = float(os.getenv("DROID_FIRST_TOKEN_TIMEOUT", "60"))

        self.process = None
        # 챗봇 전용 작업 디렉토리 (chatbot_workspace/CLAUDE.md 읽기 위해)
        self.chatbot_workspace = Path(__file__).parent.parent.parent / "chatbot_workspace"
        self.chatbot_workspace.mkdir(exist_ok=True)

    async def start(
        self,
        system_prompt=None,
        model: str | None = None,
        style: str | None = None,
        session_id: str | None = None,
    ):
        """Droid 프로세스 시작

        Args:
            system_prompt: 시스템 프롬프트(미사용. stdin에 포함)
            model: 사용할 모델명. None이면 기본 모델 사용
        """
        if self.process is not None:
            logger.warning("Droid process already running")
            return

        try:
            use_model = model or self.primary_model
            use_style = (style or self.exec_style or "exec").lower()

            # 기본 exec 스타일 (공식 문서: --output-format json|debug)
            args = [
                self.droid_path,
                "exec",
            ]

            if not self.skip_permissions_unsafe:
                args.extend(["--output-format", "stream-json"])  # JSON 스트림 모드
            else:
                logger.info("Droid skip-permissions 모드: text 출력 사용")

            if self.skip_permissions_unsafe:
                args.append("--skip-permissions-unsafe")
                logger.info("Droid executes with --skip-permissions-unsafe (비상호작용 환경)")
            else:
                args.extend(["--auto", self.auto_level])

            args.extend(["--model", use_model])
            logger.info(f"Droid command args: {args}")
            logger.info(f"Droid working directory: {self.chatbot_workspace}")

            # 기존 세션 이어가기
            if session_id:
                args.extend(["--session-id", str(session_id)])

            if self.extra_args:
                args.extend(self.extra_args)

            self.process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.chatbot_workspace),  # 챗봇 전용 디렉토리에서 실행
            )
            logger.info(
                f"Droid process started (style={use_style}, model={use_model}, cwd={self.chatbot_workspace})"
            )
        except Exception as e:
            logger.error(f"Failed to start Droid: {e}")
            raise

    async def stop(self):
        """Droid 프로세스 종료"""
        if self.process is None:
            return

        try:
            # Check if process has already terminated
            if self.process.returncode is None:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
                logger.info("Droid process stopped")
            else:
                logger.info("Droid process already stopped")
        except (TimeoutError, ProcessLookupError) as e:
            if isinstance(e, asyncio.TimeoutError):
                try:
                    self.process.kill()
                    await self.process.wait()
                    logger.warning("Droid process killed (timeout)")
                except ProcessLookupError:
                    logger.info("Droid process already gone")
            else:
                logger.info("Droid process already gone")
        finally:
            self.process = None

    async def send_message(
        self,
        prompt,
        system_prompt=None,
        callback=None,
        session_id: str | None = None,
        model: str | None = None,
    ):
        """
        Droid에 메시지 전송 및 스트리밍 응답 수신

        Args:
            prompt: 전송할 프롬프트
            system_prompt: 시스템 프롬프트 (캐릭터 설정 등) - 프롬프트에 포함됨
            callback: 각 JSON 라인을 받을 때 호출될 async 콜백 함수
            session_id: 이어서 사용할 세션 ID

        Returns:
            최종 결과 딕셔너리
        """
        logger.info(f"Starting Droid send_message with prompt: {prompt[:100]}...")
        latest_session_id: str | None = session_id

        async def _invoke_once(model_for_try: str | None, session_id_for_try: str | None):
            """단일 모델로 한 번 호출 수행.

            Returns: (success: bool, assistant_message: str, error: dict|None)
            """
            nonlocal latest_session_id
            # 실행 스타일 순서 결정
            styles = ["exec"]

            # stderr 수집 버퍼
            stderr_buffer: list[str] = []

            # ANSI escape 코드 제거를 위한 함수
            import re

            ansi_escape = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\[?25[lh])")

            def remove_ansi_escape(text):
                # 더 포괄적인 ANSI escape 시퀀스 제거
                import re

                # ESC로 시작하는 모든 ANSI 시퀀스 제거
                text = re.sub(r"\x1b\[[0-9;]*m", "", text)  # 색상 코드
                text = re.sub(r"\x1b\[[0-9]*;?[0-9]*[A-Za-z]", "", text)  # 커서 이동 등
                text = re.sub(r"\x1b\[@-Z\\-_]", "", text)  # 기타 제어 문자
                text = re.sub(r"\x1b\[?[0-9]*[A-Za-z]", "", text)  # 간단한 형식
                return text

            def is_noise_text(text: str) -> bool:
                """Droid CLI 자동 업데이트 메시지 등 사용자에게 불필요한 출력 여부"""
                noise_phrases = [
                    "Downloading update...",
                    "Auto-update failed",
                    "Please update manually",
                    "curl -fsSL https://app.factory.ai/cli | sh",
                ]
                stripped = text.strip()
                if not stripped:
                    return True
                return any(phrase in stripped for phrase in noise_phrases)

            async def read_stderr():
                while True:
                    line = await self.process.stderr.readline()
                    if not line:
                        break
                    text = line.decode("utf-8").strip()
                    stderr_buffer.append(text)
                    if len(stderr_buffer) > 200:
                        stderr_buffer.pop(0)
                    # 에러 패턴은 warning으로 승격
                    lower = text.lower()
                    if any(k in lower for k in ("error", "failed", "429", "rate limit")):
                        logger.warning(f"Droid stderr: {text}")
                    else:
                        logger.debug(f"Droid stderr: {text}")

            for style in styles:
                if self.process is None:
                    await self.start(
                        model=model_for_try, style=style, session_id=session_id_for_try
                    )

                # System prompt를 프롬프트 앞에 추가
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n=== 사용자 메시지 ===\n{prompt}"

                # 프롬프트 전송
                prompt_with_newline = full_prompt + "\n"
                logger.info(f"Sending prompt to Droid (length: {len(prompt_with_newline)})")
                self.process.stdin.write(prompt_with_newline.encode("utf-8"))
                await self.process.stdin.drain()
                self.process.stdin.close()  # stdin 닫기 (중요!)
                logger.info("Prompt sent to Droid, stdin closed")

                assistant_message = ""
                stderr_task = asyncio.create_task(read_stderr())

                # stdout 읽기 (타임아웃 포함)
                response_started = False
                first_token_deadline = asyncio.get_event_loop().time() + self.first_token_timeout
                error_payload = None

                try:
                    # Read all remaining output after stdin is closed
                    while True:
                        try:
                            line = await asyncio.wait_for(
                                self.process.stdout.readline(), timeout=self.read_timeout
                            )

                            if not line:
                                # No more output, break the loop
                                break

                            raw = line.decode("utf-8").strip()
                            logger.debug(f"Droid raw output: {raw}")
                            try:
                                data = json.loads(raw)
                            except json.JSONDecodeError:
                                # JSON이 아닐 경우에도 토큰으로 취급(유연 파싱)
                                if raw:
                                    clean_text = remove_ansi_escape(raw)
                                    if not is_noise_text(clean_text):
                                        if callback:
                                            await callback(
                                                {
                                                    "type": "content_block_delta",
                                                    "delta": {"text": clean_text},
                                                }
                                            )
                                        assistant_message += clean_text
                                logger.debug(f"Droid non-JSON output: {raw}")
                                continue

                            # 세션 ID 저장 (init 메시지에서)
                            if data.get("type") == "system" and data.get("subtype") == "init":
                                new_session = data.get("session_id")
                                if new_session:
                                    latest_session_id = new_session
                                    logger.info(f"Droid Session ID: {new_session}")
                                if callback:
                                    await callback(
                                        {
                                            "type": "system",
                                            "subtype": "droid_init",
                                            "session_id": new_session,
                                        }
                                    )

                            # 오류 이벤트 캐치 (가능 시)
                            if data.get("type") == "error":
                                error_payload = {
                                    "type": "error",
                                    "code": data.get("code"),
                                    "message": data.get("message") or data.get("error"),
                                }
                                logger.warning(f"Droid error event: {error_payload}")

                            # 메시지/델타 스트림 처리(유연 파싱)
                            text_chunks: list[str] = []

                            # 1) 기존 가정 형식
                            if data.get("type") == "message" and (
                                data.get("role") in ("assistant", "bot", None)
                            ):
                                if isinstance(data.get("text"), str):
                                    text_chunks.append(remove_ansi_escape(data.get("text")))
                                if isinstance(data.get("content"), str):
                                    text_chunks.append(remove_ansi_escape(data.get("content")))

                            # 2) Claude 유사 형식
                            if data.get("type") == "assistant":
                                message_obj = data.get("message") or {}
                                content_items = message_obj.get("content", [])
                                for item in content_items:
                                    if (
                                        isinstance(item, dict)
                                        and item.get("type") == "text"
                                        and isinstance(item.get("text"), str)
                                    ):
                                        text_chunks.append(remove_ansi_escape(item.get("text")))

                            # 3) 일반적인 델타 키들
                            if isinstance(data.get("delta"), str):
                                text_chunks.append(remove_ansi_escape(data.get("delta")))
                            if isinstance(data.get("token"), str):
                                text_chunks.append(remove_ansi_escape(data.get("token")))

                            if text_chunks:
                                response_started = True
                                for chunk in text_chunks:
                                    if chunk and not is_noise_text(chunk):
                                        if callback:
                                            await callback(
                                                {
                                                    "type": "content_block_delta",
                                                    "delta": {"text": chunk},
                                                }
                                            )
                                        assistant_message += chunk

                            # 응답 완료 감지 - droid doesn't send explicit completion messages
                            # if data.get('type') in ('response_complete', 'result'):
                            #     logger.info("Droid response complete")
                            #     break

                            # tool_result 에러는 무시하고 계속 진행
                            if data.get("type") == "tool_result" and data.get("isError") == True:
                                logger.warning(f"Droid tool error (ignoring): {data.get('value')}")
                                continue

                            # 첫 토큰 타임아웃 체크
                            if (
                                not response_started
                                and asyncio.get_event_loop().time() > first_token_deadline
                            ):
                                logger.error("Droid first token timeout")
                                return (
                                    False,
                                    assistant_message,
                                    {
                                        "type": "timeout",
                                        "stage": "first_token",
                                        "stderr": stderr_buffer[-20:],
                                    },
                                )

                        except TimeoutError:
                            logger.error("Timeout waiting for Droid response (read)")
                            return (
                                False,
                                assistant_message,
                                {"type": "timeout", "stage": "read", "stderr": stderr_buffer[-20:]},
                            )

                finally:
                    stderr_task.cancel()

                    # 프로세스 종료 대기 및 정리
                    try:
                        await asyncio.wait_for(self.process.wait(), timeout=5.0)
                    except TimeoutError:
                        self.process.kill()
                        await self.process.wait()
                    self.process = None

                # 메시지가 비어있고 오류가 있다면 실패로 간주
                if not assistant_message and error_payload:
                    return False, assistant_message, error_payload

                # 메시지가 비어있으면 실패 처리 (상위 폴백용)
                if not assistant_message:
                    logger.warning(
                        f"Droid produced empty response (style={style}); trying next style if available"
                    )
                    continue

                # 후처리: 멀티 캐릭터 태그([이름]:) 앞에 줄바꿈 보정
                def _format_speaker_lines(text: str) -> str:
                    try:
                        import re

                        # [이름]: 패턴 앞에 줄바꿈 삽입(문서 시작 제외)
                        text = re.sub(r"(?<!^)\s*(\[[^\[\]]{1,20}\]:)", r"\n\1", text)
                        # 중복 개행 축소
                        text = re.sub(r"\n{3,}", "\n\n", text)
                        return text.lstrip("\n")
                    except Exception:
                        return text

                assistant_message = _format_speaker_lines(assistant_message)
                return True, assistant_message, None

            # 모든 스타일이 실패
            return False, "", {"type": "empty_response", "stderr": stderr_buffer[-20:]}

        try:
            # 1) 기본 모델 시도
            initial_model = model or self.primary_model
            ok, msg, err = await _invoke_once(initial_model, latest_session_id)
            if ok and msg:
                return {
                    "success": True,
                    "message": msg,
                    "token_info": None,
                    "session_id": latest_session_id,
                }

            # 2) 폴백 모델 순차 시도
            for idx, fb_model in enumerate(self.fallback_models):
                logger.warning(f"Retrying with fallback model {fb_model} (#{idx+1})")
                ok, msg, err = await _invoke_once(fb_model, latest_session_id)
                if ok and msg:
                    return {
                        "success": True,
                        "message": msg,
                        "token_info": None,
                        "fallback_used": fb_model,
                        "session_id": latest_session_id,
                    }

            # 실패 최종 반환
            logger.warning(f"All Droid attempts failed (last session_id={latest_session_id})")
            fallback_session_id = None if latest_session_id == session_id else latest_session_id
            return {
                "success": False,
                "error": err or {"type": "unknown"},
                "session_id": fallback_session_id,
            }

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await self.stop()
            fallback_session_id = None if latest_session_id == session_id else latest_session_id
            error_msg = str(e).lower()
            session_error = any(kw in error_msg for kw in ("session", "expired", "invalid"))
            return {
                "success": False,
                "error": str(e),
                "session_id": fallback_session_id,
                "session_expired": session_error,
            }

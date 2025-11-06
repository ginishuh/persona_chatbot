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
        self.fallback_models = [m.strip() for m in os.getenv("DROID_FALLBACK_MODELS", "").split(",") if m.strip()]
        self.auto_level = os.getenv("DROID_AUTO", "low")
        # 실행 방식: exec | direct | auto
        # Factory 공식 권장은 headless `droid exec` 경로
        self.exec_style = os.getenv("DROID_EXEC_STYLE", "exec").lower()
        self.extra_args = [a for a in os.getenv("DROID_EXTRA_ARGS", "").split() if a]
        # 읽기 타임아웃(초) 및 첫 토큰 타임아웃(초)
        self.read_timeout = float(os.getenv("DROID_READ_TIMEOUT", "120"))
        self.first_token_timeout = float(os.getenv("DROID_FIRST_TOKEN_TIMEOUT", "30"))

        self.process = None
        self.session_id = None
        # 챗봇 전용 작업 디렉토리 (chatbot_workspace/CLAUDE.md 읽기 위해)
        self.chatbot_workspace = Path(__file__).parent.parent.parent / "chatbot_workspace"
        self.chatbot_workspace.mkdir(exist_ok=True)

    async def start(self, system_prompt=None, model: str | None = None, style: str | None = None):
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
                "--output-format", "stream-json",  # 라인 단위 JSON 스트림 (공식 문서)
                "--auto", self.auto_level,
                "--model", use_model,
            ]

            # 기존 세션 이어가기
            if self.session_id:
                args.extend(["--session-id", str(self.session_id)])

            if self.extra_args:
                args.extend(self.extra_args)

            self.process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.chatbot_workspace)  # 챗봇 전용 디렉토리에서 실행
            )
            logger.info(f"Droid process started (style={use_style}, model={use_model}, cwd={self.chatbot_workspace})")
        except Exception as e:
            logger.error(f"Failed to start Droid: {e}")
            raise

    async def stop(self):
        """Droid 프로세스 종료"""
        if self.process is None:
            return

        try:
            self.process.terminate()
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
            logger.info("Droid process stopped")
        except asyncio.TimeoutError:
            self.process.kill()
            await self.process.wait()
            logger.warning("Droid process killed (timeout)")
        finally:
            self.process = None
            self.session_id = None

    async def send_message(self, prompt, system_prompt=None, callback=None):
        """
        Droid에 메시지 전송 및 스트리밍 응답 수신

        Args:
            prompt: 전송할 프롬프트
            system_prompt: 시스템 프롬프트 (캐릭터 설정 등) - 프롬프트에 포함됨
            callback: 각 JSON 라인을 받을 때 호출될 async 콜백 함수

        Returns:
            최종 결과 딕셔너리
        """
        async def _invoke_once(model_for_try: str | None):
            """단일 모델로 한 번 호출 수행.

            Returns: (success: bool, assistant_message: str, error: dict|None)
            """
            # 실행 스타일 순서 결정
            styles = ["exec"]

            # stderr 수집 버퍼
            stderr_buffer: list[str] = []

            async def read_stderr():
                while True:
                    line = await self.process.stderr.readline()
                    if not line:
                        break
                    text = line.decode('utf-8').strip()
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
                    await self.start(model=model_for_try, style=style)

                # System prompt를 프롬프트 앞에 추가
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n=== 사용자 메시지 ===\n{prompt}"

                # 프롬프트 전송
                prompt_with_newline = full_prompt + "\n"
                self.process.stdin.write(prompt_with_newline.encode('utf-8'))
                await self.process.stdin.drain()
                self.process.stdin.close()  # stdin 닫기 (중요!)

                assistant_message = ""
                stderr_task = asyncio.create_task(read_stderr())

                # stdout 읽기 (타임아웃 포함)
                response_started = False
                first_token_deadline = asyncio.get_event_loop().time() + self.first_token_timeout
                error_payload = None

                try:
                    while True:
                        try:
                            line = await asyncio.wait_for(
                                self.process.stdout.readline(),
                                timeout=self.read_timeout
                            )

                            if not line:
                                break

                            raw = line.decode('utf-8').strip()
                            try:
                                data = json.loads(raw)
                            except json.JSONDecodeError:
                                # JSON이 아닐 경우에도 토큰으로 취급(유연 파싱)
                                if raw:
                                    if callback:
                                        await callback({
                                            "type": "content_block_delta",
                                            "delta": {"text": raw}
                                        })
                                    assistant_message += raw
                                logger.debug(f"Droid non-JSON output: {raw}")
                                continue

                            # 세션 ID 저장 (init 메시지에서)
                            if data.get('type') == 'system' and data.get('subtype') == 'init':
                                self.session_id = data.get('session_id')
                                logger.info(f"Droid Session ID: {self.session_id}")
                                if callback:
                                    await callback({
                                        "type": "system",
                                        "subtype": "droid_init",
                                        "session_id": self.session_id
                                    })

                            # 오류 이벤트 캐치 (가능 시)
                            if data.get('type') == 'error':
                                error_payload = {
                                    "type": "error",
                                    "code": data.get('code'),
                                    "message": data.get('message') or data.get('error')
                                }
                                logger.warning(f"Droid error event: {error_payload}")

                            # 메시지/델타 스트림 처리(유연 파싱)
                            text_chunks: list[str] = []

                            # 1) 기존 가정 형식
                            if data.get('type') == 'message' and (data.get('role') in ('assistant', 'bot', None)):
                                if isinstance(data.get('text'), str):
                                    text_chunks.append(data.get('text'))
                                if isinstance(data.get('content'), str):
                                    text_chunks.append(data.get('content'))

                            # 2) Claude 유사 형식
                            if data.get('type') == 'assistant':
                                message_obj = data.get('message') or {}
                                content_items = message_obj.get('content', [])
                                for item in content_items:
                                    if isinstance(item, dict) and item.get('type') == 'text' and isinstance(item.get('text'), str):
                                        text_chunks.append(item.get('text'))

                            # 3) 일반적인 델타 키들
                            if isinstance(data.get('delta'), str):
                                text_chunks.append(data.get('delta'))
                            if isinstance(data.get('token'), str):
                                text_chunks.append(data.get('token'))

                            if text_chunks:
                                response_started = True
                                for chunk in text_chunks:
                                    if chunk:
                                        if callback:
                                            await callback({
                                                "type": "content_block_delta",
                                                "delta": {"text": chunk}
                                            })
                                        assistant_message += chunk

                            # 응답 완료 감지
                            if data.get('type') in ('response_complete', 'result'):
                                logger.info("Droid response complete")
                                break

                            # 첫 토큰 타임아웃 체크
                            if not response_started and asyncio.get_event_loop().time() > first_token_deadline:
                                logger.error("Droid first token timeout")
                                return False, assistant_message, {"type": "timeout", "stage": "first_token", "stderr": stderr_buffer[-20:]}

                        except asyncio.TimeoutError:
                            logger.error("Timeout waiting for Droid response (read)")
                            return False, assistant_message, {"type": "timeout", "stage": "read", "stderr": stderr_buffer[-20:]}

                finally:
                    stderr_task.cancel()

                    # 프로세스 종료 대기 및 정리
                    try:
                        await asyncio.wait_for(self.process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        self.process.kill()
                        await self.process.wait()
                    self.process = None

                # 메시지가 비어있고 오류가 있다면 실패로 간주
                if not assistant_message and error_payload:
                    return False, assistant_message, error_payload

                # 메시지가 비어있으면 실패 처리 (상위 폴백용)
                if not assistant_message:
                    logger.warning(f"Droid produced empty response (style={style}); trying next style if available")
                    continue

                return True, assistant_message, None

            # 모든 스타일이 실패
            return False, "", {"type": "empty_response", "stderr": stderr_buffer[-20:]}

        try:
            # 1) 기본 모델 시도
            ok, msg, err = await _invoke_once(self.primary_model)
            if ok and msg:
                return {"success": True, "message": msg, "token_info": None}

            # 2) 폴백 모델 순차 시도
            for idx, fb_model in enumerate(self.fallback_models):
                logger.warning(f"Retrying with fallback model {fb_model} (#{idx+1})")
                ok, msg, err = await _invoke_once(fb_model)
                if ok and msg:
                    return {
                        "success": True,
                        "message": msg,
                        "token_info": None,
                        "fallback_used": fb_model
                    }

            # 실패 최종 반환
            return {
                "success": False,
                "error": err or {"type": "unknown"}
            }

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await self.stop()
            return {
                "success": False,
                "error": str(e)
            }

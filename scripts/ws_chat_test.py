#!/usr/bin/env python3
"""WebSocket 메시지 송신 통합 테스트 스크립트 (로그인 포함)

한국어 주석/문서화: 서버가 로그인(토큰) 요구 시 로그인 절차를 수행하고,
컨텍스트 설정 후 챗 요청을 전송하여 스트리밍 응답을 확인합니다.

사용:
  python scripts/ws_chat_test.py --uri ws://localhost:8765 --provider droid --prompt "안녕하세요?"
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from argparse import ArgumentParser

try:
    import websockets  # type: ignore
except Exception as e:  # pragma: no cover - 런타임 설치 안내용
    raise SystemExit(
        "websockets 모듈이 필요합니다.\n"
        "설치: pip install websockets"
    )


logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("ws_chat_test")


def load_env_dotenv(path: str = ".env") -> dict[str, str]:
    """아주 단순한 .env 파서 (주요 키만 추출)."""
    env: dict[str, str] = {}
    if not os.path.exists(path):
        return env
    line_re = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            m = line_re.match(line)
            if not m:
                continue
            key, val = m.group(1), m.group(2)
            env[key] = val
    return env


async def _send_reset_sessions(ws, token: str | None) -> None:
    """서버에 세션 초기화를 요청 (로그인 사용 시 토큰 동봉)."""
    try:
        req = {"action": "reset_sessions"}
        if token:
            req["token"] = token
        await ws.send(json.dumps(req))
        # 응답은 필수가 아니지만 가능하면 소모
        try:
            res_raw = await asyncio.wait_for(ws.recv(), timeout=2.0)
            res = json.loads(res_raw)
            if res.get("action") == "reset_sessions":
                logger.info("세션 초기화 완료")
        except asyncio.TimeoutError:
            pass
    except Exception:
        # 정리 과정 오류는 치명적이지 않으므로 무시
        pass


async def run(uri: str, prompt: str, provider: str, cleanup: bool = True, timeout_seconds: int = 240) -> int:
    env = load_env_dotenv()
    username = env.get("APP_LOGIN_USERNAME", "")
    password = env.get("APP_LOGIN_PASSWORD", "")

    token: str | None = None

    logger.info(f"연결 시도: {uri}")
    async with websockets.connect(uri) as ws:
        # 초기 환영/요구 메시지 수신 시도 (있을 때만)
        try:
            for _ in range(2):
                msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                data = json.loads(msg)
                logger.info(f"서버 초기 메시지: action={data.get('action')}")
                if data.get("action") == "auth_required":
                    logger.info("서버가 인증을 요구합니다 → 로그인 진행")
        except asyncio.TimeoutError:
            pass

        # 로그인 수행 (비밀번호가 설정되어 있다면 필요)
        if password:
            login_req = {
                "action": "login",
                "username": username,
                "password": password,
            }
            await ws.send(json.dumps(login_req))
            login_res = json.loads(await ws.recv())
            if login_res.get("action") != "login" or not login_res.get("data", {}).get("success"):
                logger.error(f"로그인 실패: {login_res}")
                return 2
            token = login_res["data"].get("token")
            logger.info("로그인 성공, 토큰 발급 완료")

        # 컨텍스트 설정 (필드 상위 배치)
        set_ctx = {
            "action": "set_context",
            "token": token,
            "world": "테스트 세계",
            "situation": "간단 메시지 송수신 테스트",
            "user_character": "테스터",
            "characters": [
                {"name": "테스트봇", "description": "테스트용 캐릭터"}
            ],
            "narrator_mode": "no_narrator",
            "adult_level": "safe",
            "ai_provider": provider,
        }
        await ws.send(json.dumps(set_ctx))
        set_ctx_res = json.loads(await ws.recv())
        if set_ctx_res.get("action") != "set_context" or not set_ctx_res.get("data", {}).get("success"):
            logger.error(f"컨텍스트 설정 실패: {set_ctx_res}")
            return 3
        logger.info("컨텍스트 설정 완료")

        # 챗 요청 전송
        chat_req = {
            "action": "chat",
            "token": token,
            "prompt": prompt,
            "provider": provider,
        }
        await ws.send(json.dumps(chat_req))
        logger.info("메시지 전송 완료 → 스트리밍 수신 대기")

        full_text_chunks: list[str] = []
        got_stream_chunk = False
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                logger.error("응답 타임아웃")
                return 4
            data = json.loads(raw)
            action = data.get("action")
            if action == "chat_stream":
                sd = data.get("data", {})
                if sd.get("type") == "assistant":
                    msg = sd.get("message", {})
                    for c in msg.get("content", []):
                        if c.get("type") == "text":
                            chunk = c.get("text", "")
                            full_text_chunks.append(chunk)
                            print(chunk, end="", flush=True)
                            got_stream_chunk = True
            elif action == "chat_complete":
                ok = bool(data.get("data", {}).get("success"))
                print()
                # 스트림이 비어있으면 최종 메시지라도 출력
                if not got_stream_chunk:
                    final_msg = data.get("data", {}).get("message")
                    if isinstance(final_msg, str) and final_msg.strip():
                        print(final_msg)
                logger.info("챗 완료 수신")
                # 테스트 종료 시 세션 정리
                if cleanup:
                    await _send_reset_sessions(ws, token)
                return 0 if ok else 5
            elif action == "error":
                logger.error(f"서버 에러: {data.get('data')}" )
                # 에러 시에도 세션 정리 시도
                if cleanup:
                    await _send_reset_sessions(ws, token)
                return 6


async def _run_all(uri: str, prompt: str, providers: list[str], timeout_seconds: int) -> int:
    """여러 프로바이더 순차 테스트. 하나라도 실패하면 마지막 실패 코드 반환."""
    last_code = 0
    for p in providers:
        logger.info("\n=== Provider 테스트 시작: %s ===", p)
        code = await run(uri, prompt, p, cleanup=True, timeout_seconds=timeout_seconds)
        if code != 0:
            last_code = code
        logger.info("=== Provider 테스트 종료: %s (code=%s) ===\n", p, code)
    return last_code


def main() -> int:
    ap = ArgumentParser()
    ap.add_argument("--uri", default="ws://localhost:8765", help="WebSocket URL")
    ap.add_argument(
        "--provider",
        default="all",
        help="AI provider: claude|droid|gemini 또는 콤마 구분 목록, 'all' 지원",
    )
    ap.add_argument("--prompt", default="안녕하세요?", help="테스트 메시지")
    ap.add_argument("--timeout", type=int, default=240, help="스트리밍 응답 대기 타임아웃(초)")
    args = ap.parse_args()

    if args.provider.lower() == "all":
        providers = ["claude", "droid", "gemini"]
        return asyncio.run(_run_all(args.uri, args.prompt, providers, args.timeout))
    else:
        # 콤마 구분 목록 지원
        providers = [p.strip() for p in args.provider.split(",") if p.strip()]
        if len(providers) == 1:
            return asyncio.run(run(args.uri, args.prompt, providers[0], cleanup=True, timeout_seconds=args.timeout))
        return asyncio.run(_run_all(args.uri, args.prompt, providers, args.timeout))


if __name__ == "__main__":
    raise SystemExit(main())

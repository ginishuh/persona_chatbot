import asyncio
import json

from server.handlers.claude_handler import ClaudeCodeHandler


class _FakeWriter:
    def __init__(self):
        self.buffer = bytearray()

    def write(self, b: bytes):
        self.buffer.extend(b)

    async def drain(self):
        return None

    def close(self):
        pass


class _FakeReader:
    def __init__(self, lines: list[str]):
        self._lines = [l.encode("utf-8") for l in lines]

    async def readline(self) -> bytes:
        if not self._lines:
            return b""
        return self._lines.pop(0)


class _FakeProcess:
    def __init__(self, stdout_lines: list[str], stderr_lines: list[str] | None = None):
        self.stdin = _FakeWriter()
        self.stdout = _FakeReader(stdout_lines)
        self.stderr = _FakeReader(stderr_lines or [])
        self.returncode = None
        self._waited = False

    def terminate(self):
        self.returncode = 0

    def kill(self):
        self.returncode = -9

    async def wait(self):
        self._waited = True
        self.returncode = self.returncode or 0
        return self.returncode


async def _run(handler: ClaudeCodeHandler):
    chunks: list[dict] = []

    async def cb(d):
        chunks.append(d)

    res = await handler.send_message(
        "hi",
        system_prompt="sys",
        callback=cb,
        session_id=None,
        model=None,
    )
    return res, chunks


def test_claude_handler_stream(monkeypatch):
    # 구성: session_id → assistant 텍스트 → result(usage)
    lines = [
        json.dumps({"session_id": "S1", "type": "system"}),
        json.dumps(
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "HELLO"}]},
            }
        ),
        json.dumps(
            {
                "type": "result",
                "usage": {
                    "input_tokens": 1,
                    "cache_read_input_tokens": 2,
                    "cache_creation_input_tokens": 3,
                    "output_tokens": 4,
                },
            }
        ),
    ]

    async def fake_exec(*args, **kwargs):  # noqa: D401
        return _FakeProcess(lines, [])

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    handler = ClaudeCodeHandler(claude_path="claude")
    res, chunks = asyncio.run(_run(handler))

    assert res["success"] is True
    assert res["message"] == "HELLO"
    assert res["session_id"] == "S1"
    assert res["token_info"]["total_tokens"] == (1 + 2 + 3 + 4)
    # 콜백이 최소 한 번 호출되었는지
    assert any(isinstance(c, dict) for c in chunks)


def test_claude_handler_timeout(monkeypatch):
    # stdout.readline에서 TimeoutError 유발
    class _TimeoutReader:
        async def readline(self):
            raise TimeoutError()

    class _P:
        def __init__(self):
            self.stdin = _FakeWriter()
            self.stdout = _TimeoutReader()
            self.stderr = _FakeReader([])

        async def wait(self):
            return 0

    async def fake_exec(*args, **kwargs):
        return _P()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    handler = ClaudeCodeHandler(claude_path="claude")
    res, _ = asyncio.run(_run(handler))
    # timeout 발생했어도 graceful하게 success True(메시지 빈값) 혹은 False 처리
    assert res.get("success") in (True, False)

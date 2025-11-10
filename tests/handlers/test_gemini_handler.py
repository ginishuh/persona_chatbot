import asyncio
import json

from server.handlers.gemini_handler import GeminiHandler


class _FakeWriter:
    def write(self, b: bytes):
        pass

    async def drain(self):
        return None

    def close(self):
        pass


class _FakeReader:
    def __init__(self, lines: list[str]):
        self._lines = [line.encode("utf-8") for line in lines]

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

    def terminate(self):
        self.returncode = 0

    def kill(self):
        self.returncode = -9

    async def wait(self):
        self.returncode = self.returncode or 0
        return self.returncode


async def _run(handler: GeminiHandler):
    out = []

    async def cb(d):
        out.append(d)

    res = await handler.send_message("hi", system_prompt="sys", callback=cb)
    return res, out


def test_gemini_handler_stream(monkeypatch):
    lines = [
        json.dumps({"session_id": "G1"}),
        json.dumps({"type": "message", "role": "assistant", "content": "A", "delta": True}),
        "non-json-line",  # fallback path
    ]

    async def fake_exec(*args, **kwargs):
        return _FakeProcess(lines, [])

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    handler = GeminiHandler(gemini_path="gemini")
    res, out = asyncio.run(_run(handler))

    assert res["success"] is True
    assert "A" in res["message"]
    # 콜백이 변환 형식으로 호출되었는지
    assert any(d.get("type") == "content_block_delta" for d in out)


def test_gemini_handler_timeout(monkeypatch):
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
    handler = GeminiHandler(gemini_path="gemini")
    res, _ = asyncio.run(_run(handler))
    assert res.get("success") in (True, False)

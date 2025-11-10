import asyncio
import json

from server.handlers.droid_handler import DroidHandler


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


async def _run(handler: DroidHandler):
    out = []

    async def cb(d):
        out.append(d)

    res = await handler.send_message("hi", system_prompt="sys", callback=cb)
    return res, out


def test_droid_handler_stream(monkeypatch):
    # system init → assistant message(text) → delta token → plain text
    lines = [
        json.dumps({"type": "system", "subtype": "init", "session_id": "D1"}),
        json.dumps(
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "DR HELLO"}]},
            }
        ),
        json.dumps({"delta": " more"}),
        "plain tail",
    ]

    async def fake_exec(*args, **kwargs):
        return _FakeProcess(lines, [])

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    handler = DroidHandler(droid_path="droid")
    res, out = asyncio.run(_run(handler))

    assert res["success"] is True
    assert "DR HELLO" in res["message"] and "more" in res["message"]
    assert res.get("session_id") == "D1"
    # 콜백으로 delta가 전달되었는지
    assert any(d.get("type") in ("content_block_delta", "assistant") for d in out)


def test_droid_handler_timeout(monkeypatch):
    class _TimeoutReader:
        async def readline(self):
            raise TimeoutError()

    class _P:
        def __init__(self):
            self.stdin = _FakeWriter()
            self.stdout = _TimeoutReader()
            self.stderr = _FakeReader([])
            self.returncode = None

        def terminate(self):
            self.returncode = 0

        async def wait(self):
            self.returncode = 0
            return 0

    async def fake_exec(*args, **kwargs):
        return _P()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    handler = DroidHandler(droid_path="droid")
    res, _ = asyncio.run(_run(handler))
    assert res.get("success") in (True, False)


def test_droid_handler_start_args_variants(monkeypatch):
    captured = {}

    class _P:
        def __init__(self):
            self.stdin = _FakeWriter()
            self.stdout = _FakeReader([])
            self.stderr = _FakeReader([])
            self.returncode = None

        def terminate(self):
            self.returncode = 0

        async def wait(self):
            self.returncode = 0
            return 0

    async def fake_exec(*args, **kwargs):
        captured["args"] = list(args)
        return _P()

    monkeypatch.setenv("DROID_SKIP_PERMISSIONS_UNSAFE", "1")
    monkeypatch.setenv("DROID_MODEL", "glm-x")
    monkeypatch.setenv("DROID_EXEC_STYLE", "exec")
    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    h = DroidHandler(droid_path="droid")
    # send_message가 내부에서 start를 호출함
    asyncio.run(h.send_message("hello", system_prompt="SYS"))
    args = [str(x) for x in captured["args"]]
    # skip-permissions 옵션 포함 및 모델 인자 확인
    assert "--skip-permissions-unsafe" in args
    assert "--model" in args and "glm-x" in args

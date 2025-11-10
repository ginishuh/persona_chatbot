import asyncio
from pathlib import Path

from server.handlers.workspace_handler import WorkspaceHandler


class _FakeProc:
    def __init__(self, returncode=0, out=b"", err=b""):
        self.returncode = returncode
        self._out = out
        self._err = err

    async def communicate(self):
        return self._out, self._err


def _mk_ws(tmp_path: Path) -> WorkspaceHandler:
    ws = WorkspaceHandler(workspace_path=str(tmp_path))
    return ws


def test_git_check_status_non_repo(tmp_path: Path):
    ws = _mk_ws(tmp_path)
    # .git 없음 → is_repo False
    res = asyncio.run(ws.git_check_status())
    assert res["success"] and res["is_repo"] is False


def test_git_check_status_with_upstream(monkeypatch, tmp_path: Path):
    ws = _mk_ws(tmp_path)
    (tmp_path / ".git").mkdir()

    async def fake_exec(*args, **kwargs):
        cmd = list(args)
        if len(cmd) >= 3 and cmd[1] == "status" and "--porcelain" in cmd:
            return _FakeProc(0, out=b" M file.md\n")  # 변경 있음
        if len(cmd) >= 4 and cmd[1] == "rev-parse" and "HEAD" in cmd:
            return _FakeProc(0, out=b"main\n")
        if len(cmd) >= 5 and cmd[1] == "rev-parse" and "@{u}" in cmd:
            return _FakeProc(0, out=b"origin/main\n")
        if len(cmd) >= 4 and cmd[1] == "rev-list" and "--left-right" in cmd and "--count" in cmd:
            return _FakeProc(0, out=b"1 2\n")  # behind=1, ahead=2
        return _FakeProc(0, out=b"", err=b"")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    res = asyncio.run(ws.git_check_status())
    assert res["success"] and res["is_repo"] is True
    assert res["has_changes"] is True
    assert res["branch"] == "main"
    assert res["upstream"] == "origin/main"
    assert res["ahead"] == 2 and res["behind"] == 1


def test_git_init(monkeypatch, tmp_path: Path):
    ws = _mk_ws(tmp_path)

    async def fake_exec(*args, **kwargs):
        return _FakeProc(0, out=b"Initialized empty Git repository\n")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    res = asyncio.run(ws.git_init())
    assert res["success"]
    assert (tmp_path / ".gitignore").exists()


def test_git_sync_host_mode_no_changes(monkeypatch, tmp_path: Path):
    ws = _mk_ws(tmp_path)
    (tmp_path / ".git").mkdir()

    # env: host 모드
    monkeypatch.setenv("APP_GIT_SYNC_MODE", "host")
    monkeypatch.delenv("APP_DISABLE_GIT_PUSH", raising=False)

    calls = []

    async def fake_exec(*args, **kwargs):
        cmd = list(args)
        calls.append(cmd)
        if len(cmd) >= 3 and cmd[1] == "add" and "." in cmd:
            return _FakeProc(0, out=b"")
        if len(cmd) >= 2 and cmd[1] == "commit":
            # nothing to commit 시나리오
            return _FakeProc(1, out=b"nothing to commit, working tree clean\n")
        if len(cmd) >= 4 and cmd[1] == "rev-parse" and "--short" in cmd and "HEAD" in cmd:
            return _FakeProc(0, out=b"abc123\n")
        return _FakeProc(0, out=b"")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    res = asyncio.run(ws.git_sync("msg"))
    assert res["success"] and "호스트" in res.get("warning", "")
    # 트리거 파일 생성 확인
    sync_dir = tmp_path / ".sync"
    assert sync_dir.exists() and any(p.name.startswith("push_") for p in sync_dir.iterdir())


def test_git_pull_success(monkeypatch, tmp_path: Path):
    ws = _mk_ws(tmp_path)
    (tmp_path / ".git").mkdir()

    async def fake_exec(*args, **kwargs):
        return _FakeProc(0, out=b"Already up to date.\n")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    res = asyncio.run(ws.git_pull())
    assert res["success"] and "Pull 완료" in res["message"]


def test_git_sync_container_mode_with_upstream_push(monkeypatch, tmp_path: Path):
    ws = _mk_ws(tmp_path)
    (tmp_path / ".git").mkdir()

    # 컨테이너 모드 (기본), upstream 존재 + pull --rebase 성공 + push 성공
    monkeypatch.delenv("APP_GIT_SYNC_MODE", raising=False)
    monkeypatch.delenv("APP_DISABLE_GIT_PUSH", raising=False)

    def mk_proc(code=0, out=b"", err=b""):
        return _FakeProc(code, out, err)

    async def fake_exec(*args, **kwargs):
        cmd = list(args)
        if len(cmd) >= 3 and cmd[1] == "add":
            return mk_proc(0)
        if len(cmd) >= 2 and cmd[1] == "commit":
            return mk_proc(0, out=b"[main] ok\n")
        if len(cmd) >= 2 and cmd[1] == "rev-parse" and "@{u}" in cmd:
            return mk_proc(0, out=b"origin/main\n")
        if len(cmd) >= 2 and cmd[1] == "pull" and "--rebase" in cmd:
            return mk_proc(0, out=b"Rebase successful\n")
        if len(cmd) >= 2 and cmd[1] == "push":
            return mk_proc(0, out=b"pushed\n")
        if len(cmd) >= 2 and cmd[1] == "rev-parse" and "--short" in cmd:
            return mk_proc(0, out=b"abc123\n")
        return mk_proc(0)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    res = asyncio.run(ws.git_sync("msg"))
    assert res["success"] and "동기화 완료" in res["message"]


def test_git_sync_container_mode_no_upstream_no_remote(monkeypatch, tmp_path: Path):
    ws = _mk_ws(tmp_path)
    (tmp_path / ".git").mkdir()

    def mk_proc(code=0, out=b"", err=b""):
        return _FakeProc(code, out, err)

    async def fake_exec(*args, **kwargs):
        cmd = list(args)
        if len(cmd) >= 3 and cmd[1] == "add":
            return mk_proc(0)
        if len(cmd) >= 2 and cmd[1] == "commit":
            return mk_proc(0, out=b"[main] ok\n")
        if len(cmd) >= 2 and cmd[1] == "rev-parse" and "@{u}" in cmd:
            return mk_proc(1, err=b"no upstream\n")
        if len(cmd) >= 2 and cmd[1] == "push":
            return mk_proc(1, err=b"No configured push destination\n")
        return mk_proc(0)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    res = asyncio.run(ws.git_sync("msg"))
    assert res["success"] and "원격 레포 미설정" in res.get("message", "")


def test_story_save_append_load_delete(tmp_path: Path):
    ws = _mk_ws(tmp_path)

    # 저장(신규)
    ok = asyncio.run(ws.save_story("story1", "# 제목\n본문1\n"))
    assert ok["success"]

    # append: 전체 본문을 넘겨도 delta만 추가
    full2 = "# 제목\n본문1\n본문2\n"
    res = asyncio.run(ws.save_story("story1", full2, append=True))
    assert res["success"] and res.get("appended") is True

    content = asyncio.run(ws.load_story("story1"))
    assert content["success"] and "본문2" in content["content"]

    # append: 새 본문이 접두가 아니면 제목 제거 후 이어붙임
    res = asyncio.run(ws.save_story("story1", "# 새제목\n새본문\n", append=True))
    assert res["success"]
    content2 = asyncio.run(ws.load_story("story1"))
    assert (
        content2["success"]
        and "새제목" not in content2["content"]
        and "새본문" in content2["content"]
    )

    # 삭제
    res = asyncio.run(ws.delete_story("story1"))
    assert res["success"]

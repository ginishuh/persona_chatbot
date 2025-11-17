import pytest

from server.handlers.git_handler import GitHandler


@pytest.mark.asyncio
async def test_git_handler_status_and_commit(monkeypatch, tmp_path):
    gh = GitHandler(repo_path=str(tmp_path))

    async def fake_run_cmd_success(cmd):
        return 0, "ok", ""

    async def fake_run_cmd_nothing_to_commit(cmd):
        if cmd.startswith("git add"):
            return 0, "", ""
        if cmd.startswith("git commit"):
            return 1, "nothing to commit", ""
        return 0, "", ""

    # status success
    monkeypatch.setattr(gh, "_run_command", fake_run_cmd_success)
    s = await gh.status()
    assert s["success"] is True

    # commit_and_push when nothing to commit
    monkeypatch.setattr(gh, "_run_command", fake_run_cmd_nothing_to_commit)
    res = await gh.commit_and_push("msg")
    assert res["success"] is True
    assert "변경사항이 없습니다" in res.get("message", "")

    # commit_and_push full success
    async def fake_all_ok(cmd):
        return 0, "ok", ""

    monkeypatch.setattr(gh, "_run_command", fake_all_ok)
    res2 = await gh.commit_and_push("msg")
    assert res2["success"] is True

    # status failure
    async def fake_fail(cmd):
        return 2, "", "err"

    monkeypatch.setattr(gh, "_run_command", fake_fail)
    s2 = await gh.status()
    assert s2["success"] is False

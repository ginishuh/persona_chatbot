import asyncio

from server.handlers.git_handler import GitHandler


def test_git_handler_commit_push_success(monkeypatch, tmp_path):
    gh = GitHandler(repo_path=str(tmp_path))

    calls = []

    async def fake_run(cmd):
        calls.append(cmd)
        if cmd.startswith("git add"):
            return 0, "", ""
        if cmd.startswith("git commit"):
            return 0, "[main] ok", ""
        if cmd.startswith("git push"):
            return 0, "pushed", ""
        return 0, "", ""

    monkeypatch.setattr(gh, "_run_command", fake_run)

    res = asyncio.run(gh.commit_and_push("msg"))
    assert res["success"] is True and "완료" in res["message"]
    assert any("git add" in c for c in calls) and any("git push" in c for c in calls)


def test_git_status_failure(monkeypatch, tmp_path):
    gh = GitHandler(repo_path=str(tmp_path))

    async def fake_run(cmd):
        return 1, "", "bad"

    # monkeypatch to use shell path variant
    async def fake_shell(command):
        return 1, "", "bad"

    monkeypatch.setattr(gh, "_run_command", fake_shell)

    # status uses _run_command via status? It actually spawns create_subprocess_shell directly,
    # so we test commit path error handling via _run_command
    res = asyncio.run(gh.commit_and_push("msg"))
    assert res["success"] is False

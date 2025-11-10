import asyncio
from pathlib import Path

from server.handlers.mode_handler import ModeHandler


def test_mode_switch_roundtrip(tmp_path: Path):
    # 디렉터리 구조 준비
    root = tmp_path
    (root / ".claude").mkdir()
    (root / ".codex").mkdir()

    # 파일 생성 (루트/하위 모두)
    for d in [root, root / ".claude", root / ".codex"]:
        (d / "CLAUDE.md").write_text("x", encoding="utf-8")
        (d / "AGENTS.md").write_text("y", encoding="utf-8")

    m = ModeHandler(project_root=str(root))

    # 초기 모드: coding
    res = run(m.check_mode())
    assert res["success"] and res["mode"] in {"coding", "mixed", "none"}

    # 챗봇 모드 전환
    s1 = run(m.switch_to_chatbot())
    assert s1["success"] and s1["mode"] == "chatbot"
    # .md가 .bak로 바뀌었는지 일부 체크
    assert not (root / "CLAUDE.md").exists() and (root / "CLAUDE.md.bak").exists()

    # 코딩 모드 전환
    s2 = run(m.switch_to_coding())
    assert s2["success"] and s2["mode"] == "coding"
    assert (root / "CLAUDE.md").exists() and not (root / "CLAUDE.md.bak").exists()


def test_mode_none_and_mixed(tmp_path: Path):
    # none: 파일이 전혀 없는 경우
    m = ModeHandler(project_root=str(tmp_path))
    res = run(m.check_mode())
    assert res["success"] and res["mode"] in {"none", "coding", "chatbot", "mixed"}

    # mixed: 서로 다른 위치/이름 조합으로 .md와 .bak 혼재
    (tmp_path / "CLAUDE.md").write_text("x", encoding="utf-8")
    (tmp_path / "AGENTS.md.bak").write_text("y", encoding="utf-8")
    res2 = run(m.check_mode())
    assert res2["success"] and res2["mode"] == "mixed"

    # switch 스킵 케이스: 이미 .bak가 있을 때 chatbot 전환 시 스킵
    s1 = run(m.switch_to_chatbot())
    assert s1["success"] and "skipped" in s1

    # chatbot 모드 판단: .md 없고 .bak만 있을 때
    # 모든 대상 파일에 대해 .bak만 존재하도록 정리
    for d in [tmp_path, tmp_path / ".claude", tmp_path / ".codex"]:
        d.mkdir(exist_ok=True)
        (d / "AGENTS.md").unlink(missing_ok=True)
        (d / "CLAUDE.md").unlink(missing_ok=True)
        (d / "AGENTS.md.bak").write_text("y", encoding="utf-8")
        (d / "CLAUDE.md.bak").write_text("x", encoding="utf-8")
    res3 = run(m.check_mode())
    assert res3["success"] and res3["mode"] == "chatbot"

    # 스킵 케이스: 동일 파일명에 md와 bak가 동시에 존재
    for d in [tmp_path]:
        (d / "CLAUDE.md").write_text("x", encoding="utf-8")
        (d / "CLAUDE.md.bak").write_text("x", encoding="utf-8")
    s2 = run(m.switch_to_chatbot())
    assert s2["success"] and any("CLAUDE.md" in p for p in s2["skipped"])  # skip line 76

    # switch_to_coding 스킵 케이스: md와 bak가 동시에 있을 때
    s3 = run(m.switch_to_coding())
    assert s3["success"] and any("CLAUDE.md.bak" in p for p in s3["skipped"])  # line 109


def run(coro):
    return asyncio.run(coro)

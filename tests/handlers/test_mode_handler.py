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


import asyncio


def run(coro):
    return asyncio.run(coro)


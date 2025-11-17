import pytest

from server.handlers.mode_handler import ModeHandler


@pytest.mark.asyncio
async def test_mode_handler_check_and_switch(tmp_path):
    # make project root
    proj = tmp_path / "proj"
    proj.mkdir()

    mh = ModeHandler(project_root=str(proj))

    # none initially
    r = await mh.check_mode()
    assert r["success"] is True and r["mode"] == "none"

    # create CLAUDE.md -> coding
    (proj / "CLAUDE.md").write_text("x")
    r2 = await mh.check_mode()
    assert r2["mode"] == "coding"

    # switch to chatbot (rename .md -> .md.bak)
    s = await mh.switch_to_chatbot()
    assert s["success"] is True
    assert (proj / "CLAUDE.md.bak").exists()
    assert not (proj / "CLAUDE.md").exists()

    # switch back to coding
    s2 = await mh.switch_to_coding()
    assert s2["success"] is True
    assert (proj / "CLAUDE.md").exists()

    # mixed: create both md and bak in .claude dir
    claude_dir = proj / ".claude"
    claude_dir.mkdir()
    (claude_dir / "CLAUDE.md").write_text("a")
    (claude_dir / "AGENTS.md.bak").write_text("b")
    r3 = await mh.check_mode()
    assert r3["mode"] == "mixed"

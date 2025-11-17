import json

import pytest

from server.handlers.workspace_handler import WorkspaceHandler


@pytest.mark.asyncio
async def test_workspace_file_and_preset_and_rooms(tmp_path):
    wsroot = tmp_path / "persona_data"
    # WorkspaceHandler creates directories on init
    wh = WorkspaceHandler(str(wsroot))

    # world file save/read/list/delete
    r = await wh.save_file("world", "earth", "content1")
    assert r["success"] is True
    lst = await wh.list_files("world")
    assert any(item["name"] == "earth" for item in lst["files"])
    rf = await wh.read_file("world", "earth")
    assert rf["success"] is True and "content1" in rf["content"]
    dd = await wh.delete_file("world", "earth")
    assert dd["success"] is True

    # char_template (json)
    r2 = await wh.save_file("char_template", "hero", json.dumps({"a": 1}))
    assert r2["success"] is True
    lst2 = await wh.list_files("char_template")
    assert any(item["name"] == "hero" for item in lst2["files"])
    rf2 = await wh.read_file("char_template", "hero")
    assert rf2["success"] is True and '{"a": 1}' in rf2["content"]
    del2 = await wh.delete_file("char_template", "hero")
    assert del2["success"] is True

    # my_profile
    savep = await wh.save_file("my_profile", "my_profile", "me")
    assert savep["success"] is True
    lstp = await wh.list_files("my_profile")
    assert lstp["files"]
    rp = await wh.read_file("my_profile", "my_profile")
    assert rp["success"] is True
    dp = await wh.delete_file("my_profile", "my_profile")
    assert dp["success"] is True

    # presets save/load/delete
    sp = await wh.save_preset("p1", {"x": 1})
    assert sp["success"] is True
    lp = await wh.list_presets()
    assert any(item["name"] == "p1" for item in lp["files"])
    lp_load = await wh.load_preset("p1")
    assert lp_load["success"] is True and lp_load["preset"]["x"] == 1
    dp = await wh.delete_preset("p1")
    assert dp["success"] is True

    # rooms save/load/list/delete
    sr = await wh.save_room("Room A", {"title": "A"})
    assert sr["success"] is True
    lr = await wh.list_rooms()
    assert any(r["room_id"] == sr["room_id"] for r in lr["rooms"])
    rr = await wh.load_room("Room A")
    assert rr["success"] is True and rr["room"]["title"] == "A"
    dr = await wh.delete_room("Room A")
    assert dr["success"] is True

    # stories save/append/load/delete
    ss = await wh.save_story("story1", "Line1\n")
    assert ss["success"] is True
    # append with prefix same as existing: new content starts with existing
    sappend = await wh.save_story("story1", "Line1\nMore", append=True)
    assert sappend["success"] is True
    loaded = await wh.load_story("story1")
    assert loaded["success"] is True and "More" in loaded["content"]
    delst = await wh.delete_story("story1")
    assert delst["success"] is True

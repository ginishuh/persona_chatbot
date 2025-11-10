import asyncio
import json
from pathlib import Path

from server.handlers.workspace_handler import WorkspaceHandler


def run(coro):
    return asyncio.run(coro)


def test_md_file_crud(tmp_path: Path):
    ws = WorkspaceHandler(workspace_path=str(tmp_path))

    # 저장
    res = run(ws.save_file("world", "earth", "hello"))
    assert res["success"]

    # 목록
    res = run(ws.list_files("world"))
    assert res["success"] and any(f["filename"] == "earth.md" for f in res["files"])  # type: ignore[index]

    # 읽기
    res = run(ws.read_file("world", "earth"))
    assert res["success"] and res["content"] == "hello"

    # 경로 탈출 방지
    bad = run(ws.save_file("world", "../../evil", "x"))
    assert not bad["success"] and "잘못된 경로" in bad["error"]

    # 삭제
    res = run(ws.delete_file("world", "earth"))
    assert res["success"]


def test_char_template_and_profile(tmp_path: Path):
    ws = WorkspaceHandler(workspace_path=str(tmp_path))

    # 템플릿(JSON)
    res = run(ws.save_file("char_template", "mage", json.dumps({"role": "mage"}, ensure_ascii=False)))
    assert res["success"]

    res = run(ws.read_file("char_template", "mage"))
    assert res["success"] and json.loads(res["content"]) == {"role": "mage"}

    # my_profile 단일 파일
    res = run(ws.save_file("my_profile", "ignored", "me"))
    assert res["success"]
    res = run(ws.list_files("my_profile"))
    assert res["success"]
    res = run(ws.read_file("my_profile", "ignored"))
    assert res["success"] and res["content"] == "me"
    res = run(ws.delete_file("my_profile", "ignored"))
    assert res["success"]


def test_config_and_presets(tmp_path: Path):
    ws = WorkspaceHandler(workspace_path=str(tmp_path))

    # config
    res = run(ws.load_config())
    assert res["success"] and res["config"] == {}
    assert run(ws.save_config({"a": 1}))["success"]
    res = run(ws.load_config())
    assert res["success"] and res["config"]["a"] == 1

    # presets
    data = {"x": 2}
    assert run(ws.save_preset("first", data))["success"]
    res = run(ws.list_presets())
    assert res["success"] and any(f["filename"] == "first.json" for f in res["files"])  # type: ignore[index]
    res = run(ws.load_preset("first"))
    assert res["success"] and res["preset"] == data
    assert run(ws.delete_preset("first"))["success"]


import asyncio
from pathlib import Path

from server.handlers.file_handler import FileHandler


def run(coro):
    return asyncio.run(coro)


def test_list_read_write_delete(tmp_path: Path):
    base = tmp_path / "stories"
    base.mkdir()
    fh = FileHandler(base_path=str(base))

    # 초기 목록(빈)
    res = run(fh.list_files())
    assert res["success"] and res["files"] == []

    # 쓰기/읽기
    assert run(fh.write_file("a/b.md", "hello"))["success"]
    res = run(fh.read_file("a/b.md"))
    assert res["success"] and res["content"] == "hello"

    # 목록(재귀 rglob)
    res = run(fh.list_files())
    assert any(x["name"] == "b.md" for x in res["files"])  # type: ignore[index]

    # 경로 탈출 방지
    bad = run(fh.write_file("../../secret.md", "x"))
    assert not bad["success"] and "잘못된 경로" in bad["error"]

    # 존재하지 않는 base 디렉터리 처리
    fh2 = FileHandler(base_path=str(tmp_path / "missing"))
    res = run(fh2.list_files())
    assert not res["success"] and "STORIES 디렉토리가 없습니다" in res["error"]

    # read_file: 존재하지 않는 파일
    res = run(fh.read_file("nope.md"))
    assert not res["success"] and "파일이 존재하지 않습니다" in res["error"]

    # read_file: 링크를 통한 외부 접근 차단
    outside = tmp_path / "outside.md"
    outside.write_text("OUT", encoding="utf-8")
    link = base / "link.md"
    link.symlink_to(outside)
    res = run(fh.read_file("link.md"))
    assert not res["success"] and "잘못된 경로" in res["error"]

import aiofiles
import pytest

from server.handlers.file_handler import FileHandler


@pytest.mark.asyncio
async def test_file_handler_list_read_write(tmp_path):
    base = tmp_path / "STORIES"
    # create nested file structure
    (base / "sub").mkdir(parents=True)
    f1 = base / "hello.md"
    f2 = base / "sub" / "nested.md"
    async with aiofiles.open(f1, "w", encoding="utf-8") as f:
        await f.write("hi")
    async with aiofiles.open(f2, "w", encoding="utf-8") as f:
        await f.write("nested")

    fh = FileHandler(str(base))

    res = await fh.list_files()
    assert res["success"] is True
    paths = {it["path"] for it in res["files"]}
    assert "hello.md" in paths
    assert "sub/nested.md" in paths

    # read file
    r = await fh.read_file("hello.md")
    assert r["success"] is True
    assert r["content"] == "hi"

    # read non-existent
    r2 = await fh.read_file("nope.md")
    assert r2["success"] is False

    # path traversal attempt
    r3 = await fh.read_file("../etc/passwd")
    assert r3["success"] is False

    # write a new file
    w = await fh.write_file("newdir/out.md", "content")
    assert w["success"] is True
    # ensure file exists
    r4 = await fh.read_file("newdir/out.md")
    assert r4["success"] is True and r4["content"] == "content"

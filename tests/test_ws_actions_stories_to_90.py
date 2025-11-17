import json

import pytest

from server.core.app_context import AppContext
from server.ws.actions import stories


class FakeWS:
    def __init__(self):
        self.sent = []

    async def send(self, msg):
        self.sent.append(msg)


def make_ctx(tmp_path):
    ctx = AppContext(
        project_root=tmp_path,
        bind_host="127.0.0.1",
        login_required=False,
        jwt_secret="s",
        jwt_algorithm="HS256",
        access_ttl_seconds=60,
        refresh_ttl_seconds=120,
        login_username="",
        login_rate_limit_max_attempts=5,
        login_rate_limit_window_seconds=900,
        token_expired_grace_seconds=60,
    )
    return ctx


@pytest.mark.asyncio
async def test_list_stories(tmp_path):
    """Test list_stories to cover line 27"""
    ctx = make_ctx(tmp_path)
    ws = FakeWS()

    await stories.list_stories(ctx, ws, {})

    # Check response
    out = json.loads(ws.sent[-1])
    assert out["action"] == "list_stories"
    assert out["data"]["success"] is True
    assert out["data"]["files"] == []


@pytest.mark.asyncio
async def test_save_story(tmp_path):
    """Test save_story to cover line 38"""
    ctx = make_ctx(tmp_path)
    ws = FakeWS()

    await stories.save_story(ctx, ws, {})

    # Check response
    out = json.loads(ws.sent[-1])
    assert out["action"] == "save_story"
    assert out["data"]["success"] is False
    assert out["data"]["error"] == "stories 기능이 비활성화되었습니다"


@pytest.mark.asyncio
async def test_load_story(tmp_path):
    """Test load_story to cover line 49"""
    ctx = make_ctx(tmp_path)
    ws = FakeWS()

    await stories.load_story(ctx, ws, {})

    # Check response
    out = json.loads(ws.sent[-1])
    assert out["action"] == "load_story"
    assert out["data"]["success"] is False
    assert out["data"]["error"] == "stories 기능이 비활성화되었습니다"

from __future__ import annotations

import json

from server.core.app_context import AppContext


async def list_stories(ctx: AppContext, websocket, data: dict):
    # stories 기능은 제거됨 — 호환을 위해 빈 목록 반환
    await websocket.send(
        json.dumps({"action": "list_stories", "data": {"success": True, "files": []}})
    )


async def save_story(ctx: AppContext, websocket, data: dict):
    await websocket.send(
        json.dumps(
            {
                "action": "save_story",
                "data": {"success": False, "error": "stories 기능이 비활성화되었습니다"},
            }
        )
    )


async def load_story(ctx: AppContext, websocket, data: dict):
    await websocket.send(
        json.dumps(
            {
                "action": "load_story",
                "data": {"success": False, "error": "stories 기능이 비활성화되었습니다"},
            }
        )
    )


async def delete_story(ctx: AppContext, websocket, data: dict):
    await websocket.send(
        json.dumps(
            {
                "action": "delete_story",
                "data": {"success": False, "error": "stories 기능이 비활성화되었습니다"},
            }
        )
    )


async def resume_from_story(ctx: AppContext, websocket, data: dict):
    await websocket.send(
        json.dumps(
            {
                "action": "resume_from_story",
                "data": {
                    "success": False,
                    "error": "stories 기반 이어하기는 더 이상 지원되지 않습니다",
                },
            }
        )
    )

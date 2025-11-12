"""WebSocket 액션 라우터(스켈레톤)

우선 쉬운 액션들(files/rooms/presets/history)을 이 라우터를 통해 처리합니다.
등록되지 않은 액션은 False를 반환하여 기존 핸들러로 폴백됩니다.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from server.core.app_context import AppContext

from .actions import files as files_actions
from .actions import history as history_actions
from .actions import presets as presets_actions
from .actions import rooms as rooms_actions

Handler = Callable[[AppContext, object, dict], Awaitable[None]]


ACTION_TABLE: dict[str, Handler] = {
    # workspace files
    "list_workspace_files": files_actions.list_workspace_files,
    "load_workspace_file": files_actions.load_workspace_file,
    "save_workspace_file": files_actions.save_workspace_file,
    "delete_workspace_file": files_actions.delete_workspace_file,
    # presets
    "list_presets": presets_actions.list_presets,
    "save_preset": presets_actions.save_preset,
    "load_preset": presets_actions.load_preset,
    "delete_preset": presets_actions.delete_preset,
    # rooms
    "room_list": rooms_actions.room_list,
    "room_save": rooms_actions.room_save,
    "room_load": rooms_actions.room_load,
    "room_delete": rooms_actions.room_delete,
    # history
    "get_narrative": history_actions.get_narrative,
    "get_history_settings": history_actions.get_history_settings,
    "set_history_limit": history_actions.set_history_limit,
    "clear_history": history_actions.clear_history,
    "get_history_snapshot": history_actions.get_history_snapshot,
    "reset_sessions": history_actions.reset_sessions,
}


async def dispatch(ctx: AppContext | None, websocket, data: dict) -> bool:
    """액션을 라우팅. 처리 시 True, 미등록 시 False."""
    if ctx is None:
        return False
    action = (data or {}).get("action")
    handler = ACTION_TABLE.get(str(action))
    if not handler:
        return False
    await handler(ctx, websocket, data)
    return True

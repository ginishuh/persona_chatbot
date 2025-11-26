"""스트림 취소 액션"""

from __future__ import annotations

import json
import logging
from typing import Any

from server.core.app_context import AppContext

logger = logging.getLogger(__name__)


async def cancel_stream(ctx: AppContext, websocket, data: dict[str, Any]):
    """스트리밍 응답 취소 요청

    클라이언트에서 중단 버튼을 누르면 호출됩니다.
    cancel_flags에 플래그를 설정하여 진행 중인 스트리밍을 중단합니다.
    """
    ctx.cancel_flags[websocket] = True
    logger.info("Stream cancellation requested")
    await websocket.send(json.dumps({"action": "cancel_stream", "data": {"success": True}}))

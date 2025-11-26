"""애플리케이션 공용 컨텍스트

핸들러/유틸 사이의 의존성을 깔끔히 주입하기 위한 컨텍스트 객체입니다.
프로세스 수명 동안 1개 인스턴스를 생성해 공유합니다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AppContext:
    # 경로/환경
    project_root: Path
    bind_host: str

    # 인증/로그인 설정
    login_required: bool
    jwt_secret: str
    jwt_algorithm: str
    access_ttl_seconds: int
    refresh_ttl_seconds: int
    login_username: str
    login_rate_limit_max_attempts: int
    login_rate_limit_window_seconds: int
    token_expired_grace_seconds: int

    # 런타임 상태
    connected_clients: set = field(default_factory=set)
    login_attempts: dict = field(default_factory=dict)
    websocket_to_session: dict = field(default_factory=dict)
    sessions: dict = field(default_factory=dict)
    cancel_flags: dict = field(default_factory=dict)  # websocket -> bool (스트림 취소 플래그)

    # 핸들러/서비스
    file_handler: Any | None = None
    git_handler: Any | None = None
    claude_handler: Any | None = None
    droid_handler: Any | None = None
    gemini_handler: Any | None = None
    context_handler: Any | None = None
    workspace_handler: Any | None = None
    mode_handler: Any | None = None
    token_usage_handler: Any | None = None
    db_handler: Any | None = None

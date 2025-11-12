# ruff: noqa: E402
from __future__ import annotations

"""HTTP 서버 (정적 파일 + SPA fallback + Export)

History API 라우팅을 지원하기 위해 존재하지 않는 경로를 index.html로 반환합니다.
Export는 초기 단계에서 메모리 세션 스냅샷 기반 JSON 다운로드를 제공합니다.
"""

import json
import os
from datetime import datetime
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from urllib.parse import parse_qs, urlparse

from server.core.app_context import AppContext


def run_http_server(ctx: AppContext):
    import logging

    logger = logging.getLogger(__name__)

    # 정적 파일 위치(web/)
    web_dir = (
        os.path.join(ctx.project_root, "web")
        if isinstance(ctx.project_root, str)
        else os.path.join(str(ctx.project_root), "web")
    )
    os.chdir(web_dir)

    app_config = {
        "ws_url": os.getenv("APP_PUBLIC_WS_URL", ""),
        "ws_port": int(os.getenv("WS_PORT", "8765")),
        "login_required": ctx.login_required,
        "show_token_usage": bool(int(os.getenv("SHOW_TOKEN_USAGE", "1"))),
    }

    class CustomHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            logger.info(f"HTTP: {format % args}")

        def do_GET(self):
            # 앱 설정
            if self.path == "/app-config.json":
                payload = json.dumps(app_config).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return

            # Export 다운로드(API)
            if self.path.startswith("/api/export"):
                try:
                    url = urlparse(self.path)
                    qs = parse_qs(url.query)
                    scope = (qs.get("scope", ["single"]))[0]
                    room_id = (qs.get("room_id", ["default"]))[0]

                    export_obj = {
                        "version": "1.0",
                        "export_type": scope,
                        "exported_at": datetime.utcnow().isoformat() + "Z",
                    }

                    def room_snapshot(rid: str) -> dict:
                        for sess in ctx.sessions.values():
                            room = sess.get("rooms", {}).get(rid)
                            if room:
                                hist = room.get("history")
                                messages = []
                                if hist:
                                    for m in getattr(hist, "full_history", []):
                                        messages.append(
                                            {
                                                "role": m.get("role"),
                                                "content": m.get("content"),
                                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                            }
                                        )
                                return {"room_id": rid, "title": rid, "messages": messages}
                        return {"room_id": rid, "title": rid, "messages": []}

                    if scope == "single":
                        export_obj["rooms"] = [room_snapshot(room_id)]
                    elif scope == "selected":
                        room_ids = (
                            (qs.get("room_ids", [""]))[0].split(",")
                            if qs.get("room_ids")
                            else [room_id]
                        )
                        export_obj["rooms"] = [
                            room_snapshot(r.strip() or "default") for r in room_ids
                        ]
                    else:  # full
                        seen = set()
                        rooms_acc = []
                        for sess in ctx.sessions.values():
                            for rid in sess.get("rooms", {}).keys():
                                if rid in seen:
                                    continue
                                seen.add(rid)
                                rooms_acc.append(room_snapshot(rid))
                        export_obj["rooms"] = rooms_acc

                    payload = json.dumps(export_obj, ensure_ascii=False).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header(
                        "Content-Disposition",
                        f"attachment; filename=backup_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json",
                    )
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as e:
                    body = json.dumps({"success": False, "error": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                return

            # 정적 파일 시도 → 실패 시 SPA fallback
            try:
                return super().do_GET()
            except Exception:
                pass
            try:
                with open("index.html", "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            except FileNotFoundError:
                return super().do_GET()

    http_port = int(os.getenv("HTTP_PORT", "9000"))
    with TCPServer((ctx.bind_host, http_port), CustomHandler) as httpd:
        logger.info(f"HTTP server started on port {http_port}")
        httpd.serve_forever()

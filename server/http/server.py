# ruff: noqa: E402
from __future__ import annotations

"""HTTP 서버 (정적 파일 + SPA fallback + Export)

History API 라우팅을 지원하기 위해 존재하지 않는 경로를 index.html로 반환합니다.
Export는 초기 단계에서 메모리 세션 스냅샷 기반 JSON 다운로드를 제공합니다.
"""

import asyncio
import io
import json
import os
import zipfile
from datetime import datetime
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from urllib.parse import parse_qs, urlparse

from server.core.app_context import AppContext
from server.core.auth import verify_token as auth_verify_token


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

        def _parse_bool(self, v: str | None, default: bool = False) -> bool:
            if v is None:
                return default
            return v.lower() in {"1", "true", "yes", "on"}

        def _parse_date(self, v: str | None, end: bool = False) -> str | None:
            if not v:
                return None
            try:
                if "T" in v:
                    return v.replace("T", " ")[:19]
                return f"{v} 23:59:59" if end else f"{v} 00:00:00"
            except Exception:
                return None

        def _ok_json(self, obj: dict, filename: str | None = None):
            payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            if filename:
                self.send_header("Content-Disposition", f"attachment; filename={filename}")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _ok_zip(self, content_bytes: bytes, filename: str):
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Disposition", f"attachment; filename={filename}")
            self.send_header("Content-Length", str(len(content_bytes)))
            self.end_headers()
            self.wfile.write(content_bytes)

        def _write_ndjson_line(self, obj: dict):
            try:
                line = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
                self.wfile.write(line)
            except Exception:
                # best-effort streaming; ignore downstream disconnects
                pass

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
                    fmt = (qs.get("format", ["json"]))[0].lower()  # json | zip
                    includes = set((qs.get("include", ["messages,context"]))[0].split(","))
                    start = self._parse_date((qs.get("start", [None]))[0], end=False)
                    end = self._parse_date((qs.get("end", [None]))[0], end=True)

                    # 인증: 로그인 환경에서는 JWT 필요
                    if ctx.login_required:
                        token = None
                        authz = self.headers.get("Authorization")
                        if authz and authz.lower().startswith("bearer "):
                            token = authz.split(" ", 1)[1].strip()
                        if not token:
                            token = (qs.get("token", [None]))[0]
                        _, err = auth_verify_token(ctx, token, expected_type="access")
                        if err:
                            body = json.dumps(
                                {"success": False, "error": f"unauthorized: {err}"}
                            ).encode("utf-8")
                            self.send_response(401)
                            self.send_header("Content-Type", "application/json")
                            self.send_header("Content-Length", str(len(body)))
                            self.end_headers()
                            self.wfile.write(body)
                            return

                    export_obj = {
                        "version": "1.0",
                        "export_type": scope,
                        "exported_at": datetime.utcnow().isoformat() + "Z",
                    }

                    def room_snapshot(rid: str) -> dict:
                        # DB 우선: 다른 스레드의 이벤트 루프에서 실행
                        try:
                            if ctx.db_handler and getattr(ctx, "loop", None):
                                msgs = None
                                if "messages" in includes:
                                    fut = asyncio.run_coroutine_threadsafe(
                                        ctx.db_handler.list_messages_range(
                                            rid, start=start, end=end
                                        ),
                                        ctx.loop,
                                    )
                                    msgs = fut.result(timeout=5)
                                base = {"room_id": rid, "title": rid}
                                if msgs:
                                    return {
                                        **base,
                                        "messages": [
                                            {
                                                "role": m.get("role"),
                                                "content": m.get("content"),
                                                "timestamp": str(m.get("timestamp")),
                                            }
                                            for m in msgs
                                        ],
                                        **(
                                            {
                                                "token_usage": asyncio.run_coroutine_threadsafe(
                                                    ctx.db_handler.list_token_usage_range(
                                                        rid, start=start, end=end
                                                    ),
                                                    ctx.loop,
                                                ).result(timeout=5)
                                            }
                                            if "token_usage" in includes
                                            else {}
                                        ),
                                        **(
                                            {
                                                "context": json.loads(
                                                    asyncio.run_coroutine_threadsafe(
                                                        ctx.db_handler.get_room(rid), ctx.loop
                                                    )
                                                    .result(timeout=5)
                                                    .get("context")
                                                    or "{}"
                                                )
                                            }
                                            if "context" in includes
                                            else {}
                                        ),
                                    }
                        except Exception:
                            pass

                        # 폴백: 메모리 세션
                        for sess in ctx.sessions.values():
                            room = sess.get("rooms", {}).get(rid)
                            if room:
                                hist = room.get("history")
                                messages = []
                                if hist and "messages" in includes:
                                    for m in getattr(hist, "full_history", []):
                                        messages.append(
                                            {
                                                "role": m.get("role"),
                                                "content": m.get("content"),
                                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                            }
                                        )
                                base = {"room_id": rid, "title": rid}
                                if messages:
                                    base["messages"] = messages
                                return base
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
                        try:
                            if ctx.db_handler and getattr(ctx, "loop", None):
                                fut = asyncio.run_coroutine_threadsafe(
                                    ctx.db_handler.list_all_rooms(), ctx.loop
                                )
                                db_rooms = fut.result(timeout=5)
                                for r in db_rooms:
                                    rid = r.get("room_id")
                                    if not rid or rid in seen:
                                        continue
                                    seen.add(rid)
                                    rooms_acc.append(room_snapshot(rid))
                        except Exception:
                            pass
                        # 폴백: 메모리 rooms
                        for sess in ctx.sessions.values():
                            for rid in sess.get("rooms", {}).keys():
                                if rid in seen:
                                    continue
                                seen.add(rid)
                                rooms_acc.append(room_snapshot(rid))
                        export_obj["rooms"] = rooms_acc

                    tsname = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                    if fmt == "zip":
                        buf = io.BytesIO()
                        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                            zf.writestr(
                                f"export_{tsname}.json", json.dumps(export_obj, ensure_ascii=False)
                            )
                        self._ok_zip(buf.getvalue(), f"backup_{tsname}.zip")
                    else:
                        self._ok_json(export_obj, filename=f"backup_{tsname}.json")
                except Exception as e:
                    body = json.dumps({"success": False, "error": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                return

            # Export 스트리밍(API, NDJSON)
            if self.path.startswith("/api/export/stream"):
                try:
                    url = urlparse(self.path)
                    qs = parse_qs(url.query)
                    scope = (qs.get("scope", ["single"]))[0]
                    room_id = (qs.get("room_id", ["default"]))[0]
                    includes = set((qs.get("include", ["messages,context"]))[0].split(","))
                    start = self._parse_date((qs.get("start", [None]))[0], end=False)
                    end = self._parse_date((qs.get("end", [None]))[0], end=True)

                    # 인증
                    if ctx.login_required:
                        token = None
                        authz = self.headers.get("Authorization")
                        if authz and authz.lower().startswith("bearer "):
                            token = authz.split(" ", 1)[1].strip()
                        if not token:
                            token = (qs.get("token", [None]))[0]
                        _, err = auth_verify_token(ctx, token, expected_type="access")
                        if err:
                            body = json.dumps(
                                {"success": False, "error": f"unauthorized: {err}"}
                            ).encode("utf-8")
                            self.send_response(401)
                            self.send_header("Content-Type", "application/json")
                            self.send_header("Content-Length", str(len(body)))
                            self.end_headers()
                            self.wfile.write(body)
                            return

                    tsname = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/x-ndjson")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header(
                        "Content-Disposition", f"attachment; filename=backup_{tsname}.ndjson"
                    )
                    self.end_headers()

                    # meta 헤더 라인
                    self._write_ndjson_line(
                        {
                            "type": "meta",
                            "version": "1.0",
                            "exported_at": datetime.utcnow().isoformat() + "Z",
                            "scope": scope,
                            "include": sorted(list(includes)),
                            **({"start": start} if start else {}),
                            **({"end": end} if end else {}),
                        }
                    )

                    def stream_room(rid: str):
                        # DB 우선
                        try:
                            if ctx.db_handler and getattr(ctx, "loop", None):
                                base = {"room_id": rid}
                                if "context" in includes:
                                    room_row = asyncio.run_coroutine_threadsafe(
                                        ctx.db_handler.get_room(rid), ctx.loop
                                    ).result(timeout=5)
                                    if room_row and room_row.get("context"):
                                        try:
                                            base["context"] = json.loads(room_row["context"])
                                        except Exception:
                                            base["context"] = {}
                                self._write_ndjson_line({"type": "room", **base})

                                # messages
                                if "messages" in includes:
                                    msgs = asyncio.run_coroutine_threadsafe(
                                        ctx.db_handler.list_messages_range(
                                            rid, start=start, end=end
                                        ),
                                        ctx.loop,
                                    ).result(timeout=10)
                                    for m in msgs or []:
                                        self._write_ndjson_line(
                                            {
                                                "type": "message",
                                                "room_id": rid,
                                                "role": m.get("role"),
                                                "content": m.get("content"),
                                                "timestamp": str(m.get("timestamp")),
                                            }
                                        )

                                # token usage
                                if "token_usage" in includes:
                                    usages = asyncio.run_coroutine_threadsafe(
                                        ctx.db_handler.list_token_usage_range(
                                            rid, start=start, end=end
                                        ),
                                        ctx.loop,
                                    ).result(timeout=10)
                                    for u in usages or []:
                                        self._write_ndjson_line(
                                            {
                                                "type": "token_usage",
                                                "room_id": rid,
                                                "session_key": u.get("session_key"),
                                                "provider": u.get("provider"),
                                                "token_info": u.get("token_info"),
                                                "timestamp": str(u.get("timestamp")),
                                            }
                                        )
                                return
                        except Exception:
                            pass

                        # 폴백: 메모리 세션
                        try:
                            for sess in ctx.sessions.values():
                                room = sess.get("rooms", {}).get(rid)
                                if room:
                                    self._write_ndjson_line({"type": "room", "room_id": rid})
                                    if "messages" in includes:
                                        hist = room.get("history")
                                        for m in getattr(hist, "full_history", []) or []:
                                            self._write_ndjson_line(
                                                {
                                                    "type": "message",
                                                    "room_id": rid,
                                                    "role": m.get("role"),
                                                    "content": m.get("content"),
                                                    "timestamp": datetime.utcnow().isoformat()
                                                    + "Z",
                                                }
                                            )
                                    return
                        except Exception:
                            pass

                    # 방 집합 계산 후 스트리밍
                    seen: set[str] = set()
                    if scope == "single":
                        stream_room(room_id)
                        seen.add(room_id)
                    elif scope == "selected":
                        room_ids = (
                            (qs.get("room_ids", [""]))[0].split(",")
                            if qs.get("room_ids")
                            else [room_id]
                        )
                        for r in room_ids:
                            rid = (r or "default").strip()
                            if rid and rid not in seen:
                                stream_room(rid)
                                seen.add(rid)
                    else:  # full
                        # DB 방 우선 스트림
                        try:
                            if ctx.db_handler and getattr(ctx, "loop", None):
                                db_rooms = asyncio.run_coroutine_threadsafe(
                                    ctx.db_handler.list_all_rooms(), ctx.loop
                                ).result(timeout=10)
                                for rr in db_rooms or []:
                                    rid = rr.get("room_id")
                                    if rid and rid not in seen:
                                        stream_room(rid)
                                        seen.add(rid)
                        except Exception:
                            pass
                        # 메모리 폴백
                        for sess in ctx.sessions.values():
                            for rid in sess.get("rooms", {}).keys():
                                if rid not in seen:
                                    stream_room(rid)
                                    seen.add(rid)

                    # 종료 라인
                    self._write_ndjson_line({"type": "end", "rooms": len(seen)})
                except Exception as e:
                    body = json.dumps({"success": False, "error": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                return

            # Export MD (단일 MD 또는 ZIP of MD)
            if self.path.startswith("/api/export/md"):
                try:
                    url = urlparse(self.path)
                    qs = parse_qs(url.query)
                    scope = (qs.get("scope", ["single"]))[0]
                    room_id = (qs.get("room_id", ["default"]))[0]
                    start = self._parse_date((qs.get("start", [None]))[0], end=False)
                    end = self._parse_date((qs.get("end", [None]))[0], end=True)

                    # 인증
                    if ctx.login_required:
                        token = None
                        authz = self.headers.get("Authorization")
                        if authz and authz.lower().startswith("bearer "):
                            token = authz.split(" ", 1)[1].strip()
                        if not token:
                            token = (qs.get("token", [None]))[0]
                        _, err = auth_verify_token(ctx, token, expected_type="access")
                        if err:
                            body = json.dumps(
                                {"success": False, "error": f"unauthorized: {err}"}
                            ).encode("utf-8")
                            self.send_response(401)
                            self.send_header("Content-Type", "application/json")
                            self.send_header("Content-Length", str(len(body)))
                            self.end_headers()
                            self.wfile.write(body)
                            return

                    def render_md(rid: str) -> tuple[str, bytes]:
                        title = rid
                        msgs = []
                        # DB 우선
                        try:
                            if ctx.db_handler and getattr(ctx, "loop", None):
                                row = asyncio.run_coroutine_threadsafe(
                                    ctx.db_handler.get_room(rid), ctx.loop
                                ).result(timeout=5)
                                if row and row.get("title"):
                                    title = row.get("title")
                                msgs = asyncio.run_coroutine_threadsafe(
                                    ctx.db_handler.list_messages_range(rid, start=start, end=end),
                                    ctx.loop,
                                ).result(timeout=10)
                        except Exception:
                            pass

                        # 폴백: 메모리 세션
                        if not msgs:
                            for sess in ctx.sessions.values():
                                room = sess.get("rooms", {}).get(rid)
                                if room:
                                    try:
                                        msgs = room["history"].get_history()
                                        break
                                    except Exception:
                                        pass

                        lines = [f"# {title}", ""]
                        for m in msgs or []:
                            role = (m.get("role") or "assistant").lower()
                            lines.append("## 사용자" if role == "user" else "## AI 응답")
                            lines.append(m.get("content", ""))
                            lines.append("")
                        return title, "\n".join(lines).encode("utf-8")

                    tsname = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                    if scope == "single":
                        title, md_bytes = render_md(room_id)
                        fname = f"{title or room_id}_{tsname}.md".replace("/", "_")
                        self.send_response(200)
                        self.send_header("Content-Type", "text/markdown; charset=utf-8")
                        self.send_header("Cache-Control", "no-store")
                        self.send_header("Content-Disposition", f"attachment; filename={fname}")
                        self.send_header("Content-Length", str(len(md_bytes)))
                        self.end_headers()
                        self.wfile.write(md_bytes)
                        return

                    # selected/full → ZIP 묶음
                    room_ids = []
                    if scope == "selected":
                        room_ids = (
                            (qs.get("room_ids", [""]))[0].split(",")
                            if qs.get("room_ids")
                            else [room_id]
                        )
                    else:  # full
                        seen = set()
                        try:
                            if ctx.db_handler and getattr(ctx, "loop", None):
                                db_rooms = asyncio.run_coroutine_threadsafe(
                                    ctx.db_handler.list_all_rooms(), ctx.loop
                                ).result(timeout=10)
                                for r in db_rooms or []:
                                    rid = r.get("room_id")
                                    if rid and rid not in seen:
                                        seen.add(rid)
                                        room_ids.append(rid)
                        except Exception:
                            pass
                        for sess in ctx.sessions.values():
                            for rid in sess.get("rooms", {}).keys():
                                if rid not in seen:
                                    seen.add(rid)
                                    room_ids.append(rid)

                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                        for rid in room_ids:
                            try:
                                title, md_bytes = render_md((rid or "default").strip())
                                zf.writestr(
                                    f"{title or rid}_{tsname}.md".replace("/", "_"), md_bytes
                                )
                            except Exception:
                                continue
                    content = buf.getvalue()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/zip")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header(
                        "Content-Disposition", f"attachment; filename=md_export_{tsname}.zip"
                    )
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                except Exception as e:
                    body = json.dumps({"success": False, "error": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                return

            # 정적 파일 시도 → 실패 시 SPA fallback
            # URL 경로를 파일 경로로 변환 (쿼리 파라미터 제거)
            path = self.path.split("?")[0]
            if path.startswith("/"):
                path = path[1:]  # 앞의 / 제거
            if not path:
                path = "index.html"

            # 파일이 존재하는지 확인
            file_path = os.path.join(os.getcwd(), path)
            if os.path.isfile(file_path):
                # 실제 파일이 존재하면 정상 처리
                return super().do_GET()

            # 파일이 없으면 SPA fallback (index.html 반환)
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
                # index.html도 없으면 404
                return super().do_GET()

        def do_POST(self):
            """POST 요청 처리 (Import API)"""
            # Import API
            if self.path.startswith("/api/import"):
                try:
                    # Content-Length 파싱
                    content_length = int(self.headers.get("Content-Length", 0))
                    if content_length > 100 * 1024 * 1024:  # 100MB 제한
                        self.send_response(413)  # Payload Too Large
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {"success": False, "error": "파일이 너무 큽니다 (최대 100MB)"}
                            ).encode()
                        )
                        return

                    # Content-Type 확인
                    content_type = self.headers.get("Content-Type", "")

                    # JSON 직접 업로드
                    if "application/json" in content_type:
                        # JSON 데이터 읽기
                        body = self.rfile.read(content_length)
                        request_data = json.loads(body.decode("utf-8"))

                        # Import 파라미터 추출
                        duplicate_policy = request_data.get("duplicate_policy", "skip")
                        target_room_id = request_data.get("target_room_id")
                        json_data = request_data.get("json_data", {})

                        # Import 로직 실행 (동기 래퍼 필요)
                        import asyncio

                        from server.ws.actions.importer import _import_single_room

                        # 세션 키 생성 또는 추출
                        session_key = request_data.get("session_key", "http_import")

                        # 비동기 import 실행
                        async def run_import():
                            exported_type = json_data.get("export_type", "").lower()
                            new_room_ids = []
                            messages_imported = 0

                            if exported_type == "single_room":
                                room = json_data.get("room", {})
                                rid, cnt = await _import_single_room(
                                    ctx,
                                    session_key,
                                    room,
                                    target_room_id=target_room_id,
                                    duplicate_policy=duplicate_policy,
                                )
                                new_room_ids.append(rid)
                                messages_imported += cnt
                            elif exported_type in {"full_backup", "selected"}:
                                rooms = json_data.get("rooms", [])
                                for r in rooms:
                                    rid, cnt = await _import_single_room(
                                        ctx,
                                        session_key,
                                        r,
                                        target_room_id=None,
                                        duplicate_policy=duplicate_policy,
                                    )
                                    new_room_ids.append(rid)
                                    messages_imported += cnt
                            else:
                                # 포맷이 명시되지 않은 경우
                                room = json_data.get("room") or json_data
                                rid, cnt = await _import_single_room(
                                    ctx,
                                    session_key,
                                    room,
                                    target_room_id=target_room_id,
                                    duplicate_policy=duplicate_policy,
                                )
                                new_room_ids.append(rid)
                                messages_imported += cnt

                            return {
                                "success": True,
                                "rooms_imported": len(new_room_ids),
                                "messages_imported": messages_imported,
                                "new_room_ids": new_room_ids,
                            }

                        # 이벤트 루프에서 실행
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(run_import())
                        loop.close()

                        # 성공 응답
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        response_data = json.dumps(result, ensure_ascii=False).encode("utf-8")
                        self.send_header("Content-Length", str(len(response_data)))
                        self.end_headers()
                        self.wfile.write(response_data)
                        return

                    else:
                        # 지원하지 않는 Content-Type
                        self.send_response(415)  # Unsupported Media Type
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {
                                    "success": False,
                                    "error": f"지원하지 않는 Content-Type: {content_type}. application/json을 사용하세요.",
                                }
                            ).encode()
                        )
                        return

                except json.JSONDecodeError as e:
                    self.send_response(400)  # Bad Request
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps(
                            {"success": False, "error": f"JSON 파싱 실패: {str(e)}"}
                        ).encode()
                    )
                    return
                except Exception as e:
                    logger.exception("Import API error")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())
                    return

            # 다른 POST 요청은 405
            self.send_response(405)  # Method Not Allowed
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": "Method not allowed"}).encode())

    http_port = int(os.getenv("HTTP_PORT", "9000"))
    with TCPServer((ctx.bind_host, http_port), CustomHandler) as httpd:
        logger.info(f"HTTP server started on port {http_port}")
        httpd.serve_forever()

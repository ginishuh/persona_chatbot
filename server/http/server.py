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
                    user_id = None  # JWT에서 추출한 user_id (사용자별 데이터 격리)
                    if ctx.login_required:
                        token = None
                        authz = self.headers.get("Authorization")
                        if authz and authz.lower().startswith("bearer "):
                            token = authz.split(" ", 1)[1].strip()
                        if not token:
                            token = (qs.get("token", [None]))[0]
                        payload, err = auth_verify_token(ctx, token, expected_type="access")
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
                        # JWT payload에서 user_id 추출
                        if payload:
                            user_id = payload.get("user_id")
                        if not user_id:
                            body = json.dumps(
                                {"success": False, "error": "user_id not found in token"}
                            ).encode("utf-8")
                            self.send_response(401)
                            self.send_header("Content-Type", "application/json")
                            self.send_header("Content-Length", str(len(body)))
                            self.end_headers()
                            self.wfile.write(body)
                            return
                    else:
                        # 비로그인 모드는 더 이상 지원하지 않음
                        body = json.dumps({"success": False, "error": "login required"}).encode(
                            "utf-8"
                        )
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
                                # 먼저 room 소유권 확인 (user_id로 격리)
                                room_row = asyncio.run_coroutine_threadsafe(
                                    ctx.db_handler.get_room(rid, user_id), ctx.loop
                                ).result(timeout=5)

                                # room이 현재 user_id에 속하지 않으면 빈 결과 반환
                                if not room_row:
                                    return {"room_id": rid, "title": rid, "messages": []}

                                base = {
                                    "room_id": rid,
                                    "title": room_row.get("title", rid),
                                }

                                # room 소유권 확인 후 messages 가져오기
                                if "messages" in includes:
                                    msgs = asyncio.run_coroutine_threadsafe(
                                        ctx.db_handler.list_messages_range(
                                            rid, user_id=user_id, start=start, end=end
                                        ),
                                        ctx.loop,
                                    ).result(timeout=5)
                                    if msgs:
                                        base["messages"] = [
                                            {
                                                "role": m.get("role"),
                                                "content": m.get("content"),
                                                "timestamp": str(m.get("timestamp")),
                                            }
                                            for m in msgs
                                        ]

                                # token_usage
                                if "token_usage" in includes:
                                    usage = asyncio.run_coroutine_threadsafe(
                                        ctx.db_handler.list_token_usage_range(
                                            rid, user_id=user_id, start=start, end=end
                                        ),
                                        ctx.loop,
                                    ).result(timeout=5)
                                    if usage:
                                        base["token_usage"] = usage

                                # context
                                if "context" in includes and room_row.get("context"):
                                    try:
                                        base["context"] = json.loads(room_row["context"])
                                    except Exception:
                                        pass

                                return base
                        except Exception:
                            # DB 조회 실패 시 빈 결과 반환 (user_id 기반 시스템)
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
                    user_id = None
                    if ctx.login_required:
                        token = None
                        authz = self.headers.get("Authorization")
                        if authz and authz.lower().startswith("bearer "):
                            token = authz.split(" ", 1)[1].strip()
                        if not token:
                            token = (qs.get("token", [None]))[0]
                        payload, err = auth_verify_token(ctx, token, expected_type="access")
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
                        # JWT payload에서 user_id 추출
                        if payload:
                            user_id = payload.get("user_id")
                        if not user_id:
                            body = json.dumps(
                                {"success": False, "error": "user_id not found in token"}
                            ).encode("utf-8")
                            self.send_response(401)
                            self.send_header("Content-Type", "application/json")
                            self.send_header("Content-Length", str(len(body)))
                            self.end_headers()
                            self.wfile.write(body)
                            return
                    else:
                        # 비로그인 모드는 더 이상 지원하지 않음
                        body = json.dumps({"success": False, "error": "login required"}).encode(
                            "utf-8"
                        )
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
                                # 먼저 room 소유권 확인 (user_id로 격리)
                                room_row = asyncio.run_coroutine_threadsafe(
                                    ctx.db_handler.get_room(rid, user_id), ctx.loop
                                ).result(timeout=5)

                                # room이 현재 user_id에 속하지 않으면 스킵
                                if not room_row:
                                    return

                                base = {"room_id": rid}
                                if "context" in includes and room_row.get("context"):
                                    try:
                                        base["context"] = json.loads(room_row["context"])
                                    except Exception:
                                        base["context"] = {}
                                self._write_ndjson_line({"type": "room", **base})

                                # room 소유권 확인 후 messages 가져오기
                                if "messages" in includes:
                                    msgs = asyncio.run_coroutine_threadsafe(
                                        ctx.db_handler.list_messages_range(
                                            rid, user_id=user_id, start=start, end=end
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
                                            rid, user_id=user_id, start=start, end=end
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
                            # DB 조회 실패 시 스킵 (user_id 기반 시스템)
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
                    user_id = None  # JWT에서 추출한 user_id (사용자별 데이터 격리)
                    if ctx.login_required:
                        token = None
                        authz = self.headers.get("Authorization")
                        if authz and authz.lower().startswith("bearer "):
                            token = authz.split(" ", 1)[1].strip()
                        if not token:
                            token = (qs.get("token", [None]))[0]
                        payload, err = auth_verify_token(ctx, token, expected_type="access")
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
                        # JWT payload에서 user_id 추출
                        if payload:
                            user_id = payload.get("user_id")
                        if not user_id:
                            body = json.dumps(
                                {"success": False, "error": "user_id not found in token"}
                            ).encode("utf-8")
                            self.send_response(401)
                            self.send_header("Content-Type", "application/json")
                            self.send_header("Content-Length", str(len(body)))
                            self.end_headers()
                            self.wfile.write(body)
                            return
                    else:
                        # 비로그인 모드는 더 이상 지원하지 않음
                        body = json.dumps({"success": False, "error": "login required"}).encode(
                            "utf-8"
                        )
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
                                # 먼저 room 소유권 확인 (user_id로 격리)
                                row = asyncio.run_coroutine_threadsafe(
                                    ctx.db_handler.get_room(rid, user_id), ctx.loop
                                ).result(timeout=5)

                                # room이 현재 user_id에 속할 때만 메시지 가져오기
                                if row:
                                    if row.get("title"):
                                        title = row.get("title")
                                    msgs = asyncio.run_coroutine_threadsafe(
                                        ctx.db_handler.list_messages_range(
                                            rid, user_id=user_id, start=start, end=end
                                        ),
                                        ctx.loop,
                                    ).result(timeout=10)
                        except Exception:
                            pass

                        # 폴백: 메모리 세션 (user_id로 격리)
                        if not msgs:
                            if user_id:
                                # user_id가 일치하는 세션만 검색
                                target_sess = ctx.sessions.get(user_id)
                                if target_sess:
                                    room = target_sess.get("rooms", {}).get(rid)
                                    if room:
                                        try:
                                            msgs = room["history"].get_history()
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
            """POST 요청 처리 (Import API, 회원가입, 로그인)"""
            # 회원가입 API
            if self.path == "/api/register":
                try:
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length)
                    data = json.loads(body.decode("utf-8"))

                    username = data.get("username", "").strip()
                    email = data.get("email", "").strip()
                    password = data.get("password", "")

                    # 입력 검증
                    if not username or not email or not password:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {
                                    "success": False,
                                    "error": "username, email, password는 필수입니다",
                                }
                            ).encode("utf-8")
                        )
                        return

                    # 비밀번호 해싱
                    import bcrypt

                    password_hash = bcrypt.hashpw(
                        password.encode("utf-8"), bcrypt.gensalt()
                    ).decode("utf-8")

                    # DB에 사용자 생성 (비동기)
                    import asyncio

                    if not ctx.db_handler or not ctx.loop:
                        raise RuntimeError("DB handler or event loop not available")

                    future = asyncio.run_coroutine_threadsafe(
                        ctx.db_handler.create_user(username, email, password_hash), ctx.loop
                    )
                    user_id = future.result(timeout=5)

                    if user_id is None:
                        # 중복 사용자명 또는 이메일
                        self.send_response(409)  # Conflict
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {
                                    "success": False,
                                    "error": "사용자명 또는 이메일이 이미 존재합니다",
                                }
                            ).encode("utf-8")
                        )
                        return

                    # 성공
                    self.send_response(201)  # Created
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    response_data = json.dumps(
                        {"success": True, "user_id": user_id, "username": username}
                    ).encode("utf-8")
                    self.send_header("Content-Length", str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data)
                    return

                except json.JSONDecodeError as e:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"success": False, "error": f"JSON 파싱 실패: {str(e)}"}).encode(
                            "utf-8"
                        )
                    )
                    return
                except Exception as e:
                    logger.exception("Register API error")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"success": False, "error": str(e)}).encode("utf-8")
                    )
                    return

            # 로그인 API
            if self.path == "/api/login":
                try:
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length)
                    data = json.loads(body.decode("utf-8"))

                    username = data.get("username", "").strip()
                    password = data.get("password", "")

                    # 입력 검증
                    if not username or not password:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {"success": False, "error": "username과 password는 필수입니다"}
                            ).encode("utf-8")
                        )
                        return

                    # DB에서 사용자 조회 (비동기)
                    import asyncio

                    if not ctx.db_handler or not ctx.loop:
                        raise RuntimeError("DB handler or event loop not available")

                    future = asyncio.run_coroutine_threadsafe(
                        ctx.db_handler.get_user_by_username(username), ctx.loop
                    )
                    user = future.result(timeout=5)

                    if not user:
                        # 사용자 없음
                        self.send_response(401)  # Unauthorized
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {
                                    "success": False,
                                    "error": "사용자명 또는 비밀번호가 올바르지 않습니다",
                                }
                            ).encode("utf-8")
                        )
                        return

                    # 비밀번호 검증
                    import bcrypt

                    password_hash = user.get("password_hash", "")
                    if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
                        # 비밀번호 불일치
                        self.send_response(401)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {
                                    "success": False,
                                    "error": "사용자명 또는 비밀번호가 올바르지 않습니다",
                                }
                            ).encode("utf-8")
                        )
                        return

                    # 승인 여부 확인
                    is_approved = user.get("is_approved", 0)
                    if not is_approved:
                        # 승인 대기 중
                        self.send_response(403)  # Forbidden
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {
                                    "success": False,
                                    "error": "관리자 승인이 필요합니다. 승인 후 다시 로그인해주세요.",
                                }
                            ).encode("utf-8")
                        )
                        return

                    # 로그인 성공 → JWT 발급
                    user_id = user.get("user_id")
                    session_key = f"user:{username}"

                    # JWT 발급 함수 import
                    from server.websocket_server import issue_access_token, issue_refresh_token

                    access_token, access_exp = issue_access_token(session_key, user_id)
                    refresh_token, refresh_exp = issue_refresh_token(session_key, user_id)

                    # last_login 업데이트 (비동기)
                    asyncio.run_coroutine_threadsafe(
                        ctx.db_handler.update_user_last_login(user_id), ctx.loop
                    )
                    # user_id 기반 시스템에서는 sessions 테이블이 없음 (메모리에서만 관리)

                    # 성공 응답
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    response_data = json.dumps(
                        {
                            "success": True,
                            "user_id": user_id,
                            "username": username,
                            "role": user.get("role", "user"),
                            "access_token": access_token,
                            "access_exp": access_exp,
                            "refresh_token": refresh_token,
                            "refresh_exp": refresh_exp,
                        }
                    ).encode("utf-8")
                    self.send_header("Content-Length", str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data)
                    return

                except json.JSONDecodeError as e:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"success": False, "error": f"JSON 파싱 실패: {str(e)}"}).encode(
                            "utf-8"
                        )
                    )
                    return
                except Exception as e:
                    logger.exception("Login API error")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"success": False, "error": str(e)}).encode("utf-8")
                    )
                    return

            # Admin API: 승인 대기 목록 조회
            if self.path == "/api/admin/pending-users":
                try:
                    # JWT 인증
                    token = None
                    authz = self.headers.get("Authorization")
                    if authz and authz.lower().startswith("bearer "):
                        token = authz.split(" ", 1)[1].strip()

                    payload, err = auth_verify_token(ctx, token, expected_type="access")
                    if err:
                        self.send_response(401)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"success": False, "error": f"인증 실패: {err}"}).encode(
                                "utf-8"
                            )
                        )
                        return

                    # 관리자 권한 확인
                    user_id = payload.get("user_id") if payload else None
                    if not user_id:
                        self.send_response(401)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"success": False, "error": "유효하지 않은 토큰"}).encode(
                                "utf-8"
                            )
                        )
                        return

                    import asyncio

                    if not ctx.db_handler or not ctx.loop:
                        raise RuntimeError("DB handler or event loop not available")

                    # 사용자 조회
                    future = asyncio.run_coroutine_threadsafe(
                        ctx.db_handler.get_user_by_id(user_id), ctx.loop
                    )
                    admin_user = future.result(timeout=5)

                    if not admin_user or admin_user.get("role") != "admin":
                        self.send_response(403)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {"success": False, "error": "관리자 권한이 필요합니다"}
                            ).encode("utf-8")
                        )
                        return

                    # 승인 대기 사용자 목록 조회
                    future = asyncio.run_coroutine_threadsafe(
                        ctx.db_handler.list_pending_users(), ctx.loop
                    )
                    pending_users = future.result(timeout=5)

                    # 성공 응답
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    response_data = json.dumps(
                        {"success": True, "users": pending_users}, ensure_ascii=False
                    ).encode("utf-8")
                    self.send_header("Content-Length", str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data)
                    return

                except Exception as e:
                    logger.exception("Admin pending-users API error")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"success": False, "error": str(e)}).encode("utf-8")
                    )
                    return

            # Admin API: 사용자 승인
            if self.path == "/api/admin/approve-user":
                try:
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length)
                    data = json.loads(body.decode("utf-8"))

                    # JWT 인증
                    token = None
                    authz = self.headers.get("Authorization")
                    if authz and authz.lower().startswith("bearer "):
                        token = authz.split(" ", 1)[1].strip()

                    payload, err = auth_verify_token(ctx, token, expected_type="access")
                    if err:
                        self.send_response(401)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"success": False, "error": f"인증 실패: {err}"}).encode(
                                "utf-8"
                            )
                        )
                        return

                    # 관리자 권한 확인
                    admin_user_id = payload.get("user_id") if payload else None
                    if not admin_user_id:
                        self.send_response(401)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"success": False, "error": "유효하지 않은 토큰"}).encode(
                                "utf-8"
                            )
                        )
                        return

                    import asyncio

                    if not ctx.db_handler or not ctx.loop:
                        raise RuntimeError("DB handler or event loop not available")

                    # 관리자 확인
                    future = asyncio.run_coroutine_threadsafe(
                        ctx.db_handler.get_user_by_id(admin_user_id), ctx.loop
                    )
                    admin_user = future.result(timeout=5)

                    if not admin_user or admin_user.get("role") != "admin":
                        self.send_response(403)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {"success": False, "error": "관리자 권한이 필요합니다"}
                            ).encode("utf-8")
                        )
                        return

                    # 승인할 사용자 ID 확인
                    target_user_id = data.get("user_id")
                    if not target_user_id:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"success": False, "error": "user_id는 필수입니다"}).encode(
                                "utf-8"
                            )
                        )
                        return

                    # 사용자 승인
                    future = asyncio.run_coroutine_threadsafe(
                        ctx.db_handler.approve_user(target_user_id, admin_user_id), ctx.loop
                    )
                    success = future.result(timeout=5)

                    if not success:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"success": False, "error": "사용자 승인 실패"}).encode(
                                "utf-8"
                            )
                        )
                        return

                    # 성공 응답
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    response_data = json.dumps({"success": True}).encode("utf-8")
                    self.send_header("Content-Length", str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data)
                    return

                except json.JSONDecodeError as e:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"success": False, "error": f"JSON 파싱 실패: {str(e)}"}).encode(
                            "utf-8"
                        )
                    )
                    return
                except Exception as e:
                    logger.exception("Admin approve-user API error")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"success": False, "error": str(e)}).encode("utf-8")
                    )
                    return

            # Import API
            if self.path.startswith("/api/import"):
                try:
                    # JWT 인증 (Export와 동일)
                    user_id = None  # JWT에서 추출한 user_id (사용자별 데이터 격리)
                    if ctx.login_required:
                        parsed = urlparse(self.path)
                        qs = parse_qs(parsed.query)
                        token = None
                        authz = self.headers.get("Authorization")
                        if authz and authz.lower().startswith("bearer "):
                            token = authz.split(" ", 1)[1].strip()
                        if not token:
                            token = (qs.get("token", [None]))[0]
                        payload, err = auth_verify_token(ctx, token, expected_type="access")
                        if err:
                            body = json.dumps(
                                {"success": False, "error": f"unauthorized: {err}"}
                            ).encode()
                            self.send_response(401)
                            self.send_header("Content-Type", "application/json")
                            self.end_headers()
                            self.wfile.write(body)
                            return
                        # JWT payload에서 user_id 추출
                        if payload:
                            user_id = payload.get("user_id")
                        if not user_id:
                            body = json.dumps(
                                {"success": False, "error": "user_id not found in token"}
                            ).encode()
                            self.send_response(401)
                            self.send_header("Content-Type", "application/json")
                            self.end_headers()
                            self.wfile.write(body)
                            return
                    else:
                        # 비로그인 모드는 더 이상 지원하지 않음
                        body = json.dumps({"success": False, "error": "login required"}).encode()
                        self.send_response(401)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(body)
                        return

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

                        # 비동기 import 실행
                        async def run_import():
                            exported_type = json_data.get("export_type", "").lower()
                            new_room_ids = []
                            messages_imported = 0

                            if exported_type == "single_room":
                                room = json_data.get("room", {})
                                rid, cnt = await _import_single_room(
                                    ctx,
                                    websocket=None,  # HTTP에서는 websocket 없음
                                    user_id=user_id,
                                    room_obj=room,
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
                                        websocket=None,
                                        user_id=user_id,
                                        room_obj=r,
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
                                    websocket=None,
                                    user_id=user_id,
                                    room_obj=room,
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

                        # 기존 이벤트 루프에서 실행 (새 루프 생성 금지)
                        if not ctx.loop:
                            raise RuntimeError("Event loop not available in AppContext")
                        future = asyncio.run_coroutine_threadsafe(run_import(), ctx.loop)
                        result = future.result(timeout=60)

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

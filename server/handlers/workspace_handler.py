import json
from pathlib import Path

import aiofiles


class WorkspaceHandler:
    """세계관, 캐릭터, 상황 파일 관리 + 프리셋 관리

    - 기존 MD 기반(world, situation, my_character, npc) 파일을 유지합니다.
    - 캐릭터 템플릿(JSON)과 내 프로필(JSON)을 간단히 저장/로드하기 위한 경로를 추가합니다.
    """

    def __init__(self, workspace_path="persona_data"):
        self.workspace_path = Path(workspace_path).resolve()
        self.worlds_path = self.workspace_path / "worlds"
        self.my_characters_path = self.workspace_path / "my_characters"
        self.npcs_path = self.workspace_path / "npcs"
        self.situations_path = self.workspace_path / "situations"
        self.presets_path = self.workspace_path / "presets"
        self.stories_path = self.workspace_path / "stories"
        self.rooms_path = self.workspace_path / "rooms"
        self.config_path = self.workspace_path / "config.json"

        # 신규: JSON 캐릭터 템플릿/내 프로필
        self.characters_dir = self.workspace_path / "characters"
        self.char_templates_path = self.characters_dir / "templates"
        self.my_profile_path = self.characters_dir / "my_profile.json"

        # 디렉토리 생성
        self.worlds_path.mkdir(parents=True, exist_ok=True)
        self.my_characters_path.mkdir(parents=True, exist_ok=True)
        self.npcs_path.mkdir(parents=True, exist_ok=True)
        self.situations_path.mkdir(parents=True, exist_ok=True)
        self.presets_path.mkdir(parents=True, exist_ok=True)
        self.stories_path.mkdir(parents=True, exist_ok=True)
        self.rooms_path.mkdir(parents=True, exist_ok=True)
        self.characters_dir.mkdir(parents=True, exist_ok=True)
        self.char_templates_path.mkdir(parents=True, exist_ok=True)

    def _get_base_path(self, file_type):
        """파일 타입에 따른 기본 경로 반환"""
        paths = {
            "world": self.worlds_path,
            "my_character": self.my_characters_path,
            "npc": self.npcs_path,
            "situation": self.situations_path,
            # 신규: JSON 템플릿 디렉터리(파일 확장자만 다름)
            "char_template": self.char_templates_path,
        }
        return paths.get(file_type)

    async def list_files(self, file_type):
        """파일 목록 반환

        Args:
            file_type: "world", "my_character", "npc", "situation"
        """
        try:
            # 단일 파일 타입 처리(my_profile)
            if file_type == "my_profile":
                if self.my_profile_path.exists():
                    return {
                        "success": True,
                        "files": [
                            {
                                "name": "my_profile",
                                "filename": self.my_profile_path.name,
                                "size": self.my_profile_path.stat().st_size,
                            }
                        ],
                    }
                return {"success": True, "files": []}

            base_path = self._get_base_path(file_type)
            if not base_path:
                return {"success": False, "error": f"Unknown file type: {file_type}"}

            if not base_path.exists():
                return {"success": True, "files": []}

            files = []
            # 확장자 분기: 템플릿은 .json, 나머지는 .md
            pattern = "*.json" if file_type == "char_template" else "*.md"
            for file_path in base_path.glob(pattern):
                files.append(
                    {
                        "name": file_path.stem,  # 확장자 제외한 파일명
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                    }
                )

            files.sort(key=lambda x: x["name"])
            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def read_file(self, file_type, filename):
        """파일 읽기

        Args:
            file_type: "world", "my_character", "npc", "situation"
            filename: 파일명 (확장자 포함 또는 미포함)
        """
        try:
            # 단일 파일(my_profile)
            if file_type == "my_profile":
                full_path = self.my_profile_path
                if not full_path.exists():
                    return {"success": False, "error": "프로필이 존재하지 않습니다"}
                async with aiofiles.open(full_path, encoding="utf-8") as f:
                    content = await f.read()
                return {"success": True, "content": content, "filename": full_path.name}

            base_path = self._get_base_path(file_type)
            if not base_path:
                return {"success": False, "error": f"Unknown file type: {file_type}"}

            # 확장자 결정
            if file_type == "char_template":
                if not filename.endswith(".json"):
                    filename = f"{filename}.json"
            else:
                if not filename.endswith(".md"):
                    filename = f"{filename}.md"

            full_path = base_path / filename

            if not full_path.exists():
                return {"success": False, "error": "파일이 존재하지 않습니다"}

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(base_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            async with aiofiles.open(full_path, encoding="utf-8") as f:
                content = await f.read()

            return {"success": True, "content": content, "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def save_file(self, file_type, filename, content):
        """파일 저장

        Args:
            file_type: "world", "my_character", "npc", "situation"
            filename: 파일명 (확장자 포함 또는 미포함)
            content: 파일 내용
        """
        try:
            # 단일 파일(my_profile)
            if file_type == "my_profile":
                full_path = self.my_profile_path
                # 디렉터리 보장
                full_path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                    await f.write(content)
                return {"success": True, "filename": full_path.name}

            base_path = self._get_base_path(file_type)
            if not base_path:
                return {"success": False, "error": f"Unknown file type: {file_type}"}

            # 확장자 결정
            if file_type == "char_template":
                if not filename.endswith(".json"):
                    filename = f"{filename}.json"
            else:
                if not filename.endswith(".md"):
                    filename = f"{filename}.md"

            full_path = base_path / filename

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(base_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            # 디렉터리 보장
            full_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(content)

            return {"success": True, "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_file(self, file_type, filename):
        """파일 삭제

        Args:
            file_type: "world", "my_character", "npc", "situation"
            filename: 파일명
        """
        try:
            # 단일 파일(my_profile)
            if file_type == "my_profile":
                if self.my_profile_path.exists():
                    self.my_profile_path.unlink()
                    return {"success": True, "filename": self.my_profile_path.name}
                return {"success": False, "error": "프로필이 존재하지 않습니다"}

            base_path = self._get_base_path(file_type)
            if not base_path:
                return {"success": False, "error": f"Unknown file type: {file_type}"}

            # 확장자 결정
            if file_type == "char_template":
                if not filename.endswith(".json"):
                    filename = f"{filename}.json"
            else:
                if not filename.endswith(".md"):
                    filename = f"{filename}.md"

            full_path = base_path / filename

            if not full_path.exists():
                return {"success": False, "error": "파일이 존재하지 않습니다"}

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(base_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            full_path.unlink()

            return {"success": True, "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def load_config(self):
        """설정 로드 (기본 파일 등)"""
        try:
            if not self.config_path.exists():
                return {"success": True, "config": {}}

            async with aiofiles.open(self.config_path, encoding="utf-8") as f:
                content = await f.read()
                config = json.loads(content)

            return {"success": True, "config": config}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def save_config(self, config):
        """설정 저장"""
        try:
            async with aiofiles.open(self.config_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(config, ensure_ascii=False, indent=2))

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ===== 프리셋 관리 =====

    async def list_presets(self):
        """프리셋 목록 반환"""
        try:
            if not self.presets_path.exists():
                return {"success": True, "files": []}

            files = []
            for file_path in self.presets_path.glob("*.json"):
                files.append(
                    {
                        "name": file_path.stem,
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                    }
                )

            files.sort(key=lambda x: x["name"])
            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def save_preset(self, filename, preset_data):
        """프리셋 저장

        Args:
            filename: 프리셋 파일명
            preset_data: 전체 설정 데이터 (dict)
        """
        try:
            if not filename.endswith(".json"):
                filename = f"{filename}.json"

            full_path = self.presets_path / filename

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(self.presets_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(preset_data, ensure_ascii=False, indent=2))

            return {"success": True, "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def load_preset(self, filename):
        """프리셋 로드

        Args:
            filename: 프리셋 파일명
        """
        try:
            if not filename.endswith(".json"):
                filename = f"{filename}.json"

            full_path = self.presets_path / filename

            if not full_path.exists():
                return {"success": False, "error": "프리셋 파일이 존재하지 않습니다"}

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(self.presets_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            async with aiofiles.open(full_path, encoding="utf-8") as f:
                content = await f.read()
                preset_data = json.loads(content)

            return {"success": True, "preset": preset_data, "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_preset(self, filename):
        """프리셋 삭제

        Args:
            filename: 프리셋 파일명
        """
        try:
            if not filename.endswith(".json"):
                filename = f"{filename}.json"

            full_path = self.presets_path / filename

            if not full_path.exists():
                return {"success": False, "error": "프리셋 파일이 존재하지 않습니다"}

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(self.presets_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            full_path.unlink()

            return {"success": True, "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ===== 서사 관리 =====

    def _sanitize_room(self, room_id: str | None) -> str:
        """채팅방 폴더명 안전화: 영숫자, -, _ 만 허용. 빈 값은 'default'."""
        rid = (room_id or "default").strip()
        import re

        rid = re.sub(r"[^A-Za-z0-9_\-]", "_", rid)
        return rid or "default"

    def _stories_dir(self, room_id: str | None):
        rid = self._sanitize_room(room_id)
        path = self.stories_path / rid
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ===== 채팅방 설정 저장/로드 =====
    def _rooms_dir(self, room_id: str | None):
        rid = self._sanitize_room(room_id)
        path = self.rooms_path / rid
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def list_rooms(self):
        try:
            if not self.rooms_path.exists():
                return {"success": True, "rooms": []}
            rooms = []
            for d in sorted(self.rooms_path.iterdir()):
                if d.is_dir():
                    cfg = d / "room.json"
                    title = d.name
                    mtime = d.stat().st_mtime
                    if cfg.exists():
                        try:
                            async with aiofiles.open(cfg, encoding="utf-8") as f:
                                import json as _json

                                obj = _json.loads(await f.read() or "{}")
                                title = obj.get("title") or obj.get("room_id") or title
                        except Exception:
                            pass
                    rooms.append({"room_id": d.name, "title": title, "modified": mtime})
            rooms.sort(key=lambda x: x["modified"], reverse=True)
            return {"success": True, "rooms": rooms}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def save_room(self, room_id: str, config: dict):
        try:
            base = self._rooms_dir(room_id)
            cfg = base / "room.json"
            import json as _json

            async with aiofiles.open(cfg, "w", encoding="utf-8") as f:
                await f.write(_json.dumps(config, ensure_ascii=False, indent=2))
            return {"success": True, "room_id": self._sanitize_room(room_id)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def load_room(self, room_id: str):
        try:
            base = self._rooms_dir(room_id)
            cfg = base / "room.json"
            if not cfg.exists():
                return {"success": False, "error": "room.json 이 없습니다"}
            async with aiofiles.open(cfg, encoding="utf-8") as f:
                import json as _json

                obj = _json.loads(await f.read() or "{}")
            return {"success": True, "room": obj, "room_id": self._sanitize_room(room_id)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_room(self, room_id: str):
        try:
            base = self._rooms_dir(room_id)
            # room.json만 삭제(폴더는 유지) — 스토리 등 보존 목적
            cfg = base / "room.json"
            if cfg.exists():
                cfg.unlink()
            return {"success": True, "room_id": self._sanitize_room(room_id)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_stories(self, room_id: str | None = None):
        """서사 목록 반환

        요구사항: 우측 '서사 기록' 패널을 채팅방으로 활용. 즉, 최상위 stories 목록을 그대로 노출.
        room_id 인자는 무시하고 최상위 디렉터리를 조회합니다.
        """
        try:
            base = self.stories_path
            if not base.exists():
                return {"success": True, "files": []}

            files = []
            for file_path in base.glob("*.md"):
                files.append(
                    {
                        "name": file_path.stem,
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime,
                    }
                )

            # 수정시간 역순 정렬 (최신순)
            files.sort(key=lambda x: x["modified"], reverse=True)
            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def save_story(self, filename, content, append: bool = False, room_id: str | None = None):
        """서사 저장

        Args:
            filename: 서사 파일명
            content: 마크다운 내용 (append=True일 때 전체 본문이어도 자동으로 delta만 추가)
            append: True이면 기존 파일 뒤에 새로운 부분만 덧붙임
        """
        try:
            if not filename.endswith(".md"):
                filename = f"{filename}.md"

            base = self.stories_path
            full_path = base / filename

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(self.stories_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            # 덧붙이기: 기존 파일이 있고, 새 본문이 기존의 확장이라면 delta만 추가
            if append and full_path.exists():
                async with aiofiles.open(full_path, encoding="utf-8") as rf:
                    existing = await rf.read()

                new_full = content or ""
                # 정확한 접두 검사: 기존 본문이 새 본문의 앞부분이면 delta만 추가
                if new_full.startswith(existing):
                    delta = new_full[len(existing) :]
                    if not delta.strip():
                        return {
                            "success": True,
                            "filename": filename,
                            "message": "변경사항이 없습니다",
                        }
                    async with aiofiles.open(full_path, "a", encoding="utf-8") as af:
                        await af.write(delta)
                    return {"success": True, "filename": filename, "appended": True}

                # 접두가 아니면 헤더 중복 최소화를 위해 첫 행의 제목 제거 후 이어붙임
                to_append = new_full
                if to_append.lstrip().startswith("# "):
                    # 첫 제목 라인과 이어지는 빈 줄 제거
                    stripped = to_append.lstrip()
                    idx = stripped.find("\n")
                    if idx != -1:
                        stripped = stripped[idx + 1 :]
                        # 다음 빈 줄 하나 더 제거
                        if stripped.startswith("\n"):
                            stripped = stripped[1:]
                    to_append = stripped

                # 파일 끝에 개행이 없으면 하나 추가
                if not existing.endswith("\n"):
                    to_append = "\n" + to_append

                async with aiofiles.open(full_path, "a", encoding="utf-8") as af:
                    await af.write(to_append)
                return {"success": True, "filename": filename, "appended": True}

            # 기본: 새 파일 생성 또는 덮어쓰기
            body = content or ""
            try:
                # front matter가 없으면 간단한 메타데이터를 추가
                needs_header = not body.lstrip().startswith("---\n")
                if needs_header:
                    from datetime import datetime

                    title = filename[:-3] if filename.endswith(".md") else filename
                    rid = self._sanitize_room(title)
                    iso = datetime.utcnow().isoformat() + "Z"
                    header = (
                        f"---\n"
                        f"title: {title}\n"
                        f"room_id: {rid}\n"
                        f"created_at: {iso}\n"
                        f"updated_at: {iso}\n"
                        f"---\n\n"
                    )
                    body = header + body
            except Exception:
                pass

            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(body)

            return {"success": True, "filename": filename, "appended": False}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def load_story(self, filename, room_id: str | None = None):
        """서사 로드

        Args:
            filename: 서사 파일명
        """
        try:
            if not filename.endswith(".md"):
                filename = f"{filename}.md"

            base = self.stories_path
            full_path = base / filename

            if not full_path.exists():
                return {"success": False, "error": "서사 파일이 존재하지 않습니다"}

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(self.stories_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            async with aiofiles.open(full_path, encoding="utf-8") as f:
                content = await f.read()

            return {"success": True, "content": content, "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_story(self, filename, room_id: str | None = None):
        """서사 삭제

        Args:
            filename: 서사 파일명
        """
        try:
            if not filename.endswith(".md"):
                filename = f"{filename}.md"

            base = self.stories_path
            full_path = base / filename

            if not full_path.exists():
                return {"success": False, "error": "서사 파일이 존재하지 않습니다"}

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(self.stories_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            full_path.unlink()

            return {"success": True, "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

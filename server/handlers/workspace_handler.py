import asyncio
import json
import os
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

    # ===== Git 관리 (persona_data 폴더) =====

    async def git_check_status(self):
        """Git 레포 상태 확인(로컬 변경/원격 앞섬/뒤처짐 포함)

        반환:
            - is_repo: bool
            - has_changes: bool (워킹트리 변경)
            - ahead: int (원격보다 앞선 커밋 수)
            - behind: int (원격보다 뒤처진 커밋 수)
            - branch: 현재 브랜치명(없으면 None)
            - upstream: 추적 브랜치(없으면 None)
            - status: `git status --porcelain` 출력
        """
        try:
            git_dir = self.workspace_path / ".git"
            is_repo = git_dir.exists()

            if not is_repo:
                return {"success": True, "is_repo": False, "message": "Git 레포지토리가 아닙니다"}

            # 로컬 변경 확인
            proc = await asyncio.create_subprocess_exec(
                "git",
                "status",
                "--porcelain",
                cwd=str(self.workspace_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            st_stdout, st_stderr = await proc.communicate()
            if proc.returncode != 0:
                return {
                    "success": False,
                    "is_repo": True,
                    "error": (st_stderr or st_stdout).decode(),
                }
            status_text = (st_stdout or b"").decode()
            has_changes = len(status_text.strip()) > 0

            # 현재 브랜치
            branch = None
            try:
                proc_b = await asyncio.create_subprocess_exec(
                    "git",
                    "rev-parse",
                    "--abbrev-ref",
                    "HEAD",
                    cwd=str(self.workspace_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                b_out, _ = await proc_b.communicate()
                branch = (b_out or b"").decode().strip() or None
            except Exception:
                branch = None

            # 업스트림(추적 브랜치)
            upstream = None
            try:
                proc_u = await asyncio.create_subprocess_exec(
                    "git",
                    "rev-parse",
                    "--abbrev-ref",
                    "--symbolic-full-name",
                    "@{u}",
                    cwd=str(self.workspace_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                u_out, u_err = await proc_u.communicate()
                if proc_u.returncode == 0:
                    upstream = (u_out or b"").decode().strip() or None
            except Exception:
                upstream = None

            # ahead/behind 계산 (업스트림이 있을 때)
            ahead = 0
            behind = 0
            if upstream:
                try:
                    # @{u}...HEAD 형태: left(behind), right(ahead)
                    proc_ab = await asyncio.create_subprocess_exec(
                        "git",
                        "rev-list",
                        "--left-right",
                        "--count",
                        "@{u}...HEAD",
                        cwd=str(self.workspace_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    ab_out, ab_err = await asyncio.wait_for(proc_ab.communicate(), timeout=2.0)
                    if proc_ab.returncode == 0:
                        parts = (ab_out or b"").decode().strip().split()
                        if len(parts) >= 2:
                            behind = int(parts[0])
                            ahead = int(parts[1])
                except Exception:
                    ahead = 0
                    behind = 0

            return {
                "success": True,
                "is_repo": True,
                "has_changes": has_changes,
                "ahead": ahead,
                "behind": behind,
                "branch": branch,
                "upstream": upstream,
                "status": status_text,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def git_init(self):
        """Git 레포 초기화"""
        try:
            # git init
            proc = await asyncio.create_subprocess_exec(
                "git",
                "init",
                cwd=str(self.workspace_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                return {"success": False, "error": stderr.decode()}

            # .gitignore 생성 (선택사항)
            gitignore_path = self.workspace_path / ".gitignore"
            if not gitignore_path.exists():
                async with aiofiles.open(gitignore_path, "w", encoding="utf-8") as f:
                    await f.write("# OS files\n.DS_Store\nThumbs.db\n")

            return {"success": True, "message": "Git 레포지토리가 초기화되었습니다"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def git_sync(self, commit_message=None):
        """Git 자동 동기화 (add + commit + push)"""
        try:
            push_mode = os.getenv("APP_GIT_SYNC_MODE", "container").lower()  # container | host
            disable_push = os.getenv("APP_DISABLE_GIT_PUSH", "0") in ("1", "true", "yes")
            # 기본 커밋 메시지
            if not commit_message:
                from datetime import datetime

                commit_message = f"Auto sync - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # git add .
            proc = await asyncio.create_subprocess_exec(
                "git",
                "add",
                ".",
                cwd=str(self.workspace_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            add_stdout, add_stderr = await proc.communicate()

            if proc.returncode != 0:
                # add 실패 사유를 그대로 노출해 진단 용이성 향상
                return {
                    "success": False,
                    "error": f"git add 실패: {(add_stderr or add_stdout).decode().strip()}",
                }

            committed = False  # 커밋 여부 추적
            # git commit
            proc = await asyncio.create_subprocess_exec(
                "git",
                "commit",
                "-m",
                commit_message,
                cwd=str(self.workspace_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            commit_stdout, commit_stderr = await proc.communicate()

            # 커밋할 내용이 없는 경우: git은 종료코드 1을 반환하고 메시지는 보통 stdout에 기록됨
            if proc.returncode != 0:
                out = (commit_stdout or b"").decode()
                err = (commit_stderr or b"").decode()
                combined = f"{out}\n{err}".lower()
                if "nothing to commit" in combined or "no changes added to commit" in combined:
                    # 호스트 모드면 푸시 트리거 생성 후 종료, 컨테이너 모드면 pull/push 진행
                    if disable_push or push_mode == "host":
                        await self._write_host_push_trigger(commit_message)
                        return {
                            "success": True,
                            "message": "커밋할 변경 없음 (호스트에 pull/push 위임)",
                            "warning": "컨테이너 푸시는 비활성화되어 호스트로 위임됩니다.",
                        }
                    committed = False
                else:
                    return {"success": False, "error": (err or out).strip()}

            # 커밋된 경우 커밋 SHA 추출 (호스트 위임 시 트리거에 기록)
            commit_sha = None
            try:
                proc_sha = await asyncio.create_subprocess_exec(
                    "git",
                    "rev-parse",
                    "--short",
                    "HEAD",
                    cwd=str(self.workspace_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                sha_out, _ = await proc_sha.communicate()
                commit_sha = (sha_out or b"").decode().strip() or None
            except Exception:
                commit_sha = None

            # 컨테이너에서 푸시 비활성화 또는 호스트 모드면 푸시를 호스트에 위임
            if disable_push or push_mode == "host":
                await self._write_host_push_trigger(commit_message, commit_sha)
                return {
                    "success": True,
                    "message": "커밋 완료 (호스트 푸시 트리거 전송)",
                    "warning": "컨테이너 푸시는 비활성화되어 호스트로 위임됩니다.",
                }

            # 컨테이너 모드: 원격 변경이 있으면 pull --rebase 먼저 수행
            try:
                proc_u = await asyncio.create_subprocess_exec(
                    "git",
                    "rev-parse",
                    "--abbrev-ref",
                    "--symbolic-full-name",
                    "@{u}",
                    cwd=str(self.workspace_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                u_out, _ = await proc_u.communicate()
                if proc_u.returncode == 0:
                    # 업스트림 존재 → 리베이스 pull (네트워크 호출은 사용자 동작에서만 수행)
                    proc_pull = await asyncio.create_subprocess_exec(
                        "git",
                        "pull",
                        "--rebase",
                        cwd=str(self.workspace_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    try:
                        pull_out, pull_err = await asyncio.wait_for(
                            proc_pull.communicate(), timeout=20.0
                        )
                    except TimeoutError:
                        return {"success": False, "error": "git pull --rebase 타임아웃"}
                    if proc_pull.returncode != 0:
                        return {
                            "success": False,
                            "error": (pull_err or pull_out).decode().strip()
                            or "git pull --rebase 실패",
                        }
            except Exception:
                # pull 시도 중 오류는 이후 push 단계에서 재확인되므로 조용히 무시
                pass

            # git push
            proc = await asyncio.create_subprocess_exec(
                "git",
                "push",
                cwd=str(self.workspace_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            push_stdout, push_stderr = await proc.communicate()

            if proc.returncode != 0:
                stderr_text = (push_stderr or b"").decode()
                stdout_text = (push_stdout or b"").decode()
                combined = f"{stdout_text}\n{stderr_text}"
                # 원격 레포 설정 안 된 경우
                if "No configured push destination" in stderr_text or "no upstream" in stderr_text:
                    return {
                        "success": True,
                        "message": "커밋 완료 (원격 레포 미설정)",
                        "warning": "원격 레포지토리를 설정하세요: git remote add origin <URL>",
                    }
                return {"success": False, "error": combined.strip()}

            return {"success": True, "message": "동기화 완료 (pull + commit + push)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _write_host_push_trigger(
        self, commit_message: str | None, commit_sha: str | None = None
    ):
        """호스트 측 푸시를 유도하기 위한 트리거 파일 작성.

        컨테이너와 호스트가 공유하는 `persona_data/.sync/` 디렉토리에
        JSON 파일을 기록합니다. 호스트 워처가 이를 감지해 `git push`를 수행하게 됩니다.
        """
        try:
            from datetime import datetime

            sync_dir = self.workspace_path / ".sync"
            sync_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            trigger_path = sync_dir / f"push_{ts}.json"

            payload = {
                "action": "push",
                "timestamp": ts,
                "commit": commit_sha,
                "message": commit_message or "",
            }

            async with aiofiles.open(trigger_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(payload, ensure_ascii=False))

            return str(trigger_path)
        except Exception:
            # 트리거 실패는 동작을 막을 정도는 아니므로 조용히 무시
            return None

    async def git_pull(self):
        """Git pull (원격에서 가져오기)"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "pull",
                cwd=str(self.workspace_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                stderr_text = stderr.decode()
                return {"success": False, "error": stderr_text}

            return {"success": True, "message": "Pull 완료", "output": stdout.decode()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ===== 서사 관리 =====

    async def list_stories(self):
        """서사 목록 반환"""
        try:
            if not self.stories_path.exists():
                return {"success": True, "files": []}

            files = []
            for file_path in self.stories_path.glob("*.md"):
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

    async def save_story(self, filename, content, append: bool = False):
        """서사 저장

        Args:
            filename: 서사 파일명
            content: 마크다운 내용 (append=True일 때 전체 본문이어도 자동으로 delta만 추가)
            append: True이면 기존 파일 뒤에 새로운 부분만 덧붙임
        """
        try:
            if not filename.endswith(".md"):
                filename = f"{filename}.md"

            full_path = self.stories_path / filename

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
            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(content)

            return {"success": True, "filename": filename, "appended": False}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def load_story(self, filename):
        """서사 로드

        Args:
            filename: 서사 파일명
        """
        try:
            if not filename.endswith(".md"):
                filename = f"{filename}.md"

            full_path = self.stories_path / filename

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

    async def delete_story(self, filename):
        """서사 삭제

        Args:
            filename: 서사 파일명
        """
        try:
            if not filename.endswith(".md"):
                filename = f"{filename}.md"

            full_path = self.stories_path / filename

            if not full_path.exists():
                return {"success": False, "error": "서사 파일이 존재하지 않습니다"}

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(self.stories_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            full_path.unlink()

            return {"success": True, "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

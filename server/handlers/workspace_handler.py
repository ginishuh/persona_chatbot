import os
import json
import aiofiles
import asyncio
from pathlib import Path

class WorkspaceHandler:
    """세계관, 캐릭터, 상황 파일 관리 + 프리셋 관리"""

    def __init__(self, workspace_path="persona_data"):
        self.workspace_path = Path(workspace_path).resolve()
        self.worlds_path = self.workspace_path / "worlds"
        self.my_characters_path = self.workspace_path / "my_characters"
        self.npcs_path = self.workspace_path / "npcs"
        self.situations_path = self.workspace_path / "situations"
        self.presets_path = self.workspace_path / "presets"
        self.stories_path = self.workspace_path / "stories"
        self.config_path = self.workspace_path / "config.json"

        # 디렉토리 생성
        self.worlds_path.mkdir(parents=True, exist_ok=True)
        self.my_characters_path.mkdir(parents=True, exist_ok=True)
        self.npcs_path.mkdir(parents=True, exist_ok=True)
        self.situations_path.mkdir(parents=True, exist_ok=True)
        self.presets_path.mkdir(parents=True, exist_ok=True)
        self.stories_path.mkdir(parents=True, exist_ok=True)

    def _get_base_path(self, file_type):
        """파일 타입에 따른 기본 경로 반환"""
        paths = {
            "world": self.worlds_path,
            "my_character": self.my_characters_path,
            "npc": self.npcs_path,
            "situation": self.situations_path
        }
        return paths.get(file_type)

    async def list_files(self, file_type):
        """파일 목록 반환

        Args:
            file_type: "world", "my_character", "npc", "situation"
        """
        try:
            base_path = self._get_base_path(file_type)
            if not base_path:
                return {"success": False, "error": f"Unknown file type: {file_type}"}

            if not base_path.exists():
                return {"success": True, "files": []}

            # 모두 마크다운 파일
            files = []
            for file_path in base_path.glob("*.md"):
                files.append({
                    "name": file_path.stem,  # 확장자 제외한 파일명
                    "filename": file_path.name,
                    "size": file_path.stat().st_size
                })

            # 이름순 정렬
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
            base_path = self._get_base_path(file_type)
            if not base_path:
                return {"success": False, "error": f"Unknown file type: {file_type}"}

            # 모두 .md 확장자
            if not filename.endswith(".md"):
                filename = f"{filename}.md"

            full_path = base_path / filename

            if not full_path.exists():
                return {"success": False, "error": "파일이 존재하지 않습니다"}

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(base_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
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
            base_path = self._get_base_path(file_type)
            if not base_path:
                return {"success": False, "error": f"Unknown file type: {file_type}"}

            # 모두 .md 확장자
            if not filename.endswith(".md"):
                filename = f"{filename}.md"

            full_path = base_path / filename

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(base_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
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
            base_path = self._get_base_path(file_type)
            if not base_path:
                return {"success": False, "error": f"Unknown file type: {file_type}"}

            # 모두 .md 확장자
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

            async with aiofiles.open(self.config_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                config = json.loads(content)

            return {"success": True, "config": config}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def save_config(self, config):
        """설정 저장"""
        try:
            async with aiofiles.open(self.config_path, 'w', encoding='utf-8') as f:
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
                files.append({
                    "name": file_path.stem,
                    "filename": file_path.name,
                    "size": file_path.stat().st_size
                })

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

            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
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

            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
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
        """Git 레포 상태 확인"""
        try:
            # .git 디렉토리가 있는지 확인
            git_dir = self.workspace_path / ".git"
            is_repo = git_dir.exists()

            if not is_repo:
                return {
                    "success": True,
                    "is_repo": False,
                    "message": "Git 레포지토리가 아닙니다"
                }

            # git status 실행
            proc = await asyncio.create_subprocess_exec(
                'git', 'status', '--porcelain',
                cwd=str(self.workspace_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                return {
                    "success": False,
                    "is_repo": True,
                    "error": stderr.decode()
                }

            # 변경사항이 있는지 확인
            has_changes = len(stdout.decode().strip()) > 0

            return {
                "success": True,
                "is_repo": True,
                "has_changes": has_changes,
                "status": stdout.decode()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def git_init(self):
        """Git 레포 초기화"""
        try:
            # git init
            proc = await asyncio.create_subprocess_exec(
                'git', 'init',
                cwd=str(self.workspace_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                return {"success": False, "error": stderr.decode()}

            # .gitignore 생성 (선택사항)
            gitignore_path = self.workspace_path / ".gitignore"
            if not gitignore_path.exists():
                async with aiofiles.open(gitignore_path, 'w', encoding='utf-8') as f:
                    await f.write("# OS files\n.DS_Store\nThumbs.db\n")

            return {
                "success": True,
                "message": "Git 레포지토리가 초기화되었습니다"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def git_sync(self, commit_message=None):
        """Git 자동 동기화 (add + commit + push)"""
        try:
            # 기본 커밋 메시지
            if not commit_message:
                from datetime import datetime
                commit_message = f"Auto sync - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # git add .
            proc = await asyncio.create_subprocess_exec(
                'git', 'add', '.',
                cwd=str(self.workspace_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()

            if proc.returncode != 0:
                return {"success": False, "error": "git add 실패"}

            # git commit
            proc = await asyncio.create_subprocess_exec(
                'git', 'commit', '-m', commit_message,
                cwd=str(self.workspace_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            # 커밋할 내용이 없으면 성공으로 처리
            if proc.returncode != 0:
                stderr_text = stderr.decode()
                if "nothing to commit" in stderr_text:
                    return {
                        "success": True,
                        "message": "변경사항이 없습니다"
                    }
                else:
                    return {"success": False, "error": stderr_text}

            # git push
            proc = await asyncio.create_subprocess_exec(
                'git', 'push',
                cwd=str(self.workspace_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                stderr_text = stderr.decode()
                # 원격 레포 설정 안 된 경우
                if "No configured push destination" in stderr_text or "no upstream" in stderr_text:
                    return {
                        "success": True,
                        "message": "커밋 완료 (원격 레포 미설정)",
                        "warning": "원격 레포지토리를 설정하세요: git remote add origin <URL>"
                    }
                else:
                    return {"success": False, "error": stderr_text}

            return {
                "success": True,
                "message": "동기화 완료 (커밋 및 푸시)"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def git_pull(self):
        """Git pull (원격에서 가져오기)"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'git', 'pull',
                cwd=str(self.workspace_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                stderr_text = stderr.decode()
                return {"success": False, "error": stderr_text}

            return {
                "success": True,
                "message": "Pull 완료",
                "output": stdout.decode()
            }
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
                files.append({
                    "name": file_path.stem,
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime
                })

            # 수정시간 역순 정렬 (최신순)
            files.sort(key=lambda x: x["modified"], reverse=True)
            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def save_story(self, filename, content):
        """서사 저장

        Args:
            filename: 서사 파일명
            content: 마크다운 내용
        """
        try:
            if not filename.endswith(".md"):
                filename = f"{filename}.md"

            full_path = self.stories_path / filename

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(self.stories_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(content)

            return {"success": True, "filename": filename}
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

            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
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

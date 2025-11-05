import asyncio
from pathlib import Path

class ModeHandler:
    """코딩 모드 ↔ 챗봇 모드 전환 관리"""

    def __init__(self, project_root="."):
        self.project_root = Path(project_root).resolve()

        # 대상 폴더들
        self.target_dirs = [
            self.project_root,
            self.project_root / ".claude",
            self.project_root / ".codex"
        ]

        # 대상 파일명들
        self.target_files = ["CLAUDE.md", "AGENTS.md"]

    async def check_mode(self):
        """현재 모드 확인

        Returns:
            "chatbot": 챗봇 모드 (.md.bak 존재, .md 없음)
            "coding": 코딩 모드 (.md 존재)
            "mixed": 혼재 상태
        """
        try:
            md_count = 0
            bak_count = 0

            for target_dir in self.target_dirs:
                if not target_dir.exists():
                    continue

                for filename in self.target_files:
                    md_path = target_dir / filename
                    bak_path = target_dir / f"{filename}.bak"

                    if md_path.exists():
                        md_count += 1
                    if bak_path.exists():
                        bak_count += 1

            # 모드 판단
            if md_count > 0 and bak_count == 0:
                mode = "coding"
            elif md_count == 0 and bak_count > 0:
                mode = "chatbot"
            elif md_count == 0 and bak_count == 0:
                mode = "none"
            else:
                mode = "mixed"

            return {
                "success": True,
                "mode": mode,
                "md_files": md_count,
                "bak_files": bak_count
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def switch_to_chatbot(self):
        """챗봇 전용 모드로 전환 (.md → .md.bak)"""
        try:
            moved_files = []
            skipped_files = []

            for target_dir in self.target_dirs:
                if not target_dir.exists():
                    continue

                for filename in self.target_files:
                    md_path = target_dir / filename
                    bak_path = target_dir / f"{filename}.bak"

                    if md_path.exists():
                        # .md.bak가 이미 있으면 스킵
                        if bak_path.exists():
                            skipped_files.append(str(md_path.relative_to(self.project_root)))
                        else:
                            # .md → .md.bak
                            md_path.rename(bak_path)
                            moved_files.append(str(md_path.relative_to(self.project_root)))

            return {
                "success": True,
                "mode": "chatbot",
                "moved": moved_files,
                "skipped": skipped_files,
                "message": f"챗봇 전용 모드로 전환 완료 ({len(moved_files)}개 파일)"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def switch_to_coding(self):
        """코딩 모드로 전환 (.md.bak → .md)"""
        try:
            moved_files = []
            skipped_files = []

            for target_dir in self.target_dirs:
                if not target_dir.exists():
                    continue

                for filename in self.target_files:
                    md_path = target_dir / filename
                    bak_path = target_dir / f"{filename}.bak"

                    if bak_path.exists():
                        # .md가 이미 있으면 스킵
                        if md_path.exists():
                            skipped_files.append(str(bak_path.relative_to(self.project_root)))
                        else:
                            # .md.bak → .md
                            bak_path.rename(md_path)
                            moved_files.append(str(md_path.relative_to(self.project_root)))

            return {
                "success": True,
                "mode": "coding",
                "moved": moved_files,
                "skipped": skipped_files,
                "message": f"코딩 모드로 전환 완료 ({len(moved_files)}개 파일)"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

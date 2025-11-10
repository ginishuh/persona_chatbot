import asyncio
from pathlib import Path


class GitHandler:
    def __init__(self, repo_path="STORIES"):
        self.repo_path = Path(repo_path).resolve()

    async def _run_command(self, command):
        """Git 명령어 실행"""
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.repo_path,
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()

    async def status(self):
        """Git 상태 확인"""
        try:
            returncode, stdout, stderr = await self._run_command("git status --short")

            if returncode != 0:
                return {"success": False, "error": stderr}

            return {"success": True, "status": stdout}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def commit_and_push(self, message="Update from web app"):
        """변경사항 커밋 및 푸시"""
        try:
            # git add .
            returncode, stdout, stderr = await self._run_command("git add .")
            if returncode != 0:
                return {"success": False, "error": f"git add 실패: {stderr}"}

            # git commit
            returncode, stdout, stderr = await self._run_command(f'git commit -m "{message}"')
            if returncode != 0:
                # 커밋할 내용이 없는 경우
                if "nothing to commit" in stdout or "nothing to commit" in stderr:
                    return {"success": True, "message": "변경사항이 없습니다"}
                return {"success": False, "error": f"git commit 실패: {stderr}"}

            # git push
            returncode, stdout, stderr = await self._run_command("git push")
            if returncode != 0:
                return {"success": False, "error": f"git push 실패: {stderr}"}

            return {"success": True, "message": "커밋 및 푸시 완료"}
        except Exception as e:
            return {"success": False, "error": str(e)}

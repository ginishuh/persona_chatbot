from pathlib import Path

import aiofiles


class FileHandler:
    def __init__(self, base_path="STORIES"):
        self.base_path = Path(base_path).resolve()

    async def list_files(self):
        """서사 파일 목록 반환"""
        try:
            if not self.base_path.exists():
                return {"success": False, "error": "STORIES 디렉토리가 없습니다"}

            files = []
            for file_path in self.base_path.rglob("*.md"):
                relative_path = file_path.relative_to(self.base_path)
                files.append(
                    {
                        "path": str(relative_path),
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                    }
                )

            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def read_file(self, file_path):
        """파일 읽기"""
        try:
            full_path = self.base_path / file_path

            if not full_path.exists():
                return {"success": False, "error": "파일이 존재하지 않습니다"}

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            async with aiofiles.open(full_path, encoding="utf-8") as f:
                content = await f.read()

            return {"success": True, "content": content, "path": file_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def write_file(self, file_path, content):
        """파일 쓰기"""
        try:
            full_path = self.base_path / file_path

            # 보안: 경로 탈출 방지
            if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
                return {"success": False, "error": "잘못된 경로입니다"}

            # 디렉토리 생성
            full_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(content)

            return {"success": True, "path": file_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

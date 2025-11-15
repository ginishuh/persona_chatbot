#!/usr/bin/env python3
"""관리자 계정 시드 스크립트

.env 파일에서 관리자 정보를 읽어 DB에 추가합니다.

환경 변수:
- ADMIN_USERNAME: 관리자 아이디 (기본값: admin)
- ADMIN_EMAIL: 관리자 이메일 (기본값: admin@example.com)
- ADMIN_PASSWORD: 관리자 비밀번호 (기본값: admin123)
- DB_PATH: DB 파일 경로 (기본값: data/chatbot.db)

사용법:
    python3 scripts/seed_admin.py
"""

import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

import bcrypt
from dotenv import load_dotenv

from server.handlers.db_handler import DBHandler


async def seed_admin():
    """관리자 계정 생성"""
    # .env 로드
    load_dotenv()

    # 환경 변수에서 관리자 정보 읽기
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    db_path = os.getenv("DB_PATH", "data/chatbot.db")

    print("🔧 관리자 계정 시드 스크립트")
    print(f"   DB 경로: {db_path}")
    print(f"   아이디: {admin_username}")
    print(f"   이메일: {admin_email}")
    print()

    # DB 초기화
    db = DBHandler(db_path)
    await db.initialize()

    # 비밀번호 해싱
    password_hash = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # 관리자 계정 생성
    user_id = await db.create_admin_user(admin_username, admin_email, password_hash)

    if user_id is None:
        print("❌ 관리자 계정 생성 실패 (이미 존재하는 사용자명 또는 이메일)")
        # 기존 사용자 조회
        existing = await db.get_user_by_username(admin_username)
        if existing:
            print("   기존 사용자 정보:")
            print(f"   - user_id: {existing['user_id']}")
            print(f"   - username: {existing['username']}")
            print(f"   - email: {existing['email']}")
            print(f"   - role: {existing.get('role', 'N/A')}")
            print(f"   - is_approved: {existing.get('is_approved', 'N/A')}")
    else:
        print("✅ 관리자 계정 생성 완료")
        print(f"   user_id: {user_id}")
        print(f"   username: {admin_username}")
        print(f"   email: {admin_email}")
        print("   role: admin")
        print("   is_approved: True")

    await db.close()


if __name__ == "__main__":
    asyncio.run(seed_admin())

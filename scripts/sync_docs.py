#!/usr/bin/env python3
"""
문서 동기화 스크립트

베이스 영문 문서(`docs/agents_base_en.md`)로부터
`CLAUDE.md`와 `AGENTS.md`를 자동으로 복제합니다.

실행 방법:
    python3 scripts/sync_docs.py
"""

import shutil
from pathlib import Path


def sync_docs() -> bool:
    """베이스 문서로부터 `CLAUDE.md`와 `AGENTS.md`를 동기화합니다.

    Returns:
        True on success, False on failure.
    """

    base_en = Path("docs/agents_base_en.md")
    base_ko = Path("docs/agents_base_ko.md")
    claude_dev = Path("CLAUDE.md")
    agents_ko = Path("AGENTS.md")

    if not base_en.exists() or not base_ko.exists():
        missing = []
        if not base_en.exists():
            missing.append(str(base_en))
        if not base_ko.exists():
            missing.append(str(base_ko))
        print(f"❌ 베이스 문서를 찾을 수 없습니다: {', '.join(missing)}")
        return False

    print("📚 문서 동기화 시작...")

    # CLAUDE.md 동기화 (영문 베이스 복제)
    print("📝 CLAUDE.md 동기화...")
    try:
        shutil.copy2(base_en, claude_dev)
        print("✅ CLAUDE.md 업데이트 완료")
    except Exception as e:
        print(f"❌ CLAUDE.md 복제 실패: {e}")
        return False

    # AGENTS.md 동기화 (영문 베이스 복제)
    print("📝 AGENTS.md 동기화...")
    try:
        shutil.copy2(base_en, agents_ko)
        print("✅ AGENTS.md 업데이트 완료")
    except Exception as e:
        print(f"❌ AGENTS.md 복제 실패: {e}")
        return False

    print("🎉 문서 동기화 완료!")
    print("\n📋 언어 규칙 요약:")
    print("- 코드/주석/커밋: 한국어")
    print("- 변수명/함수명/API: 영어")
    print("- 베이스 문서(docs/agents_base_en.md): 영문 (SSOT)")
    print("- 개발 문서(CLAUDE.md, AGENTS.md): 베이스 문서로부터 자동 복제")

    return True


if __name__ == "__main__":
    success = sync_docs()
    exit(0 if success else 1)

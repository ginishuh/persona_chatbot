#!/usr/bin/env bash
set -euo pipefail

# 한국어 안내: pre-commit 훅 설치 스크립트
# - Python 가상환경이 있다면 활성화 후 실행 권장

if ! command -v pre-commit >/dev/null 2>&1; then
  echo "pre-commit이 설치되어 있지 않습니다. pip로 설치합니다..." >&2
  python3 -m pip install --user pre-commit
fi

echo "pre-commit 훅 설치 중..."
pre-commit install --hook-type pre-commit --hook-type pre-push

echo "최초 전체 검사 실행(캐시 생성)..."
pre-commit run --all-files || true

echo "완료: .git/hooks/pre-commit, pre-push 설치됨"

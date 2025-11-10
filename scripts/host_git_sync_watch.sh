#!/usr/bin/env bash
set -euo pipefail

# 호스트에서 persona_data 푸시를 지속적으로 감시/실행하는 간단한 워처
# inotify가 있으면 더 효율적으로 만들 수 있으나, 기본 쉘 루프로도 동작합니다.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="${REPO_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)/persona_data}"
SYNC_DIR="${REPO_DIR}/.sync"

mkdir -p "${SYNC_DIR}"

echo "[host-git-sync] 감시 시작: ${SYNC_DIR}"
while true; do
  "${SCRIPT_DIR}/host_git_sync_once.sh" || true
  sleep 3
done

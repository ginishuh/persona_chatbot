#!/usr/bin/env bash
set -euo pipefail

# 호스트에서 persona_data 푸시를 1회 수행하는 스크립트
# - 컨테이너에서 생성한 트리거 파일(persona_data/.sync/push_*.json)을 감지하여 push 실행
# - push 성공 시 해당 트리거 파일을 삭제, 실패 시 파일을 보존하여 재시도 가능

# REPO_DIR 환경변수로 경로를 주입할 수 있으며, 미지정 시 본 저장소 기준 상대 경로 사용
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="${REPO_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)/persona_data}"
SYNC_DIR="${REPO_DIR}/.sync"

mkdir -p "${SYNC_DIR}"

# 가장 오래된 트리거 1개 선택
TRIGGER_FILE=$(ls -1 "${SYNC_DIR}"/push_*.json 2>/dev/null | head -n 1 || true)
if [[ -z "${TRIGGER_FILE}" ]]; then
  echo "[host-git-sync] 처리할 트리거가 없습니다." >&2
  exit 0
fi

echo "[host-git-sync] 트리거 감지: ${TRIGGER_FILE}"

# 원격이 없거나 인증이 없는 경우 사용자가 별도로 구성해야 합니다.
echo "[host-git-sync] 원격 가져오기 (rebase) 시도"
if ! git -C "${REPO_DIR}" pull --rebase; then
  echo "[host-git-sync] pull 실패 (무시하고 push 시도하거나 다음에 재시도)" >&2
fi

echo "[host-git-sync] 원격 푸시 시도"
if git -C "${REPO_DIR}" push; then
  rm -f "${TRIGGER_FILE}"
  echo "[host-git-sync] push 성공 → 트리거 제거"
  exit 0
else
  echo "[host-git-sync] push 실패 → 트리거 유지 (후속 재시도 필요)" >&2
  exit 1
fi


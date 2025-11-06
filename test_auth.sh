#!/bin/bash

# 컨테이너 내부에서 Claude CLI 인증 테스트

echo "=== Claude CLI 버전 확인 ==="
claude --version

echo ""
echo "=== Claude 설정 디렉토리 확인 ==="
ls -la /root/.claude/

echo ""
echo "=== 인증 파일 존재 확인 ==="
if [ -f /root/.claude/.credentials.json ]; then
    echo "✓ .credentials.json 파일이 존재합니다"
else
    echo "✗ .credentials.json 파일이 없습니다"
    exit 1
fi

echo ""
echo "=== Claude CLI 간단한 명령 테스트 ==="
echo "Hello, test" | claude --print --verbose --output-format stream-json --setting-sources user,project,local 2>&1 | head -20

echo ""
echo "=== 테스트 완료 ==="

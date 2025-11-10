**로컬 훅(Pre-commit) 가이드**

- 목적: 커밋/푸시 전에 자동으로 포맷/린트/보안 점검을 수행합니다.
- 적용 범위: Python(black/ruff/bandit), 웹 자산(Prettier), 시크릿 스캔(detect-secrets).

**설치**
- 권장: 가상환경 활성화 후 실행
```
python3 -m pip install --user pre-commit
bash scripts/install_hooks.sh
```

**사용**
- 커밋 시 자동 실행됩니다. 수동 실행:
```
pre-commit run --all-files
```

**구성 파일**
- `.pre-commit-config.yaml`: 훅 정의
- `pyproject.toml`: black/ruff/bandit 설정
- `bandit.yaml`: bandit 상세 설정
- `.secrets.baseline`: detect-secrets 베이스라인(신규 시크릿 추가 차단)

**베이스라인 갱신**
```
detect-secrets scan --exclude-files '(^|/)(\.git|\.env|\.venv|venv|node_modules)/' > .secrets.baseline
git add .secrets.baseline && git commit -m "chore(security): 시크릿 베이스라인 갱신"
```

**팁**
- 느린 훅은 pre-push 단계에서만 실행하도록 분리할 수 있습니다.
- Node가 없으면 Prettier 훅을 일시 비활성화하거나 Node 설치 후 사용하세요.


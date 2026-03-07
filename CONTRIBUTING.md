# Contributing to Persona Chat

Thanks for considering a contribution. Whether it's a bug fix, a new test, better docs, or a feature idea — it all helps.

## Before you start

- **Search first.** Check existing issues and PRs to avoid duplicate work.
- **Big changes → open an issue.** For anything beyond a quick fix, let's align on scope before you invest time writing code.
- **Small fixes → go straight to a PR.** Typos, doc improvements, and one-liner bug fixes don't need an issue.

## Setting up the dev environment

```bash
git clone https://github.com/ginishuh/persona_chatbot.git
cd persona_chatbot

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the app
python3 -m server.websocket_server
# Web UI  → http://127.0.0.1:9000
# WS      → ws://127.0.0.1:8765
```

You'll also need at least one AI CLI installed and authenticated locally (Claude Code, Gemini, or Droid). See the [README](README.md) for provider setup.

## Code style

| Area | Convention |
|------|-----------|
| Python formatting | PEP 8, 4-space indent, enforced by `black` and `ruff` |
| Naming | `snake_case` for modules/functions, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants |
| Type hints | Encouraged where practical |
| Logging | Use `logging`, not `print` |
| JS (web/) | ES6+ (`const`/`let`), small pure functions, DOM logic separated from rendering |
| Comments & commits | Korean preferred; identifiers stay in English |

Pre-commit hooks enforce most of this automatically:

```bash
pre-commit install          # first time only
pre-commit run --all-files  # check everything
```

## Running tests

```bash
pytest -q                    # unit tests
python scripts/ws_chat_test.py --provider claude --prompt "Smoke test"  # e2e smoke
```

- Tests live in `tests/`, mirroring the source layout (e.g., `tests/handlers/test_history_handler.py`).
- File names: `test_*.py`. Function names: `test_*`.
- Mock external calls (CLI, filesystem, network). Aim for meaningful coverage, not 100%.

## Submitting a pull request

1. **Fork & branch.** Create a focused branch from `main` — one topic per branch.
2. **Keep it small.** A tight, reviewable diff is better than a sweeping change.
3. **Update docs** when behavior, setup, or user-facing output changes.
4. **Run checks** before pushing: `pytest -q && pre-commit run --all-files`.
5. **Write a clear PR description:** motivation, key changes, and how you verified it works.
6. **Verify locally** that the app runs on `:9000` / `:8765` before requesting review.

### Commit message format

```
<type>(<scope>): <subject in Korean>
```

Examples:
- `fix(server): WebSocket 연결 종료 시 세션 정리 누락`
- `feat(web): 토큰 사용량 표시 토글 추가`
- `docs(readme): 빠른 시작 가이드 보강`

## Reporting bugs

A good bug report includes:

- What you expected vs. what happened
- Steps to reproduce
- Environment: local or Docker, OS, Python version, AI provider
- Logs, screenshots, or exported data when helpful

## Proposing features

Feature requests work best when they explain:

- The problem or use case you're solving
- Current limitations or workarounds
- Expected behavior
- Any scope or compatibility concerns

## Documentation

README improvements, onboarding examples, Korean/English clarity fixes, and inline comment cleanups are all valuable. Docs contributions follow the same PR process.

## Security issues

For sensitive vulnerabilities, **do not** open a public issue. Follow the private reporting process in [SECURITY.md](SECURITY.md).

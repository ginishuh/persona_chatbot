# Repository Guidelines

## Project Structure & Module Organization
- `server/` – Python backend. Entry: `server/websocket_server.py`; shared logic in `server/handlers/` (file, Claude/Gemini/Droid, context, history, mode, workspace/git).
- `web/` – Static frontend (`index.html`, `app.js`, `style.css`) served by the Python HTTP helper.
- `STORIES/` – Saved narratives (markdown). Created on first run if missing.
- `chatbot_workspace/` – Chatbot-only workspace (reads `chatbot_workspace/CLAUDE.md`).
- `persona_data/` – Presets and workspace configuration (git-synced via UI).
- `scripts/` – Host-side helpers (`host_git_sync_once.sh`, `host_git_sync_watch.sh`).
- Root: `requirements.txt`, `Dockerfile*`, `docker-compose.yml`, `.env.example`, `README.md`.

## Build, Test, and Development Commands
- Create env: `python3 -m venv venv && source venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Claude CLI (first time): `claude auth login`
- Run locally: `python server/websocket_server.py`
  - HTTP: `http://localhost:9000` (static UI)
  - WebSocket: `ws://localhost:8765`
- Optional Docker (CLI auth inside containers is limited): `docker compose up --build`
  - Ports follow `.env` (`HTTP_PORT`, `WS_PORT`) for Docker only.

### Git Sync Modes (persona_data)
- The web UI "🔄 동기화" button operates on `persona_data/`.
- Two push modes are supported:
  - Container mode (default): container does `pull --rebase` → `commit` → `push`.
  - Host mode: set `APP_GIT_SYNC_MODE=host` in Compose → container writes a trigger file under `persona_data/.sync/` and host runner pushes (see `scripts/`).
- Host runner options:
  - One-shot: `scripts/host_git_sync_once.sh`
  - Watch: `scripts/host_git_sync_watch.sh` (or systemd user path unit)
- UI status icon mapping:
  - `✓ 동기화`: no local changes, ahead=0, behind=0
  - `🔄 동기화 ↑`: local changes or ahead>0 (push needed)
  - `🔄 동기화 ↓`: behind>0 (pull needed)
  - `🔄 동기화 ↑↓`: both

## Language Guidelines
- Default language is Korean for comments, docstrings, user‑facing copy, commit messages, PRs, and documentation.
- Exception: this "Repository Guidelines" file may remain in English.
- Prefer English identifiers (APIs, variable/class names) for interoperability; explain behavior in Korean comments/docstrings.

## Coding Style & Naming Conventions
- Python: PEP 8, 4‑space indent, type hints where practical, module/function `snake_case`, class `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Use `logging` (not `print`); include short docstrings for public functions.
- JS: ES6+ (`const`/`let`), small pure functions in `web/app.js`; keep DOM selectors and rendering logic separated.

## Testing Guidelines
- Framework: `pytest` (add when contributing).
- Location: `tests/` mirroring source paths (e.g., `tests/handlers/test_history_handler.py`).
- Naming: files `test_*.py`, functions `test_*`.
- Run: `pip install pytest && pytest -q`.
- Mock external calls (Claude CLI, filesystem, network). Aim for meaningful coverage of handlers.

## Commit & Pull Request Guidelines
- Commits: imperative mood with a scope prefix (e.g., `fix(server): ...`). Write the subject/description in Korean. Example: `fix(server): websockets v13 연결 종료 처리`.
- PRs: include problem/solution summary (Korean), local run steps, screenshots of UI changes, and linked issues. Keep PRs focused; avoid unrelated refactors. Verify the app runs at 9000/8765 before requesting review.

## Security & Configuration Tips
- Do not commit secrets. Copy `.env.example` to `.env` for Docker workflows; local run uses ports hardcoded in `websocket_server.py`.
- Mode switching: `server/handlers/mode_handler.py` can rename `AGENTS.md`/`CLAUDE.md` to `*.bak` in “chatbot” mode. Make edits and commits in “coding” mode.
 - For container push, prefer SSH credentials mounted read-only (e.g., `~/.ssh:/home/node/.ssh:ro`). Host-push mode avoids credentials inside the container entirely.

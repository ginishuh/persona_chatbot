# Repository Guidelines

## Project Structure & Module Organization
- `server/` – Python backend. Entry: `server/websocket_server.py`; shared logic in `server/handlers/` (file, Claude/Gemini/Droid, context, history, mode, workspace).
- `web/` – Static frontend (`index.html`, `app.js`, `style.css`) served by the Python HTTP helper.
- `persona_data/stories/` – Saved narratives (markdown). The legacy `STORIES/` folder is no longer used.
- `chatbot_workspace/` – Chatbot-only workspace (reads `chatbot_workspace/CLAUDE.md`).
- `persona_data/` – Presets and workspace configuration.
- Root: `requirements.txt`, `Dockerfile.full`, `docker-compose.yml.example`, `.env.example`, `README.md`.

## Build, Test, and Development Commands
- Create env: `python3 -m venv venv && source venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Claude CLI (first time): `claude auth login`
- Run locally: `python server/websocket_server.py`
  - HTTP: `http://localhost:9000` (static UI)
  - WebSocket: `ws://localhost:8765`
- Optional Docker: copy `docker-compose.yml.example` → `docker-compose.yml`, then `docker compose up --build`
  - Ports follow `.env` (`HTTP_PORT`, `WS_PORT`) for Docker only.

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
- Mode switching: UI control has been removed. The backend helper `server/handlers/mode_handler.py` still exists for scripted or manual use (renames `AGENTS.md`/`CLAUDE.md` to `*.bak`). Prefer doing edits/commits in "coding" mode if you use it manually.

## Current Status & Smoke Test

- As of 2025-11-10, all providers are verified working end-to-end: Claude ✅, Droid ✅, Gemini ✅ (both Docker and local runs).
- Quick smoke test script is provided at `scripts/ws_chat_test.py` (handles login, context setup, chat stream, and completion).

Examples:

```bash
# Start containers
docker compose up --build -d

# WebSocket smoke tests
python scripts/ws_chat_test.py --provider claude --prompt "Smoke: Claude"
python scripts/ws_chat_test.py --provider droid  --prompt "Smoke: Droid"
python scripts/ws_chat_test.py --provider gemini --prompt "Smoke: Gemini"
```

Notes:
- When `APP_LOGIN_PASSWORD` is set, ensure `APP_JWT_SECRET` is also set; the server enforces this at startup.
- For Docker, prefer host-absolute auth directories in `.env`:
  - `FACTORY_AUTH_DIR=$HOME/.factory`, `CLAUDE_AUTH_DIR=$HOME/.claude`, `GEMINI_AUTH_DIR=$HOME/.gemini`.

English | [한국어](README.ko.md)

# Persona Chat

> Turn a single chat window into a living table where characters talk, argue, and tell stories together.

[![CI](https://github.com/ginishuh/persona_chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/ginishuh/persona_chatbot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-brightgreen.svg)](https://www.docker.com/)

Persona Chat is an open-source web app that lets multiple AI characters hold a conversation in the same room — streamed live over WebSocket.
Think TRPG session, collaborative fiction workshop, or multi-voice brainstorm, all running locally on your machine.

Quick links: [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [License](LICENSE)

---

## Highlights

| What | Why it matters |
|------|---------------|
| **Multi-character rooms** | Several characters speak in sequence inside one session — party chat, not ping-pong. |
| **TRPG-style GM modes** | Choose aggressive, moderate, or passive AI game-master — or take the GM seat yourself. |
| **Live streaming** | Responses appear token-by-token over WebSocket; no waiting for a full reply. |
| **Swap providers on the fly** | Claude Code CLI, Gemini CLI, and Droid CLI all plug into the same interface. |
| **Narrative context panel** | Set the world, scenario, player character, NPCs, and GM style from a side panel — the AI reads it all. |
| **Export everything** | JSON, Zip, or NDJSON stream. Import back over WebSocket. Local storage and exports stay under your control. |

## Who This Is For

- **Writers & TRPG players** — run structured party conversations and scenario sessions in your browser.
- **Developers** — study a working example of multi-provider AI orchestration, WebSocket streaming, and session management.
- **Privacy-first users** — keep characters, stories, and auth state on your own machine. AI provider auth is needed, but nothing else leaves your control.

## Architecture at a Glance

```text
┌─────────────┐  WebSocket   ┌──────────────────────────────────┐
│  Browser UI  │◄────────────►│  Python server                   │
│  (web/)      │   JSON msgs  │  ├─ ws/        routing + actions │
└─────────────┘              │  ├─ handlers/  business logic    │
       ▲                     │  ├─ core/      session, auth     │
       │  HTTP :9000         │  └─ http/      static + export   │
       └─────────────────────┤                                  │
                             │  AI provider layer               │
                             │  ├─ Claude Code CLI              │
                             │  ├─ Gemini CLI                   │
                             │  └─ Droid CLI                    │
                             └──────────────────────────────────┘
```

## Quick Start

### Local run

**Requirements:** Python 3.11+, Node.js, at least one AI CLI authenticated locally.

```bash
# Install a provider (pick one or more)
npm install -g @anthropic-ai/claude-code && claude auth login
npm install -g @google/gemini-cli       && gemini auth login
curl -fsSL https://app.factory.ai/cli | sh && droid auth login
```

```bash
git clone https://github.com/ginishuh/persona_chatbot.git
cd persona_chatbot

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python3 -m server.websocket_server
# Web UI  → http://127.0.0.1:9000
# WS      → ws://127.0.0.1:8765
```

### Docker Compose

Pick an `.env` template from `examples/env/`, then:

```bash
cp docker-compose.yml.example docker-compose.yml
# edit .env as needed
docker compose up -d --build
docker compose logs -f
```

Docker ports follow `.env` (`HTTP_PORT`, `WS_PORT`).

<details>
<summary>Creating an admin account (when login is enabled)</summary>

Run inside the container to avoid SQLite locking:

```bash
docker compose exec persona-chatbot python3 -c "
from server.handlers.db_handler import DBHandler
import asyncio
async def create_admin():
    db = DBHandler('./data')
    await db.initialize()
    success = await db.create_admin_user('admin', 'password')
    print('Admin created' if success else 'Already exists')
asyncio.run(create_admin())
"
```
</details>

## Core Workflows

### Context & session control

The left-side workspace panel manages everything the AI reads before responding:

- **World & scenario** — set the stage once, reference it across the session.
- **Player character & NPCs** — define who's in the room and how they behave.
- **GM mode** — pick a game-master style or disable it entirely.
- **History window** — control how many past turns the AI sees, or go unlimited.
- **Session lifecycle** — retain sessions across reconnects, or reset on demand.

### Export & import

| Route | Format | Notes |
|-------|--------|-------|
| `GET /api/export` | JSON or Zip | Full snapshot download |
| `GET /api/export/stream` | NDJSON | Streaming export for large datasets |
| WebSocket `import_data` | JSON | Restore a previous export |
| `/backup` UI | — | Browser-based backup screen |

### WebSocket actions (selected)

```text
set_context / get_context          — read or write the narrative panel
chat / clear_history               — send a message or wipe the log
set_history_limit / reset_sessions — tune session behavior
list_files / read_file / write_file — workspace file ops
import_data                        — restore an export
```

### Workspace separation

Repository development instructions and chatbot runtime instructions live in separate spaces:

| File | Purpose |
|------|---------|
| Root `CLAUDE.md` | Dev guidance for contributors |
| `chatbot_workspace/CLAUDE.md` | Runtime instructions the chatbot reads |
| `chatbot_workspace/GEMINI.md` | Gemini-specific runtime instructions |

Sample files are provided — copy them to get started:

```bash
cp chatbot_workspace/CLAUDE.sample.md chatbot_workspace/CLAUDE.md
cp chatbot_workspace/GEMINI.sample.md chatbot_workspace/GEMINI.md
```

Character presets, worlds, and stories live under `persona_data/`. This folder works well as a separate private companion repository.

## Providers

| Provider | Auth | Session retention |
|----------|------|-------------------|
| Claude Code CLI | Local OAuth | Supported |
| Gemini CLI | Local OAuth | Supported |
| Droid CLI | OAuth or API key | Supported |

## Project Layout

```text
persona_chatbot/
├── server/                # Python backend — WS server, HTTP export, handlers
│   ├── core/              #   session, auth, app context
│   ├── handlers/          #   business logic per domain
│   ├── http/              #   static file serving + export API
│   └── ws/                #   WebSocket routing + action handlers
├── web/                   # Static frontend (vanilla JS)
├── tests/                 # pytest unit + e2e smoke tests
├── scripts/               # Maintenance & smoke-test utilities
├── chatbot_workspace/     # Chatbot runtime instructions (not dev docs)
├── persona_data/          # Characters, presets, worlds, stories
├── examples/env/          # .env templates for various setups
├── README.md              # ← you are here
└── README.ko.md
```

## Configuration

See `.env.example` and `examples/env/` for ready-to-use templates.

| Variable | Purpose |
|----------|---------|
| `APP_LOGIN_PASSWORD` | Enable simple password login |
| `APP_JWT_SECRET` | **Required** when login is enabled |
| `APP_ACCESS_TTL` / `APP_REFRESH_TTL` | Token lifetimes |
| `APP_BIND_HOST` | Bind address (default `127.0.0.1`) |
| `APP_PUBLIC_WS_URL` | External WebSocket URL for reverse-proxy setups |
| `SHOW_TOKEN_USAGE` | Toggle token usage display in the UI |
| `FACTORY_AUTH_DIR` / `CLAUDE_AUTH_DIR` / `GEMINI_AUTH_DIR` | Host auth directory mounts for Docker |

> **WSL tip:** Keep the SQLite database on the Linux filesystem, not under `/mnt/c`.

## Development

```bash
pip install -r requirements.txt
pytest -q
python scripts/ws_chat_test.py --provider claude --prompt "Smoke: Claude"
pre-commit run --all-files
```

CI (GitHub Actions) runs:
- `pre-commit` across the full repo
- `pytest` coverage for core handlers
- WebSocket e2e smoke tests from `tests/e2e`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, code style, and PR guidelines.
Bug reports, feature ideas, tests, and doc fixes are all welcome.
For anything bigger than a quick fix, open an issue first so we can align on scope.

## Security

See [SECURITY.md](SECURITY.md). Please report sensitive vulnerabilities privately — do not open a public issue.

## License

[MIT](LICENSE)

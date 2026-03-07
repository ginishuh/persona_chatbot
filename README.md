English | [한국어](README.ko.md)

# Persona Chat

> Open-source web app for multi-character AI conversation and narrative orchestration

[![CI](https://github.com/ginishuh/persona_chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/ginishuh/persona_chatbot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-brightgreen.svg)](https://www.docker.com/)

Persona Chat is a public open-source web application for running multi-character AI conversations in a browser. It combines real-time WebSocket streaming, CLI-backed AI providers, narrative context controls, and export workflows in a local-first workspace.

The project is useful both as a reusable tool and as a small reference implementation for people building or studying:

- multi-character roleplay and story rooms
- GM-assisted narrative sessions
- local/private AI chat workflows
- streaming chat apps that coordinate multiple AI backends

Quick links: [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [License](LICENSE)

## Why Persona Chat

- **Multi-character conversation**: run rooms where several characters respond inside the same session.
- **Narrative orchestration**: manage world setup, current situation, player character, NPCs, and GM-style modes.
- **Real-time streaming**: receive chat output over WebSocket as it is generated.
- **Multiple AI providers**: switch between Claude Code CLI, Gemini CLI, and Droid CLI.
- **Context and session controls**: use a sliding history window, unlimited mode, session retention, and manual resets.
- **Export and backup workflows**: export rooms and history via JSON, Zip, or NDJSON streaming, and import data over WebSocket.
- **Local-first operation**: keep `persona_data`, authentication state, and story logs in your own environment.

## Who This Is For

- writers, roleplay users, and TRPG players who want a structured local workspace
- developers exploring multi-provider AI orchestration patterns
- teams that want a browser-based reference implementation for streaming AI chat
- users who prefer private, self-hosted workflows over a hosted SaaS product

## Common Use Cases

- running a party chat where multiple characters speak in sequence
- orchestrating AI-assisted scenario sessions with or without a GM
- maintaining local narrative logs and exporting them for backup or review
- testing how different CLI-based AI providers behave in the same interface

## Quick Start

### Local run

Requirements:

- Python 3.11 or newer
- Node.js for AI CLI installation
- at least one supported AI CLI authenticated locally

Provider setup examples:

```bash
# Claude Code
npm install -g @anthropic-ai/claude-code
claude auth login

# Gemini CLI
npm install -g @google/gemini-cli
gemini auth login

# Droid CLI
curl -fsSL https://app.factory.ai/cli | sh
droid auth login
```

Run the app:

```bash
git clone https://github.com/ginishuh/persona_chatbot.git
cd persona_chatbot

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 -m server.websocket_server
```

Default local endpoints:

- Web UI: `http://127.0.0.1:9000`
- WebSocket: `ws://127.0.0.1:8765`

### Docker Compose

Choose the `.env` example that matches your environment from `examples/env/`, then:

```bash
cp docker-compose.yml.example docker-compose.yml
docker compose up -d --build
docker compose logs -f
```

For Docker deployments, ports follow `.env` (`HTTP_PORT`, `WS_PORT`).

If login is enabled, create the admin account inside the container to avoid SQLite locking issues:

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

## Core Workflows

### Context and session control

The left-side workspace manages:

- world and scenario context
- player character and NPC definitions
- GM mode selection
- context window length
- session retention and session reset

### Export and import

- HTTP export endpoints: `GET /api/export`, `GET /api/export/stream`
- export formats: JSON, Zip, NDJSON stream
- import path: WebSocket `import_data` action
- backup UI: available in the `/backup` screen

### WebSocket interface

WebSocket messages use JSON payloads. Common actions include:

- `set_context`, `get_context`
- `chat`, `clear_history`, `get_narrative`
- `set_history_limit`, `set_session_retention`, `reset_sessions`
- `list_files`, `read_file`, `write_file`
- `import_data`

### Workspace separation

The repository separates chatbot-specific instructions from repository development instructions:

- root `CLAUDE.md`: repository development guidance
- `chatbot_workspace/CLAUDE.md`: chatbot runtime guidance
- `chatbot_workspace/GEMINI.md`: Gemini runtime guidance

Sample files are provided and can be copied locally:

```bash
cp chatbot_workspace/CLAUDE.sample.md chatbot_workspace/CLAUDE.md
cp chatbot_workspace/GEMINI.sample.md chatbot_workspace/GEMINI.md
```

The application expects the folder name `persona_data/` and works well with a separate private companion repository for character presets, worlds, and story data.

## Providers

- **Claude Code CLI**: OAuth-based local authentication, session retention supported
- **Gemini CLI**: OAuth-based local authentication, session retention supported
- **Droid CLI**: OAuth or API key, session retention supported

## Project Layout

```text
persona_chatbot/
├── server/                # Python backend, WebSocket server, HTTP export API
├── web/                   # Static frontend
├── tests/                 # Pytest coverage and e2e smoke tests
├── scripts/               # Smoke tests and maintenance utilities
├── chatbot_workspace/     # Chatbot-only runtime instructions
├── persona_data/          # Characters, presets, worlds, stories
├── examples/env/          # Environment templates
├── README.md
└── README.ko.md
```

## Configuration Notes

See `.env.example` and `examples/env/` for concrete templates. Key settings include:

- `APP_LOGIN_PASSWORD` and `APP_JWT_SECRET` for optional login protection
- `APP_ACCESS_TTL` and `APP_REFRESH_TTL` for token lifetime control
- `APP_BIND_HOST` for local binding security
- `APP_PUBLIC_WS_URL` for externally exposed deployments
- `SHOW_TOKEN_USAGE` to toggle token usage display
- `FACTORY_AUTH_DIR`, `CLAUDE_AUTH_DIR`, `GEMINI_AUTH_DIR` for host auth mounts

For WSL, prefer storing the SQLite database on the Linux filesystem rather than under `/mnt/c`.

## Development

```bash
pip install -r requirements.txt
pytest -q
python scripts/ws_chat_test.py --provider claude --prompt "Smoke: Claude"
pre-commit run --all-files
```

GitHub Actions currently runs:

- `pre-commit` on the full repository
- `pytest` coverage checks for core handlers
- WebSocket e2e smoke tests from `tests/e2e`

Documentation improvements are welcome alongside code changes.

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports, feature proposals, tests, and documentation cleanups are all welcome. For major changes, open an issue first so scope and direction can be discussed before implementation.

## Security

Please see [SECURITY.md](SECURITY.md). Do not open public issues for sensitive vulnerabilities.

## License

This project is available under the [MIT License](LICENSE).

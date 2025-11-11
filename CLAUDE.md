# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Persona Chat is a web-based multi-character conversation system for interactive storytelling. It uses Claude Code CLI as the AI backend, WebSocket for real-time communication, and supports TRPG-style game master features with conversation history management.

**Key Feature**: The chatbot runs in an isolated workspace (`chatbot_workspace/`) with its own CLAUDE.md that contains adult content guidelines and character performance instructions. This isolation prevents those instructions from affecting development work.

## Language Convention

**All documentation, commit messages, code comments, and user-facing communication should be written in Korean (한국어).**

**Exceptions:**
- Agent instruction files (`CLAUDE.md`, `agents.md`) should remain in English for compatibility
- Code identifiers (variable names, function names, class names) should use English
- Technical terms and API references can use English when appropriate

This applies to:
- README files and project documentation
- Commit messages (except the Claude Code footer)
- Code comments and docstrings
- User interface text
- Error messages and logs
- Development notes and TODOs

## Architecture

### Core Communication Flow

```
Browser (WebSocket Client)
  ↓
WebSocket Server (port 8765)
  ↓
Handler Layer (context, history, claude)
  ↓
Claude Code CLI (subprocess, stream-json)
  ↓
System Prompt (context + history injected)
```

**Critical Design**: Each chat message spawns a NEW Claude Code process. Session continuity is achieved by injecting conversation history into the system prompt, not by maintaining a persistent process.

### Directory Structure

```
persona_chatbot/
├── server/
│   ├── websocket_server.py          # Main server with action routing
│   └── handlers/
│       ├── claude_handler.py        # Claude Code subprocess management
│       ├── context_handler.py       # System prompt builder
│       ├── history_handler.py       # Sliding window conversation memory
│       ├── file_handler.py          # File operations
│       └── workspace_handler.py     # Persona data management
├── web/                             # Static frontend (HTML/CSS/JS)
├── chatbot_workspace/               # Isolated Claude Code workspace
│   └── CLAUDE.md                    # Chatbot-specific instructions (adult mode, character acting)
└── .claude/
    └── CLAUDE.md                    # Development instructions (this file)
```

### Handler Architecture

**ContextHandler** (`context_handler.py`)
- Builds system prompts with world, situation, characters, and narrator settings
- Supports three narrator modes: AI GM (active/moderate/passive), user GM, or no GM
- Injects adult mode directives when enabled
- Methods: `build_system_prompt(history_text)`, `set_world()`, `set_characters()`, etc.

**HistoryHandler** (`history_handler.py`)
- Maintains a sliding window for context; default is 30 turns via server config (`HistoryHandler(max_turns=30)`).
- Converts the current window to text for system prompt injection.
- Keeps a full transcript for narrative export.
- Methods: `add_user_message()`, `add_assistant_message()`, `get_history_text()`, `get_narrative_markdown()`, `set_max_turns()`

**ClaudeHandler** (`claude_handler.py`)
- Spawns subprocess: `CLAUDE_PATH` (env) with `--print --verbose --output-format stream-json --setting-sources user,local`
- **Working directory**: `chatbot_workspace/` (reads `chatbot_workspace/CLAUDE.md` only)
- Streams JSON responses via stdout; reads stderr asynchronously to avoid blocking.
- 120-second timeout per message.
- The process exits per message after stdin is closed (stateless per call).

### WebSocket API

Server listens on `0.0.0.0:8765`, handles these actions:
- `set_context` - Configure world, characters, narrator mode, adult mode
- `get_context` - Retrieve current context
- `chat` - Send message (returns `chat_stream` events + `chat_complete`)
- `clear_history` - Reset conversation memory
- `get_narrative` - Get markdown formatted conversation history
- `list_files`, `read_file`, `write_file` - File operations

### Frontend Message Parsing

The frontend (`web/app.js`) parses Claude responses using regex:
```javascript
/^\[(.+?)\]:\s*(.*)$/  // Matches "[CharacterName]: dialogue"
```

Each character gets assigned a color class (`character-0` through `character-4`), and `[진행자]` gets special gold styling.

## Running the Project

### Development Server

```bash
# Start server (from project root)
python3 server/websocket_server.py

# Or with venv
./venv/bin/python server/websocket_server.py
```

Servers start on:
- HTTP: `http://localhost:9000` (static files from `web/`)
- WebSocket: `ws://localhost:8765`

### Requirements

- Python 3.8+
- Claude Code CLI installed and authenticated (`claude auth login`)
- Dependencies in `requirements.txt`: websockets 12.0, aiofiles 23.2.1

### Kill Existing Server

```bash
pkill -f "python.*websocket_server.py"
# Or
lsof -ti:8765 | xargs -r kill -9
lsof -ti:9000 | xargs -r kill -9
```

## Common Development Tasks

### Modifying System Prompt Generation

Edit `server/handlers/context_handler.py` → `build_system_prompt()` method. This function concatenates:
1. Narrator mode header (GM vs character-only mode)
2. Adult mode directives (if enabled)
3. World description
4. Current situation
5. User character
6. Narrator settings (if enabled)
7. Character descriptions
8. **History text** (from HistoryHandler)
9. Conversation rules

### Adjusting History Window Size

Edit `server/websocket_server.py` line 28:
```python
history_handler = HistoryHandler(max_turns=15)  # Change this number
```

### Changing Claude Code Execution Path

Edit `server/handlers/claude_handler.py` → `__init__()`:
```python
def __init__(self, claude_path="/home/ginis/.nvm/versions/node/v22.17.1/bin/claude"):
```

### Testing WebSocket Manually

```javascript
const ws = new WebSocket('ws://localhost:8765');
ws.onopen = () => {
  ws.send(JSON.stringify({
    action: "chat",
    prompt: "안녕?"
  }));
};
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## Important Technical Constraints

### Claude Code Process Lifecycle

**Problem**: Cannot maintain a persistent Claude Code subprocess across multiple messages because closing stdin terminates the process.

**Solution**: Start fresh process for each message, inject full conversation history into system prompt. This is handled automatically by:
1. `HistoryHandler` accumulates messages
2. `ContextHandler.build_system_prompt()` includes history text
3. `ClaudeHandler` sends combined prompt to new process

### Workspace Isolation

The chatbot runs from `chatbot_workspace/` as its working directory. This ensures:
- Chatbot reads `chatbot_workspace/CLAUDE.md` (contains adult content directives)
- Development sessions read `.claude/CLAUDE.md` (this file, for code work)
- No cross-contamination of instructions

**Never modify** `chatbot_workspace/CLAUDE.md` during development work unless explicitly requested by user.

### WebSocket Handler Signature

Uses websockets v13+ API:
```python
async def websocket_handler(websocket):  # No 'path' parameter
```

Older versions (v12 and below) required `async def websocket_handler(websocket, path)`.

## Debugging

### Enabling Verbose Logging

Change logging level in `server/websocket_server.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # Was INFO
```

### Claude Code stderr Output

Check `claude_handler.py` line 99 for stderr logging. Increase verbosity or remove the try-except to see raw errors.

### Character Color Assignment

Characters are assigned colors by hashing their name modulo 5. See `web/app.js`:
```javascript
const colorClass = `character-${characterColorMap.size % 5}`;
```

## Project-Specific Conventions

- All WebSocket messages are JSON with `{ "action": "...", "data": { ... } }`
- Character dialogue format: `[CharacterName]: dialogue text`
- Narrator uses special tag: `[진행자]: situation description`
- History default: 30 turns (sliding window); adjustable at runtime via UI/API
- Adult mode content guidelines are in `chatbot_workspace/CLAUDE.md` only
- Server must be restarted after code changes (no hot reload)

---

Note: Chatbot-specific creative/NSFW directives live in `chatbot_workspace/CLAUDE.md` and are intentionally isolated from this root developer guide.

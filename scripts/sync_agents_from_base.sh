#!/usr/bin/env bash
set -euo pipefail

# Thin wrapper for consistency with other repos:
# use `bash scripts/sync_agents_from_base.sh` here as well.

python3 scripts/sync_docs.py

echo "Done. Stage and commit if needed: git add AGENTS.md CLAUDE.md GEMINI.md .github/copilot-instructions.md .github/instructions/review-language.instructions.md && git commit -m 'docs(agents): sync replicas from base'"

# Cowork-Local v3.2

## Modes
- **Cowork**: `python apps/cli/cowork_graph.py "task"` — multi-agent, Planner(Pro) + Worker(OpenCode/Flash FREE), 5 iteraciones, timeout 600s, pytest + Telegram al terminar
- **Code**: `opencode run "prompt"` — OpenCode CLI directo con Flash FREE, respuestas rápidas

## Models
- Planner/Reviewer: deepseek-v4-pro (paid, ~$0.001/proyecto)
- Worker: opencode/deepseek-v4-flash-free (FREE)
- Local backup: qwen3:14b via Ollama

## Rules
- Generate code, don't explain. Don't modify files without asking. Use absolute paths.
- See `rules/api.md` and `rules/security.md` for detailed conventions.

## Key Tools
- `python apps/cli/cowork_graph.py "task"` — full project generation with auto-tests + auto-install
- `python apps/cli/search_tools.py search "query"` — grep codebase
- `python apps/cli/apply_diff.py change file "old" "new"` — safe text replacement
- `python apps/cli/session_memory.py save/load` — PostgreSQL persistence

## Infrastructure
- PostgreSQL (sessions, artifacts, invoices) + Redis (graph state, planner cache)
- n8n on :5678 with native MCP. Skills in `.opencode/skills/n8n/`. Invoice Bot 24/7
- Graphify: 771 nodes mapped. Run `graphify update .` after code changes. Planner reads it automatically
- 16 MCP servers in `.mcp.json` + n8n-mcp
- VS Code: `opencode-vscode` plugin. Web UI: `opencode web`
- Telegram notifications via n8n webhook on every project completion

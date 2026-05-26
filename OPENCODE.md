# Cowork-Local v3.2

## Modes
- **Cowork**: `python apps/cli/cowork_graph.py "task"` — multi-agent, Planner(Pro) + 3 workers (OpenCode/OpenDesign/MCP), 5 iteraciones, timeout 600s
- **Code**: `opencode run "prompt"` — OpenCode CLI directo con Flash FREE, respuestas rápidas
- **Assistant**: Telegram bot (@byron92m_bot) — asistente personal 24/7

## Architecture
LangGraph con sub-grafos independientes por worker:
- `code_worker` → OpenCode + Flash FREE → proyectos Python
- `design_worker` → OpenDesign (API) → diseño UI/UX, landing pages, dashboards
- `mcp_worker` → 6 tools → filesystem, document, web, shell, chat, edit

## Models
- Planner/Reviewer: deepseek-v4-pro (~$0.001/proyecto)
- Code worker: opencode/deepseek-v4-flash-free (FREE)
- Design worker: OpenCode via OpenDesign daemon (FREE)
- MCP worker: local tools + OpenCode Flash FREE para chat y edit
- Local backup: qwen3:14b via Ollama

## Rules
- Generate code, don't explain. Don't modify files without asking. Use absolute paths.
- See `rules/api.md` and `rules/security.md` for detailed conventions.

## Telegram Assistant
- Chat multi-sesión: /list, /switch, /nueva, /cerrar, /estado, /pc, /ayuda
- Memoria entre mensajes vía Redis (historial de conversación)
- Clasificación automática de intención vía DeepSeek Pro
- Seguridad: whitelist Chat ID, --confirm para tool_shell y tool_web

## Infrastructure
- PostgreSQL (sessions, artifacts, invoices) + Redis (graph state, chat history, cache)
- Graphify: knowledge graph del codebase
- 16 MCP servers in `.mcp.json` + n8n-mcp
- VS Code: `opencode-vscode` plugin
- Playwright: Chromium aislado en `/browsers/`

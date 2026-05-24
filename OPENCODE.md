# Cowork-Local v3.2

## Modes
- **Cowork**: `python apps/cli/cowork_graph.py "task"` — multi-agent, Planner(Pro) + Worker(OpenCode/Flash FREE), 5 iteraciones, timeout 600s, pytest + Telegram al terminar
- **Code**: `opencode run "prompt"` — OpenCode CLI directo con Flash FREE, respuestas rápidas
- **Assistant**: Telegram bot (@byron92m_bot) — asistente personal 24/7 con 5 herramientas reales

## Models
- Planner/Reviewer: deepseek-v4-pro (paid, ~$0.001/proyecto)
- Worker: opencode/deepseek-v4-flash-free (FREE)
- Local backup: qwen3:14b via Ollama

## Rules
- Generate code, don't explain. Don't modify files without asking. Use absolute paths.
- See `rules/api.md` and `rules/security.md` for detailed conventions.

## Tools (5 reales)
- `tool_filesystem`: Buscar archivos con os.walk
- `tool_document`: Leer PDF, Excel, CSV, TXT, MD, JSON, LOG
- `tool_web`: Navegar internet con Playwright (Chromium headless)
- `tool_shell`: Ejecutar comandos (requiere --confirm)
- `code_generation`: Crear proyectos Python con OpenCode + pytest

## Telegram Assistant
- Chat multi-sesión: /list, /switch, /nueva, /cerrar, /estado, /pc, /ayuda
- Memoria entre mensajes vía Redis (historial de conversación)
- Clasificación automática de intención vía DeepSeek Pro
- Seguridad: whitelist Chat ID, --confirm para acciones peligrosas

## Infrastructure
- PostgreSQL (sessions, artifacts, invoices) + Redis (graph state, chat history, cache)
- Graphify: 771 nodes mapped. Planner reads GRAPH_REPORT.md automatically
- 16 MCP servers in `.mcp.json` + n8n-mcp
- VS Code: `opencode-vscode` plugin. Web UI: `opencode web`
- Playwright: Chromium aislado en `/browsers/`

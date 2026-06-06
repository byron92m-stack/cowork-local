# Cowork-Local v3.3

## Modes
- **Cowork**: `python apps/cli/cowork_graph.py "task"` — multi-agent, Planner(Pro) + 3 workers (OpenCode/OpenDesign/MCP), 5 iteraciones, timeout 600s
- **Code**: `opencode run "prompt"` — OpenCode CLI directo con Flash FREE
- **Assistant**: Telegram bot (@byron92m_bot)

## Architecture
LangGraph con sub-grafos independientes:
- `code_worker` → OpenCode + Flash FREE → Python projects, scripts, PowerPoints
- `design_worker` → OpenDesign API (port 34095) → UI/UX
- `mcp_worker` → tools: filesystem, document, web, shell, chat, edit, mail, calendar, skills

## Models
- Planner/Reviewer: deepseek-v4-pro
- Code/Design: opencode/deepseek-v4-flash-free (FREE)
- MCP chat: deepseek-chat

## PDF Processing
- Use `project_path` parameter, not in query string
- Extracts all pages (no limit)
- Extracts all text (no 1000 char limit)

## Code Generation
- Prompt requests JSON: `{"code": "script here"}`
- `clean_code()` handles JSON + markdown
- Scripts are saved AND executed automatically

## Email
- Provider: Mail.ru (josue.martinez.593@mail.ru)
- SMTP: smtp.mail.ru:465 SSL
- IMAP: imap.mail.ru:993 SSL
- Auth: App password (2FA activado)
- Tools: mail_send, mail_read, calendar_add, send_email (skills)
- Config: MAIL_USER, MAIL_PASSWORD, MAIL_SMTP_HOST, MAIL_SMTP_PORT, MAIL_IMAP_HOST, MAIL_IMAP_PORT

## Rules
- Generate code, don't explain. Use absolute paths.
- For long content: save to file first, then reference path
- See `rules/api.md` and `rules/security.md`

## Telegram Assistant
- Commands: /list, /switch, /nueva, /cerrar, /estado, /pc, /ayuda
- Redis memory, whitelist Chat ID, --confirm for shell/web

## Infrastructure
- PostgreSQL + Redis
- Graphify knowledge graph
- 16 MCP servers, Playwright in `/browsers/`

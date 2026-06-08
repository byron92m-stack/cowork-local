# Cowork-Local v3.4.1

## Modes
- **Cowork**: `python apps/cli/cowork_graph.py "task"` — multi-agent, Planner(Pro) + 4 workers (+ Booking), 5 iteraciones, timeout 600s
- **Code**: `opencode run "prompt"` — OpenCode CLI directo con Flash FREE
- **Assistant**: Telegram bot (@byron92m_bot)

## Architecture
LangGraph con sub-grafos independientes:
- `code_worker` → OpenCode + Flash FREE → Python projects, scripts, PowerPoints
- `design_worker` → OpenDesign API (port 34095) → UI/UX
- `mcp_worker` → tools: filesystem, document, web, shell, edit, mail, calendar, skills
- `booking_worker` → medical appointment booking (Telegram + Email)

## Models
- Planner: deepseek-reasoner (Pro)
- Code: opencode/deepseek-v4-flash
- MCP edit: opencode/deepseek-v4-flash
- Booking: deepseek-chat (Flash)
- MCP chat: disabled (use codewhale-tui)

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


## Booking Agency (v3.4)
- Medical appointments via Telegram (@byron92m_bot) + Email
- Patient ID: cédula/RUC/passport with validation
- Flow: ID → name+email → intent → date (dateparser+Flash) → time → confirm
- DB: patients, appointments, availability, email_queue
- Redis session by doc_id (2h TTL), ICS invitations, 24h reminders
- Commands: /start, /citas, /cancelar, /ayuda, /reset

## Rules
- Generate code, don't explain. Use absolute paths.
- For long content: save to file first, then reference path
- See `rules/api.md` and `rules/security.md`

## Telegram Assistant
- Booking bot with appointment agency + legacy Cowork
- Booking commands: /start, /citas, /cancelar, /ayuda, /reset
- Legacy: /list, /switch, /nueva, /cerrar, /estado, /pc
- Multi-session by doc_id, 24h APScheduler reminders, rate limiting

## Infrastructure
- PostgreSQL + Redis
- Graphify knowledge graph
- 16 MCP servers, Playwright in `/browsers/`, APScheduler for reminders

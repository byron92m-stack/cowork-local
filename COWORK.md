# Cowork-Local v3.4.1

## Modes
- **Cowork**: `python apps/cli/cowork_graph.py "task"` — multi-agent, Planner(Pro) + 4 workers (+ Booking), 5 iterations, timeout 600s
- **Code**: `opencode run "prompt"` — OpenCode CLI direct with Flash
- **Assistant**: Telegram bot (@byron92m_bot)
- **OpenCode Pro**: `cd ~/opencode-pro && opencode --model deepseek/deepseek-v4-pro` — independent collaborative assistant (read-only)

## Architecture
LangGraph with independent sub-graphs. All Redis operations wrapped in _redis_safe() — never crashes on connection failure.
- `code_worker` → OpenCode agent mode (deepseek/deepseek-v4-flash API direct) → Python projects, scripts, PowerPoints. Native tools (Read, Write, Glob, Shell). sys.executable, -- flag protection, exec_failed validation.
- `codewhale_worker` → CodeWhale agent mode (exec --auto) → 30+ tools: filesystem, document, web, shell, edit, search. Chat disabled.
- `design_worker` → OpenDesign API (port 34095) → UI/UX. Daemon at workers/open-design/. Healthcheck, graceful offline handling.
- `booking_worker` → Medical appointment booking (Telegram + Email). Async Redis wrappers.
- Both code_worker and codewhale_worker share COWORK_DIR as cwd for full project visibility and multi-worker collaboration.

## Workers Directory
All worker binaries and services in workers/:
- workers/codewhale/ — CodeWhale TUI + .codewhale config (30+ tools)
- workers/opencode-pro/ — Reserved for future OpenCode Pro assistant
- workers/open-design/ — OpenDesign daemon (UI/UX, port 34095)

## Models
- Planner: deepseek-reasoner (Pro) via DeepSeekClient
- Code worker: deepseek/deepseek-v4-flash (API direct, agent mode, -- flag protected)
- CodeWhale worker: deepseek-v4-flash (API direct, exec --auto)
- Booking: deepseek-chat (Flash) via httpx
- Design: OpenDesign daemon (no cost)
- MCP chat: disabled (use codewhale-tui)

## PDF Processing
- Use `project_path` parameter, not in query string
- Extracts all pages (no limit)
- Extracts all text (no 1000 char limit)

## Code Generation
- OpenCode uses agent mode with native tools — no forced JSON format
- Generated files saved in output/projects/{project_name}/
- Main script auto-detected (prioritizes main.py, app.py, or largest .py file)
- Scripts executed with sys.executable, validated via returncode + "OK" check
- Prompt protected with -- flag to prevent injection

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
- All Redis ops async via run_in_executor
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
- PostgreSQL + Redis (_redis_safe wrapper)
- Graphify: 34,248 nodes, 50,881 edges
- 14 MCP servers, Playwright in `/browsers/`, APScheduler for reminders
- 212 Python files syntax-verified, 26+ bugs fixed, production ready

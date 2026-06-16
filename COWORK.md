# Cowork-Local v3.4.1

## Modes
- **Cowork**: `python apps/cli/cowork_graph.py "task"` — multi-agent, Planner(Pro) + 5 workers, 5 iterations, timeout 600s
- **Code**: `opencode run "prompt"` — OpenCode CLI direct with Flash
- **Assistant**: Telegram bot (@byron92m_bot)
- **Langcli Pro**: `cd ~/chat-colaborativo && ./start.sh` — independent collaborative assistant (read-only, DeepSeek V4 Pro)

## Architecture
LangGraph with independent sub-graphs. All Redis operations wrapped in _redis_safe(). All subprocess calls use sys.executable and -- flag protection. Workers share COWORK_DIR as cwd for full project visibility and multi-worker collaboration.

- `code_worker` → OpenCode agent mode (deepseek/deepseek-v4-flash API direct) → Python projects, scripts, PowerPoints. Native tools (Read, Write, Glob, Shell). exec_failed validation.
- `codewhale_worker` → CodeWhale agent mode (exec --auto) → 30+ tools: filesystem, document, web, shell, edit, search. Chat disabled.
- `design_worker` → OpenDesign API (port 34095) → UI/UX, marketing posters. Daemon at workers/open-design/.
- `booking_worker` → Medical appointment booking via Telegram. Async Redis wrappers. doc_id as universal key.
- `accounting_worker` → SRI invoice extraction from XML/PDF email attachments. Deterministic, no LLM. Saves to invoices table.
- Marketing campaigns → sub-nodes of `design_worker` (campaign_generate, campaign_view, campaign_approve, campaign_list).

## Workers Directory
All worker binaries and services in workers/: codewhale (CodeWhale TUI, 30+ tools), opencode-pro (reserved), open-design (OpenDesign daemon, UI/UX, port 34095).

## Models
- Planner: deepseek-reasoner (Pro) via DeepSeekClient
- Code worker: deepseek/deepseek-v4-flash (API direct, agent mode, -- flag protected)
- CodeWhale worker: deepseek-v4-flash (API direct, exec --auto)
- Booking: deepseek-chat (Flash) via httpx
- Design: OpenDesign daemon (no cost)
- Accounting: no LLM (deterministic XML/PDF extraction)
- Marketing campaigns: sub-nodes of design_worker, no extra cost
- MCP chat: disabled (use codewhale-tui)

## PDF Processing
Use project_path parameter. Extracts all pages and all text with no limits.

## Code Generation
OpenCode uses agent mode with native tools — no forced JSON format. Generated files saved in output/projects/{project_name}/. Main script auto-detected. Scripts executed with sys.executable, validated via returncode + "OK" check. Prompt protected with -- flag.

## Accounting
IMAP polling via accounting_poller.py. Extracts SRI invoice data from XML (Clark notation with namespace detection) and PDF (regex). Saves to invoices table with duplicate detection. No LLM required.

## Marketing
Weekly campaigns via python apps/cli/cowork_graph.py --design [generate|view|approve|list] (or tools/marketing_scheduler.py). Templates rotate by weekday. Output: output/design/, approved: output/marketing/approved/.

## Email
Provider: Mail.ru (josue.martinez.593@mail.ru). SMTP: smtp.mail.ru:465 SSL. IMAP: imap.mail.ru:993 SSL. Auth: App password with 2FA. Rate limit: 1 email/minute. Config in .env: MAIL_USER, MAIL_PASSWORD, MAIL_SMTP_HOST, MAIL_SMTP_PORT, MAIL_IMAP_HOST, MAIL_IMAP_PORT.

## Booking Agency (v3.4)
Medical appointments via Telegram (@byron92m_bot). Patient ID: cédula/RUC/passport with validation. Flow: ID → name+email → intent → date (dateparser+Flash) → time → confirm. DB: patients, appointments, availability, email_queue. Redis session by doc_id (2h TTL), ICS invitations, 24h reminders. All Redis ops async via run_in_executor. Commands: /start, /citas, /cancelar, /ayuda, /reset.

## Rules
Generate code, don't explain. Use absolute paths. For long content: save to file first, then reference path. See rules/api.md and rules/security.md.

## Telegram Assistant
Booking bot @byron92m_bot with commands: /start, /citas, /cancelar, /ayuda, /reset. Legacy: /list, /switch, /nueva, /cerrar, /estado, /pc. Multi-session by doc_id, 24h APScheduler reminders, rate limiting.

## Infrastructure
PostgreSQL with 14 tables (8 Cowork + 6 booking + 1 accounting). Redis with _redis_safe wrapper. Graphify: 34,332 nodes, 50,990 edges. 16 MCP servers. Playwright in /browsers/. APScheduler for reminders and email queue. 84 Python files syntax-verified, 26+ bugs fixed, production ready.

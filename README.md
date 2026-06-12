# Cowork-Local v3.4.1

Local multi-agent development assistant with 5 specialized workers running on LangGraph. Planner uses DeepSeek Reasoner (Pro). Workers use deepseek/deepseek-v4-flash (API direct), deepseek-v4-flash (CodeWhale), or deepseek-chat (Flash). Total cost approximately $0.50 per month. Booking adds ~$0.30/month per 1000 appointments. Accounting and Marketing workers add no extra cost.

## Architecture

The Planner (DeepSeek Pro) classifies user intent into 9 types and routes to the correct worker via conditional edges. Workers share COWORK_DIR as cwd for full project visibility and multi-worker collaboration. All Redis operations use _redis_safe() wrapper for resilience. Subprocess calls use sys.executable and -- flag protection.

Workers: code_worker generates Python projects via OpenCode in agent mode with native tools (Read, Write, Glob, Shell). codewhale_worker provides 30+ tools via CodeWhale agent mode for filesystem, document, web, shell, and editing tasks. design_worker generates UI/UX and marketing art via OpenDesign API on port 34095. booking_worker handles medical appointments via Telegram with Redis sessions keyed by doc_id. accounting_worker extracts invoice data from SRI XML and PDF attachments via IMAP polling. marketing campaigns are handled by design_worker via campaign_generate, campaign_view, campaign_approve, campaign_list nodes.

All state definitions in state.py: CoworkState, CodeWorkerState, DesignWorkerState, BookingState, AccountingState. Step class, plan field, add_step, is_complete, get_pending_steps, get_current_step, and summary removed in Phase 35 cleanup.

## Workers

### code_worker
Generates and executes Python code using OpenCode in agent mode with native tools (Read, Write, Glob, Shell). No forced JSON format. Generated files saved to output/projects/{project_name}/. Main script auto-detected by find_generated_script() prioritizing main.py, app.py, or largest .py file. Execution validated via returncode and OK check. Prompt protected with -- flag. Uses deepseek/deepseek-v4-flash (API direct). Subprocess timeout 600s, script timeout 120s.

### codewhale_worker
CodeWhale in agent mode (exec --auto) with 30+ tools: filesystem search, document analysis, web navigation, shell execution, file editing. Chat disabled. Works in COWORK_DIR with full project access. Uses deepseek-v4-flash via CodeWhale CLI. Binary at workers/codewhale/codewhale with dynamic path detection. Subprocess timeout 120s.

### design_worker
OpenDesign daemon proxy on port 34095. Generates web prototypes, landing pages, UI/UX, and marketing posters. Healthcheck before calling. Consumes SSE stream from OpenDesign API. Saves output to output/design/. Daemon at workers/open-design/. Skill parameter supports frontend, poster, social-media.

### booking_worker
Medical appointment booking agency with 8-node LangGraph state machine. Patient identification by cédula/RUC/passport with validation algorithm. Flow: ID extraction via LLM, name and email collection, intent classification via DeepSeek Flash, date parsing with dateparser + Flash confirmation, slot selection with regex extraction. Channels: Telegram (@byron92m_bot) only. Email channel moved to accounting. DB tables: patients, appointments, availability, email_queue, faqs, appointment_history. Redis session state by doc_id with 2h TTL. ICS calendar invitations via email queue respecting Mail.ru 1/min rate limit. All Redis operations use async wrappers (save_booking_state_async, delete_booking_state_async) with run_in_executor. 24h reminders via APScheduler. Commands: /start, /citas, /cancelar, /ayuda, /reset. Security: rate limiting (15 msg/min Telegram), input sanitization, prompt injection defense.

### accounting_worker
Extracts invoice data from SRI electronic invoices (XML and PDF). Single-node LangGraph subgraph. XML extraction uses Clark notation with automatic namespace detection. PDF extraction uses regex patterns for RUC, invoice number, total, and date. Saves to invoices table in PostgreSQL with UNIQUE constraint on (numero_factura, ruc_emisor). Duplicate detection prevents re-processing. No LLM required — deterministic extraction. IMAP polling via accounting_poller.py processes UNSEEN emails with attachments matching invoice patterns. Table: invoices (id, numero_factura, ruc_emisor, razon_social, fecha_emision, subtotal, iva, total, source_email, attachment_path, raw_data JSONB, created_at).

### marketing (design_worker sub-nodes)
Weekly campaign art generation using design_worker sub-nodes (campaign_generate, campaign_view, campaign_approve, campaign_list). Invoked via python apps/cli/cowork_graph.py --design [generate|view|approve|list] or python tools/marketing_scheduler.py. Campaign templates rotate by weekday. Output saved to output/design/, approved to output/marketing/approved/.

## OpenCode Pro Assistant
Independent collaborative coding assistant at ~/opencode-pro/. Uses deepseek/deepseek-v4-pro via OpenCode CLI. Read-only consultative mode — analyzes code, reads filesystem, recommends solutions but never executes commands or modifies files. Shows code snippets for manual implementation. Launch: cd ~/opencode-pro && opencode --model deepseek/deepseek-v4-pro. Config: AGENTS.md with rules, capabilities, and project context.

## Database
PostgreSQL: localhost:5432, user cowork, password coworkpass, db coworkdb. Eight Cowork tables: sessions, steps, artifacts, tool_usage, errors, project_memory. Six booking tables: patients, appointments, availability, email_queue, faqs, appointment_history. One accounting table: invoices. Key field: doc_id as universal patient identifier across channels.

## Redis
localhost:6379, no password. Shared connection pool via graph/redis_client.py singleton. All operations wrapped in _redis_safe() — never crashes on connection failure. Booking sessions keyed by doc_id with 2h TTL. Plan cache via hashlib.sha256 with 1h TTL. Chat history via lrange(-6, -1) with 24h TTL.

## Email
Mail.ru account: josue.martinez.593@mail.ru. SMTP: smtp.mail.ru:465 SSL. IMAP: imap.mail.ru:993 SSL. Auth via app password with 2FA. Rate limit: 1 email/minute enforced by email_sender.py queue and APScheduler 60s interval. Config in .env: MAIL_USER, MAIL_PASSWORD, MAIL_SMTP_HOST, MAIL_SMTP_PORT, MAIL_IMAP_HOST, MAIL_IMAP_PORT.

## Installation and Commands
Activate environment: cd /media/SSD1T/cowork-local && source venv/bin/activate. Install: pip install -r requirements.txt. Start API: cd api-chat && python server.py &. Start Telegram bot: python api-chat/telegram_bot.py. Start OpenDesign daemon: cd workers/open-design && pnpm tools-dev run web --daemon-port 34095 --web-port 45125 &. Use Cowork: python apps/cli/cowork_graph.py "task". Marketing: python apps/cli/cowork_graph.py --design [generate|view|approve|list]. Accounting poller: python tools/accounting_poller.py. OpenCode Pro: cd ~/opencode-pro && opencode --model deepseek/deepseek-v4-pro.

## Project Structure
cowork-local/ with api-chat (FastAPI + Telegram bot), apps/cli (CLI tools), graph (LangGraph sub-graphs), workers (codewhale, opencode-pro, open-design binaries), tools (MCP servers, email tools, marketing/accounting schedulers), infra (Docker Compose, SQL schemas), output (projects, design, marketing/approved), venv (Python 3.13).

## Security
Shell injection fixed via shlex.split + shell=False. Path traversal protected via os.path.realpath. DB credentials as separate parameters. Redis shared connection pool with _redis_safe wrapper. Subprocess prompt injection protection via -- flag. Webhook n8n token authentication. Plan cache via deterministic hashlib.sha256. sys.executable for interpreter safety. Async Redis wrappers for event loop safety. Specific exception handling, no bare except. Hardcoded paths replaced with dynamic detection. Telegram token and API keys in environment variables. doc_id as universal patient key. Rate limiting via Redis. 26+ bugs fixed across 5 audit rounds. 88 Python files syntax-verified.

## Rules
Generate code, don't explain. Use absolute paths. Do not modify files without permission. See rules/api.md and rules/security.md.

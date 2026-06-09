# Cowork-Local v3.4.1

Local multi-agent development assistant with 4 specialized workers running on LangGraph.
Planner uses DeepSeek Reasoner (Pro). Workers use deepseek/deepseek-v4-flash (API direct) or deepseek-chat (Flash).
Total cost: ~$0.50/month. Booking worker adds ~$0.30/month per 1000 appointments.

## Architecture

planner (DeepSeek Pro) -> classifies intent -> route_to_worker
  - code_worker -> graph_code.py -> OpenCode (agent mode with tools) -> Python projects, scripts, PowerPoints
  - design_worker -> graph_design.py -> OpenDesign API (port 34095) -> UI/UX, landing pages
  - codewhale_worker -> graph_codewhale.py -> CodeWhale (agent mode --auto) -> filesystem, document, web, shell, edit, search
  - booking_worker -> graph_booking.py -> medical appointment agency (Telegram + Email)

## Workers

### code_worker
- Generates and EXECUTES Python code automatically using OpenCode in agent mode
- OpenCode uses native tools (Read, Write, Glob, Shell) to create complete projects
- No forced JSON format — OpenCode decides how to solve the task
- Generated files go to output/projects/{project_name}/
- Both workers share COWORK_DIR as cwd for full project visibility
- Scripts include tests (pytest) when applicable

### codewhale_worker
- Replaces the old mcp_worker with 30+ tools via CodeWhale in agent mode (--auto)
- Tools: filesystem search, document analysis, web navigation, shell execution, file editing
- Chat disabled (redirects to codewhale-tui for interactive AI chat)
- Works in COWORK_DIR with full project access

### design_worker
- OpenDesign daemon on port 34095
- Generates web prototypes, landing pages, UI/UX
- Healthcheck before calling
- Daemon path: workers/open-design/

### booking_worker
- Medical appointment booking agency
- Patient ID: cédula/RUC/passport with validation algorithm
- Flow: ID → name+email → intent classification → date (dateparser+Flash) → time → confirm
- Channels: Telegram (@byron92m_bot) + Email (Mail.ru IMAP polling)
- DB tables: patients, appointments, availability, email_queue, faqs, appointment_history
- Redis session state by doc_id (2h TTL)
- ICS calendar invitations via email queue (1/min Mail.ru rate limit)
- 24h reminders: Telegram for Telegram users, Email for email users (APScheduler)
- Commands: /start, /citas, /cancelar, /ayuda, /reset
- Security: rate limiting, input sanitization, doc_id as universal patient key

### mail_worker
- mail_send: Send emails via Mail.ru SMTP
- mail_read: Read inbox via IMAP
- calendar_add: Send .ics invitations
- Config: MAIL_USER, MAIL_PASSWORD, MAIL_SMTP_HOST, MAIL_SMTP_PORT, MAIL_IMAP_HOST, MAIL_IMAP_PORT

## PDF Processing (Important)
- Use project_path parameter, do not include path in query string
- Extracts ALL pages (no limit of 5)
- Extracts ALL text (no limit of 1000 characters)
- For long content: save to file and reference path

## Code Generation
- OpenCode uses agent mode with native tools (Read, Write, Glob, Shell)
- No JSON format required — model decides the best approach
- Generated files are saved in output/projects/{project_name}/
- Main script is auto-detected (prioritizes main.py, app.py, or largest .py file)
- Script is saved AND executed automatically

## Installation

cd /media/SSD1T/cowork-local
source venv/bin/activate
pip install -r requirements.txt

## Required Services

PostgreSQL: cowork:coworkpass@127.0.0.1:5432/coworkdb
Redis: localhost:6379
OpenDesign daemon: http://127.0.0.1:34095
Mail.ru SMTP/IMAP: smtp.mail.ru:465 / imap.mail.ru:993

## Main Commands

Activate environment:
cd /media/SSD1T/cowork-local && source venv/bin/activate

Start API:
cd api-chat && python server.py &

Start Telegram bot:
python api-chat/telegram_bot.py

Start OpenDesign daemon:
cd workers/open-design && pnpm tools-dev run web --daemon-port 34095 --web-port 45125 &

Use Cowork:
python apps/cli/cowork_graph.py "Create a CLI with --name flag"

Clear Redis cache:
python3 -c "import redis; r=redis.Redis(host='localhost',port=6379); r.flushall()"

## Telegram Assistant

Bot: @byron92m_bot (booking agency + legacy Cowork)
Booking commands: /start, /citas, /cancelar, /ayuda, /reset
Legacy commands: /list, /switch, /nueva, /cerrar, /estado, /pc
Memory: Redis by doc_id (2h TTL)
Security: rate limiting (15 msg/min), input sanitization, prompt injection defense

## Capabilities

8 intent types (7 Cowork + booking):
- code_generation -> code_worker
- tool_design -> design_worker
- tool_filesystem, tool_document, tool_web, tool_shell, tool_edit, chat -> codewhale_worker
- booking -> booking_worker

6 projects with 100% tests: webreq, logview, gitstat, tcpdump-cli, ai-reviewer, graph-report

## Project Structure

cowork-local/
  api-chat/              FastAPI + Telegram bot
  apps/cli/              CLI tools
  graph/                 LangGraph (4 sub-graphs)
  workers/               Worker binaries and services
    codewhale/           CodeWhale TUI binary (Flash, 30+ tools)
    opencode-pro/        Reserved for future OpenCode Pro assistant
    open-design/         OpenDesign daemon (UI/UX generation)
  tools/                 MCP servers and email tools
  infra/                 Docker Compose
  agents/                Sub-agents
  rules/                 Rules
  output/projects/       Generated projects
  venv/                  Python 3.13

## Security (v3.4.1)
- Shell injection: shlex.split() + shell=False
- Path traversal: os.path.realpath() validation
- DB credentials: separate parameters, no URL logging
- Redis: shared connection pool (redis_client.py)
- Webhook n8n: token authentication support
- Exception handling: specific exceptions, no bare except
- Hardcoded paths: dynamic detection via os.path

## Rules

- Generate code, don't explain
- Use absolute paths
- Do not modify files without permission
- See rules/api.md and rules/security.md

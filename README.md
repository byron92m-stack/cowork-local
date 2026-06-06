# Cowork-Local v3.3

Local multi-agent development assistant with 3 specialized workers running on LangGraph.
Planner uses DeepSeek V4 Pro. All 3 workers use free models.
Total cost: ~$0.50/month.

## Architecture

planner (DeepSeek Pro) -> classifies intent -> route_to_worker
  - code_worker -> graph_code.py -> OpenCode + Flash FREE -> Python projects, scripts, PowerPoints
  - design_worker -> graph_design.py -> OpenDesign API (port 34095) -> UI/UX, landing pages
  - mcp_worker -> graph_mcp.py -> 7 local tools -> filesystem, document, web, shell, chat, edit, mail

## Workers

### code_worker
- Generates and EXECUTES Python code automatically
- Response format: JSON {"code": "script here"}
- clean_code() handles JSON, markdown and non-ASCII characters
- Projects include tests (pytest) when applicable

### design_worker
- OpenDesign daemon on port 34095
- Generates web prototypes, landing pages, UI/UX
- Healthcheck before calling

### mail_worker
- mail_send: Send emails via Mail.ru SMTP
- mail_read: Read inbox via IMAP
- calendar_add: Send .ics invitations
- Config: MAIL_USER, MAIL_PASSWORD, MAIL_SMTP_HOST, MAIL_SMTP_PORT, MAIL_IMAP_HOST, MAIL_IMAP_PORT

### mcp_worker
- filesystem: file search with os.walk
- document: PDF, Excel, CSV, TXT reading (uses state.project_path)
- web: navigation with Playwright
- shell: command execution with --confirm
- chat: conversation with Redis memory
- edit: file editing via OpenCode

## PDF Processing (Important)
- Use project_path parameter, do not include path in query string
- Extracts ALL pages (no limit of 5)
- Extracts ALL text (no limit of 1000 characters)
- For long content: save to file and reference path

## Code Generation
- Prompt must request JSON: {"code": "script here"}
- clean_code() extracts code from JSON or markdown
- Removes non-ASCII characters (em dash, smart quotes, accents)
- Script is saved AND executed automatically

## Installation

cd /media/SSD1T/cowork-local
source venv/bin/activate
pip install -r requirements.txt

## Required Services

PostgreSQL: cowork:coworkpass@127.0.0.1:5432/coworkdb
Redis: localhost:6379
OpenDesign daemon: http://127.0.0.1:34095

## Main Commands

Activate environment:
cd /media/SSD1T/cowork-local && source venv/bin/activate

Start API:
cd api-chat && python server.py &

Start Telegram bot:
python api-chat/telegram_bot.py

Start OpenDesign daemon:
cd /media/SSD1T/open-design && pnpm tools-dev run web --daemon-port 34095 --web-port 45125 &

Use Cowork:
python apps/cli/cowork_graph.py "Create a CLI with --name flag"

Clear Redis cache:
python3 -c "import redis; r=redis.Redis(host='localhost',port=6379); r.flushall()"

## Telegram Assistant

Bot: @byron92m_bot
Authorized Chat ID: 8047752200
Commands: /list, /switch, /nueva, /cerrar, /estado, /pc, /ayuda
Memory: Redis with 24h TTL per chat_id
Security: Chat ID whitelist, --confirm for shell/web

## Capabilities

7 intent types:
- code_generation -> code_worker
- tool_design -> design_worker
- tool_filesystem, tool_document, tool_web, tool_shell, chat -> mcp_worker

6 projects with 100% tests: webreq, logview, gitstat, tcpdump-cli, ai-reviewer, graph-report

## Project Structure

cowork-local/
  api-chat/              FastAPI + Telegram bot
  graph/                 LangGraph (3 sub-graphs)
  apps/cli/              CLI tools
  tools/mcp/             16 MCP servers
  infra/                 Docker Compose
  agents/                Sub-agents
  rules/                 Rules
  output/archive/        Generated projects
  venv/                  Python 3.13

## Rules

- Generate code, don't explain
- Use absolute paths
- Do not modify files without permission
- See rules/api.md and rules/security.md

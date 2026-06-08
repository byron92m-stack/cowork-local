# Cowork-Local Development Plan

## Completed Phases

Phase 1-15: Core architecture with LangGraph, Qwen 3, 12 MCP Servers, Docker Sandbox, SSE Streaming, File Watcher, security, PostgreSQL 7 tables, plugin system, knowledge base, workspace manager, scheduled tasks, documentation, CLI integration.

Phase 16: Unified dual-mode v3.1 with Cowork mode and Code mode, 6-node LangGraph.

Phase 17: Enhanced tools and skills v3.1.1 with search_tools.py, session_memory.py, apply_diff.py, tool_caller.py, auto_watcher.py, Gmail integration, Telegram integration via @byron92m_bot, Google Calendar integration.

Phase 18: OpenCode CLI integration v3.1.1 replacing Claude Code CLI. Direct DeepSeek Cloud connection. Worker upgraded from Qwen3 GPU to DeepSeek V4 Flash.

Phase 19: Multi-agent with OpenCode worker v3.2. Planner DeepSeek V4 Pro plus Worker Flash FREE. Surgical fix mode. 6 projects 100 percent tests.

Phase 20: Redis, Graphify, n8n integration. Redis for state sharing and cache. Graphify 2395 nodes. n8n with native MCP. Invoice Bot 24/7.

Phase 21: VS Code, opencode-vscode, opencode-mem. Claude Code compatible structure with rules, agents, hooks, .mcp.json. PostgreSQL MCP server.

Phase 22: Telegram Assistant v3.2. Multi-session support via Redis. Conversation memory with 24h TTL. Automatic intent classification via DeepSeek Pro. 6 real tools including context-aware file editing.

Phase 23: Generalist planner. DeepSeek Pro classifies intent into 8 types. No hardcoded if/else. Worker executes MCPs directly for tool tasks.

Phase 24: Security hardening. Chat ID whitelist, confirm flag required for tool_shell and tool_web. Tokens and passwords moved to .env.

Phase 25: Documentation updated for v3.2 features.

Phase 26: Multi-worker sub-graph architecture. 3 independent sub-graphs: graph_code.py with CodeWorkerState, graph_design.py with DesignWorkerState, graph_mcp.py with CoworkState for 6 local tools.

Phase 27: tool_edit with OpenCode context-aware editing. Reads file content, generates diff with Flash FREE, applies changes. tool_edit added to PLANNER_SYSTEM as 8th intent type. Chat migrated from DeepSeek Pro API to OpenCode Flash FREE.

Phase 28: PDF Processing fixes. tool_document now prioritizes state.project_path over user_query. Extracts all pages (removed limit of 5). Extracts all text (removed limit of 1000 chars). Supports long content via file saving.

Phase 29: Code Generation fixes. Prompt now requests JSON format. clean_code() handles JSON responses, markdown blocks, and removes non-ASCII characters (em dash, smart quotes). Scripts are saved AND executed automatically. Output captured and returned.

Phase 30: PowerPoint generation working. 14 slides with logical structure. Full PDF content preserved. Supports both generic and template-based presentations. Automatic verification of results.

Phase 31: OPENCODE.md and README.md updated with new capabilities.

Phase 32: Mail.ru email migration v3.3. Replaced Gmail with Mail.ru (Gmail blocked bot account). SMTP port 465 SSL, IMAP port 993 SSL. App password with 2FA. Migrated 5 files: tools/mcp/gmail/ → tools/mcp/mail/, mcp_client.py, calendar/server.py, skills/server.py, .env. Updated .mcp.json. All references to Gmail removed. Graphify updated to 2713 nodes. Security audit: removed hardcoded API keys from api-chat/chat.py and api-chat/telegram_bot.py. Documentation updated: OPENCODE.md, README.md, ARCHITECTURE.md, SECURITY.md, COWORK_PLAN.md.

Phase 33: Booking Agency v3.4. Medical appointment booking system via Telegram (@byron92m_bot) and Email (Mail.ru IMAP polling). Patient identification by cédula/RUC/passport with validation algorithm (Ecuadorian ID, RUC format, passport). Flow: ID → name+email (Flash extraction) → intent classification (DeepSeek Flash API JSON mode) → date (dateparser + Flash confirmation) → time (regex extraction) → confirm. New files: graph/graph_booking.py (390 lines, 8 nodes), graph/booking_db.py (asyncpg CRUD), graph/booking_prompts.py, tools/email_poller.py, tools/email_sender.py, tools/reminder_job.py. Updated: api-chat/telegram_bot.py (APScheduler reminders, new commands /start /citas /cancelar /ayuda /reset), graph/state.py (BookingState with doc_id). DB tables: patients, appointments, availability, email_queue, faqs, appointment_history. Redis session state keyed by doc_id (2h TTL). ICS invitations via email queue (1/min Mail.ru limit). 24h reminders via APScheduler (Telegram for Telegram users, Email for email users). Security: rate limiting (15 msg/min Telegram, 3/hr email), input sanitization, prompt injection defense. Tested: full flow working (register → book → confirm → DB). Documentation updated: OPENCODE.md, README.md, ARCHITECTURE.md, COWORK_PLAN.md.

Phase 34: Security hardening v3.4.1. 22 improvements from architectural analysis via codewhale-tui. Fixed shell injection (shlex.split + shell=False). Fixed MCP error reporting (tests_passed/tests_failed now correct). Secured DB credentials (separate parameters, no URL logging). Unified DeepSeek clients into DeepSeekClient. Removed dead code (graph/nodes/). Replaced hash() with hashlib.sha256 for deterministic plan caching. Added path traversal protection (os.path.realpath). Replaced hardcoded paths with dynamic detection. Externalized PLANNER_SYSTEM to prompts/planner_system.txt. Created shared Redis connection pool (graph/redis_client.py). Optimized history loading (lrange -6 -1). Fixed continue_session (resets iteration_count + errors). Added type hints to main functions. Improved JSON extraction (balanced bracket parser). Added n8n webhook token auth. Specific exception handling (no bare except). Disabled MCP chat (redirects to codewhale-tui). Deleted chat.py and HANDOUT.md. Documentation updated: OPENCODE.md, README.md, ARCHITECTURE.md, COWORK_PLAN.md, SECURITY.md.

## Current Capabilities v3.4.1

Telegram assistant at @byron92m_bot with 7 real tools plus booking agency accessible through natural language. Multi-agent LangGraph with DeepSeek V4 Pro planner and 4 specialized workers via sub-graph architecture. 16 MCP Servers. PostgreSQL plus Redis with 24h TTL. Graphify code intelligence with 2713 nodes. n8n automation. Playwright web navigation. Context-aware file editing via OpenCode. PDF processing with no limits. Code generation with JSON format and automatic execution. PowerPoint generation from PDF content. Mail.ru email integration with SMTP/IMAP. Medical appointment booking agency via Telegram and Email with patient ID validation, dateparser+Flash date extraction, ICS invitations, 24h reminders. All workers use Flash except planner (Pro). MCP chat disabled (use codewhale-tui). Security hardened. Total cost approximately 0.50 dollars per month. Booking agency adds ~0.30/month per 1000 appointments.

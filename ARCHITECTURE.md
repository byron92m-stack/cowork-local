# Architecture — Cowork-Local v3.4.1

## Overview

Multi-agent system with DeepSeek V4 Pro planner and 4 specialized workers via LangGraph sub-graph architecture. 30+ tools via CodeWhale + OpenCode agent mode. PostgreSQL plus Redis. Telegram assistant 24/7. Playwright for web automation. Graphify for code intelligence (34,248 nodes). All 212 Python files syntax-verified. 26+ bugs fixed across 5 audit rounds. Production ready. Cost approximately 0.50 dollars per month. Booking worker adds ~0.30/month per 1000 appointments.

## Multi-Agent Pipeline

Planner uses DeepSeek Reasoner (Pro) to classify user intent into 9 types: code_generation, tool_design, tool_filesystem, tool_document, tool_web, tool_edit, tool_shell, booking, chat. Routes to the correct worker via conditional edges.

Four workers implemented as independent sub-graphs. Both code_worker and codewhale_worker share COWORK_DIR as cwd for full project visibility.

code_worker uses OpenCode CLI with deepseek/deepseek-v4-flash (API direct) in agent mode with native tools (Read, Write, Glob, Shell). Generates Python projects with pytest. No forced JSON format — OpenCode decides how to solve the task. Generated files go to output/projects/{project_name}/. Main script auto-detected (prioritizes main.py, app.py, or largest .py file). Script is saved AND executed automatically with exec_failed validation (returncode + "OK" check). Prompt protected with -- flag to prevent injection.

codewhale_worker replaces the old mcp_worker. Uses CodeWhale in agent mode (exec --auto) with 30+ tools: filesystem search, document analysis, web navigation, shell execution, file editing. Chat disabled (redirects to codewhale-tui for interactive AI chat). Works in COWORK_DIR with full project access. Binary at workers/codewhale/codewhale with dynamic path detection.

design_worker uses OpenDesign API to generate UI, UX, landing pages, and dashboards via port 34095. Daemon located at workers/open-design/. Healthcheck before calling. Graceful offline handling.

booking_worker uses LangGraph state machine for medical appointment booking via Telegram and Email. Patient identification by cédula/RUC/passport with validation algorithm. Flow: ID → name+email → intent classification (deepseek-chat Flash API with JSON mode) → date (dateparser + Flash confirmation) → time (regex extraction) → confirm. Saves to PostgreSQL (patients, appointments, availability, email_queue, faqs, appointment_history tables). Redis session state keyed by doc_id with 2h TTL. ICS calendar invitations via email queue respecting Mail.ru 1/min rate limit. 24h reminders via APScheduler (Telegram for Telegram users, Email for email users). All Redis operations use async wrappers (save_booking_state_async, delete_booking_state_async) with run_in_executor to avoid event loop blocking. Security: rate limiting (15 msg/min Telegram, 3/hr email), input sanitization, prompt injection defense.

mail_worker uses Mail.ru SMTP (port 465 SSL) and IMAP (port 993 SSL) to send/receive emails. Tools: mail_send, mail_read, calendar_add (ICS invitations). Auth via app password with 2FA. Config in .env.

Each worker has its own sub-graph with isolated state. CodeWorkerState for code generation, DesignWorkerState for design tasks. Codewhale worker shares CoworkState for chat history access. All workers propagate errors to state.errors via add_error() for proper review/diagnosis.

Review evaluates completeness using tests_passed/tests_failed. Terminal errors (Timeout, daemon offline) are detected and skip retry. Decision routes to planner for retry or END. Saves conversation history to Redis via _redis_safe() wrapper (never crashes on Redis failure). Maximum 5 iterations. Multi-worker flows supported: codewhale can search files, code_worker can generate scripts using that context in subsequent iterations.

## Code Generation (Updated)

OpenCode uses agent mode with native tools (Read, Write, Glob, Shell). No forced JSON format — model decides the best approach. Generated files saved in output/projects/{project_name}/. Main script auto-detected (prioritizes main.py, app.py, or largest .py file). Script is saved AND executed automatically with sys.executable. Execution validated: returncode != 0 or missing "OK" sets tests_failed=1. Both workers share COWORK_DIR as cwd for full project visibility.

## Sub-Graph Architecture

Main graph in graph.py contains planner, review, and decision nodes. Four sub-graphs: graph_code.py with CodeWorkerState, graph_design.py with DesignWorkerState, graph_codewhale.py with CoworkState. graph_booking.py with BookingState. All state definitions in state.py. Legacy Step class, plan field, add_step(), is_complete(), get_pending_steps(), get_current_step(), and summary() removed in Phase 35 cleanup. Dead code plan() and review() removed from DeepSeekClient.

## Workers Directory

All worker binaries and services consolidated in workers/:
- workers/codewhale/ — CodeWhale TUI binary (Flash, 30+ tools)
- workers/opencode-pro/ — Reserved for future OpenCode Pro assistant
- workers/open-design/ — OpenDesign daemon (UI/UX generation)

## Telegram Assistant

API endpoint /chat/assistant receives messages from Telegram bot polling every 10 seconds. Booking bot (@byron92m_bot) with commands: /start, /citas, /cancelar, /ayuda, /reset. Multi-session via Redis keyed by doc_id (2h TTL). Legacy Cowork commands: /list, /switch, /nueva, /cerrar, /estado, /pc. Security: rate limiting (15 msg/min), input sanitization, prompt injection defense. 24h reminders via APScheduler.

## Infrastructure

PostgreSQL with 8 Cowork tables plus 6 booking tables (patients, appointments, availability, email_queue, faqs, appointment_history). Redis for chat history, graph state, planner cache, and session management — all operations wrapped in _redis_safe() for resilience. n8n on port 5678 with native MCP for workflow automation. Graphify maps the codebase into 34,248 nodes and 50,881 edges. Playwright with Chromium headless in /browsers/ directory. 14 MCP servers in .mcp.json (googledrive removed, postgresql added). APScheduler for 24h appointment reminders and email queue processing.

## Security (v3.4.1)

API keys in .env excluded from git. Shell injection fixed (shlex.split + shell=False). Path traversal protected (os.path.realpath). DB credentials as separate parameters. Webhook n8n token auth support. Redis shared connection pool with _redis_safe() wrapper on all operations. Specific exception handling (no bare except). Hardcoded paths replaced with dynamic detection. Telegram token and API password in environment variables. Chat ID open for patient bookings. doc_id (cédula) as universal patient key across Telegram and Email channels. Confirm flag required for shell and web tools. Rate limiting via Redis. MCP servers use whitelisted paths and read-only modes. Prompt injection protection via -- flag in subprocess calls.

## Hardware

Fedora 43. AMD Ryzen Starship Matisse. NVIDIA RTX 4060 Ti 16GB VRAM. 32GB RAM. NVMe 2TB with Btrfs plus SSD 1TB with ext4. Docker for PostgreSQL, Redis, and n8n. Ollama serving qwen3:14b. Node.js v24.15.0.

## Monthly Cost

DeepSeek API approximately 0.50 dollars per month for intensive usage across all models. All other components free and open-source including LangGraph, OpenCode CLI, CodeWhale, FastAPI, Streamlit, PostgreSQL, Docker, Ollama, and 14 MCP servers. Hardware already owned. Total approximately 0.50 dollars per month. Booking agency adds ~0.30 dollars per 1000 appointments (DeepSeek Flash API for intent classification and conversation).

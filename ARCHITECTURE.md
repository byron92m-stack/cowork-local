# Architecture — Cowork-Local v3.4.1

## Overview

Multi-agent system with DeepSeek V4 Pro planner and 5 specialized workers via LangGraph sub-graph architecture. 30+ tools via CodeWhale + OpenCode agent mode. PostgreSQL plus Redis. Telegram assistant 24/7. Playwright for web automation. Graphify for code intelligence (34,332 nodes). All 84 Python files syntax-verified. 26+ bugs fixed across 5 audit rounds. Production ready. Cost approximately $0.50 per month. Booking adds ~$0.30/month per 1000 appointments. Accounting and Marketing workers add no extra cost.

## Multi-Agent Pipeline

Planner uses DeepSeek Reasoner (Pro) to classify user intent into 9 types: code_generation, tool_design, tool_filesystem, tool_document, tool_web, tool_edit, tool_shell, booking, chat. Routes to the correct worker via conditional edges in route_to_worker().

Five workers implemented as independent sub-graphs. code_worker and codewhale_worker share COWORK_DIR as cwd for full project visibility and multi-worker collaboration. All Redis operations wrapped in _redis_safe() for resilience. All subprocess calls use sys.executable and -- flag injection protection. All workers propagate errors to state.errors via add_error().

code_worker uses OpenCode CLI with deepseek/deepseek-v4-flash (API direct) in agent mode with native tools (Read, Write, Glob, Shell). No forced JSON format. Generated files go to output/projects/{project_name}/. Main script auto-detected via find_generated_script(). Execution validated via returncode and "OK" check. Prompt protected with -- flag. Subprocess timeout 600s, script timeout 120s.

codewhale_worker uses CodeWhale in agent mode (exec --auto) with 30+ tools: filesystem search, document analysis, web navigation, shell execution, file editing. Chat disabled. Works in COWORK_DIR with full project access. Binary at workers/codewhale/codewhale with dynamic path detection. Subprocess timeout 120s.

design_worker uses OpenDesign API to generate UI, UX, landing pages, marketing posters, and social media graphics via port 34095. Consumes SSE stream from API. Saves output to output/design/ with automatic project detection. Daemon at workers/open-design/. Healthcheck before calling. Skill parameter supports frontend, poster, social-media.

booking_worker uses LangGraph state machine for medical appointment booking via Telegram only (Email channel moved to accounting). Patient identification by cédula/RUC/passport with validation algorithm. Flow: ID extraction via LLM, name and email collection, intent classification (deepseek-chat Flash API with JSON mode), date parsing (dateparser + Flash confirmation), slot selection (regex extraction), confirm. Saves to PostgreSQL (patients, appointments, availability, email_queue, faqs, appointment_history). Redis session state keyed by doc_id with 2h TTL. ICS calendar invitations via email queue respecting Mail.ru 1/min rate limit. All Redis operations use async wrappers (save_booking_state_async, delete_booking_state_async) with run_in_executor. 24h reminders via APScheduler. Commands: /start, /citas, /cancelar, /ayuda, /reset. Security: rate limiting, input sanitization, prompt injection defense.

accounting_worker extracts SRI electronic invoice data from XML and PDF email attachments. Single-node subgraph. XML extraction uses Clark notation with automatic namespace detection for infoTributaria and infoFactura. PDF extraction uses regex patterns. Saves to invoices table with UNIQUE(numero_factura, ruc_emisor) for duplicate prevention. No LLM required. IMAP polling via accounting_poller.py processes UNSEEN emails with invoice attachments. Table: invoices (id, numero_factura, ruc_emisor, razon_social, fecha_emision, subtotal, iva, total, source_email, attachment_path, raw_data JSONB).

Marketing campaigns are sub-nodes of design_worker (campaign_generate, campaign_view, campaign_approve, campaign_list). Invoked via python apps/cli/cowork_graph.py --design [generate|view|approve|list].

Review evaluates completeness using tests_passed/tests_failed. Terminal errors (Timeout, daemon offline) detected and skip retry. Decision routes to planner or END. Conversation history saved to Redis via _redis_safe(). Maximum 5 iterations. Multi-worker flows supported between code_worker and codewhale_worker.

## Sub-Graph Architecture

Main graph in graph.py contains planner, review, and decision nodes. Sub-graphs: graph_code.py (CodeWorkerState), graph_design.py (DesignWorkerState), graph_codewhale.py (CoworkState), graph_booking.py (BookingState), graph_accounting.py (AccountingState). design_worker has 5 nodes (generate, campaign_generate, campaign_view, campaign_approve, campaign_list) with route_design() routing. All state definitions in state.py. Legacy Step class, plan field, add_step, is_complete, get_pending_steps, get_current_step, and summary removed in Phase 35. Dead plan() and review() removed from DeepSeekClient.

## Workers Directory

All worker binaries and services consolidated in workers/: codewhale (CodeWhale TUI + .codewhale config, 30+ tools), opencode-pro (reserved for OpenCode Pro assistant), open-design (OpenDesign daemon, UI/UX generation, port 34095). OpenCode Pro assistant at ~/chat-colaborativo/ uses deepseek-v4-pro in read-only consultative mode.

## Infrastructure

PostgreSQL with 8 Cowork tables, 6 booking tables, 1 accounting table (invoices). Redis for chat history, graph state, planner cache, session management — all _redis_safe() wrapped. n8n on port 5678. Graphify: 34,332 nodes, 50,990 edges. Playwright Chromium in /browsers/. 16 MCP servers in .mcp.json. APScheduler for reminders and email queue.

## Security (v3.4.1)

API keys in .env excluded from git. Shell injection fixed (shlex.split + shell=False). Path traversal protected (os.path.realpath). DB credentials as separate parameters. Redis _redis_safe() wrapper on all operations. Subprocess -- flag injection protection. sys.executable for interpreter safety. Async Redis wrappers for event loop safety. Webhook n8n token auth. Plan cache via hashlib.sha256. Specific exception handling. Hardcoded paths dynamic. doc_id as universal patient key. Rate limiting via Redis. MCP servers whitelisted paths. 26+ bugs fixed, production ready.

## Hardware

Fedora 43. AMD Ryzen Starship Matisse. NVIDIA RTX 4060 Ti 16GB VRAM. 32GB RAM. NVMe 2TB with Btrfs plus SSD 1TB with ext4. Docker for PostgreSQL, Redis, n8n. Ollama qwen3:14b. Node.js v24.15.0.

## Monthly Cost

DeepSeek API approximately $0.50 per month for intensive usage across all models. All other components free and open-source. Booking adds ~$0.30/month per 1000 appointments. Accounting and Marketing add no extra cost.

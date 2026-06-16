# Cowork-Local Development Plan

## Completed Phases

Phase 1-15: Core architecture with LangGraph, Qwen 3, 12 MCP Servers, Docker Sandbox, SSE Streaming, File Watcher, security, PostgreSQL 7 tables, plugin system, knowledge base, workspace manager, scheduled tasks, documentation, CLI integration.

Phase 16-34: See git history for full details. Key milestones: Unified dual-mode v3.1, OpenCode CLI integration, Multi-agent with DeepSeek Pro planner, Redis/Graphify/n8n integration, Telegram Assistant, Generalist planner with 8 intent types, Security hardening, Multi-worker sub-graph architecture, PDF/PowerPoint processing, Mail.ru email migration v3.3, Booking Agency v3.4 with patient ID validation and ICS invitations, Security hardening v3.4.1 with 22 improvements.

Phase 35: Worker consolidation, agent mode upgrade, and production hardening (5 audit rounds, 26+ bugs fixed across 84 Python files). Migrated code_worker from JSON to OpenCode agent mode. Replaced mcp_worker with codewhale_worker (30+ tools). Consolidated workers into workers/ directory. Added _redis_safe() wrapper, -- flag injection protection, sys.executable, async Redis wrappers, exec_failed validation. Removed dead code: Step class, plan system, add_step, is_complete, graph_mcp.py, plan()/review() from DeepSeekClient. Fixed reply propagation, last_project_dir, timeout detection, CLI imports, googledrive references. Updated all documentation and graphify (34,332 nodes).

Phase 36: Accounting, Design/Marketing, and Langcli Pro Assistant.

Phase 36a — Accounting Worker:
- graph/graph_accounting.py: Extracts SRI electronic invoice data from XML (Clark notation with automatic namespace detection) and PDF (regex patterns). Single-node LangGraph subgraph. No LLM required.
- graph/accounting_db.py: invoices table CRUD with UNIQUE(numero_factura, ruc_emisor) for duplicate prevention. Async pool with run_in_executor for sync operations.
- tools/accounting_poller.py: IMAP polling every 5 minutes for UNSEEN emails with XML/PDF attachments matching invoice patterns. Replaced email_poller.py which was previously used by booking.
- graph/state.py: AccountingState with channel, user_id, attachment_path, attachment_type, invoice_data fields.
- infra/postgres_booking.sql: invoices table schema with all fields including raw_data JSONB.
- Booking email reading removed — booking now Telegram-only. Email confirmation sending remains for ICS invitations.

Phase 36b — Design/Marketing Worker:
- graph/graph_design.py upgraded to consume SSE stream from OpenDesign API, save output to output/design/, and auto-detect generated project folders. Now serves both design and marketing use cases.
- tools/marketing_scheduler.py: CLI-based weekly campaign workflow. --generate creates campaign via OpenDesign poster skill, --view opens latest campaign in Firefox, --approve marks approved and sends email notification, --list shows all campaigns with status. Campaign templates rotate by weekday: Lunes de Salud, Miércoles de Bienestar, Viernes de Oferta.
- tools/email_sender.py: Added send_email_simple() for direct email sends bypassing the queue (for admin notifications).
- Marketing output saved to output/design/, approved campaigns copied to output/marketing/approved/.

Phase 36c — Langcli Pro Assistant:
- Created ~/chat-colaborativo/ as independent collaborative coding assistant using deepseek-v4-pro.
- AGENTS.md with rules: read-only consultative mode, analyzes code, reads filesystem, recommends solutions, never executes commands or modifies files, shows code snippets for manual implementation.
- Access to entire filesystem for analysis and diagnosis.

Phase 37 — Design/Marketing unification:
- graph/graph_design.py: 5 nodes (generate, campaign_generate, campaign_view, campaign_approve, campaign_list) with route_design() routing. _call_opendesign() helper shared by all nodes.
- apps/cli/cowork_graph.py: --design flag for direct design/campaign commands, bypassing planner.
- tools/marketing_scheduler.py: simplified to 25-line wrapper invoking build_design_graph().
- README.md, ARCHITECTURE.md: 6->5 workers, updated commands.

Phase 36d — Documentation refresh:
- All docs updated for 5 workers: README.md, ARCHITECTURE.md, COWORK_PLAN.md, HANDOUT.md, COWORK.md.
- Updated security documentation reflecting Phase 35-36 improvements.

## Current Capabilities v3.4.1

Five specialized workers: code_worker (Python project generation via OpenCode agent mode), codewhale_worker (30+ tools via CodeWhale for filesystem, document, web, shell, editing), design_worker (UI/UX and marketing art via OpenDesign API), booking_worker (medical appointments via Telegram with patient ID validation, ICS invitations, 24h reminders), accounting_worker (SRI invoice extraction from XML/PDF email attachments, automatic DB storage). Marketing campaigns are sub-nodes of design_worker (campaign_generate, campaign_view, campaign_approve, campaign_list). Planner uses DeepSeek Reasoner Pro. All workers use Flash except planner. Telegram assistant @byron92m_bot. PostgreSQL with 14 tables. Redis with _redis_safe() resilience. Graphify 34,332 nodes. 16 MCP servers. Langcli Pro assistant at ~/chat-colaborativo/. 26+ bugs fixed, 84 Python files verified. Production ready. Total cost approximately $0.50 per month. Booking adds ~$0.30/month per 1000 appointments. Accounting and Marketing add no extra cost.

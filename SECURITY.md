# Security Policy

## Reporting

Email the maintainer directly. Do not open public issues.

## Principles

API Keys: Never hardcoded. Loaded via os.getenv from environment variables. dotenv file excluded from Git. Zero API keys in committed code. Tool Restrictions: Filesystem MCP whitelisted paths only. Shell MCP whitelisted commands with destructive commands blocked. Git MCP read-only. Docker MCP read-only. Docker Sandbox: Full container isolation, no network access, read-only filesystem, resource limits, no privilege escalation, SELinux compatible. Prompt Injection Defenses: Pattern-based detection, input sanitization, tool argument validation, length limits on input, JSON mode for structured LLM outputs in booking and planner, subprocess -- flag to separate arguments from prompt data. Database: Credentials via environment variables only, no default passwords, UUID primary keys with audit timestamps. File Watcher Security: Monitors specified directories only, filters by file extension, ignores temp files, auto-execution disabled by default.

Graph Security: LangGraph loop limited to 5 iterations. DeepSeek planner uses JSON mode with response_format json_object. OpenCode and CodeWhale workers run via subprocess with timeout protection. Multi-worker flows share COWORK_DIR as cwd for collaboration. All Redis operations wrapped in _redis_safe() for resilience. Subprocess calls use sys.executable for interpreter safety. Prompt arguments protected with -- flag to prevent injection. All worker wrappers propagate errors to state.errors via add_error() for proper diagnosis.

Integration Security: Mail.ru and Telegram use dedicated bot accounts (josue.martinez.593@mail.ru, @byron92m_bot), never personal credentials. Calendar uses email invitations via ICS files through Mail.ru SMTP, no OAuth tokens stored. All external API calls use environment variables for authentication.

Worker Security: OpenCode CLI runs as subprocess with 600s timeout, uses deepseek-v4-flash via DeepSeek API direct, prompt protected with -- flag, execution via sys.executable with returncode validation. CodeWhale runs as subprocess with 120s timeout in agent mode, uses deepseek-v4-flash via API direct, binary at workers/codewhale/codewhale with dynamic path detection. Booking uses async Redis wrappers (save_booking_state_async, delete_booking_state_async) with run_in_executor, session state keyed by doc_id with 2h TTL. Accounting extracts invoice data deterministically from XML/PDF attachments, no LLM required, IMAP polling restricted to UNSEEN with invoice patterns. Marketing campaigns are sub-nodes of design_worker using OpenDesign API on localhost:34095, output saved locally, CLI-based approval workflow, email notifications via send_email_simple respecting Mail.ru rate limit.

## Audit Results June 2026

Zero API keys committed. Zero personal emails exposed. Zero local IPs exposed. All sensitive data in dotenv excluded from Git. Project unified into single folder. Anthropic proxy removed. OpenCode CLI direct integration eliminates proxy translation layer. Workers consolidated in workers/ directory. 26+ bugs fixed across 5 audit rounds. 88 Python files syntax-verified. Dead code removed: graph/nodes/, graph_mcp.py, Step class, plan steps system, deepseek_client plan()/review().

## PDF Processing Security
PDF files read via pypdf with no shell execution. Extracted text sanitized. No PDF rendering or JavaScript execution. Path validated before access. Extracts all pages and all text with no arbitrary limits.

## Code Generation Security
Generated scripts saved to output/projects/ directory. OpenCode uses agent mode with native tools. Scripts executed via subprocess.run with timeout using sys.executable. Main script auto-detected. Output captured, not printed to terminal. Execution validated via returncode and "OK" check.

## Redis Security
Redis runs locally without password on port 6379. Not exposed externally. All operations wrapped in _redis_safe(). Booking sessions keyed by doc_id with 2h TTL. Keys have TTL to auto-expire and prevent memory buildup. No sensitive data stored permanently. Async wrappers prevent event loop blocking.

## n8n Security
n8n API key stored in dotenv excluded from Git. MCP server uses JWT authentication. Webhook endpoints protected by n8n internal auth with N8N_WEBHOOK_TOKEN. Credentials configured via n8n UI, not exposed in workflow exports.

## Graphify Security
Output stored in graphify-out/ directory. GRAPH_REPORT.md contains function names and file paths only, no secrets. Excluded from Git.

## Telegram Bot Security
Chat ID open for patient bookings. Rate limiting (15 msg/min) and input sanitization. Legacy Cowork mode restricted to authorized Chat ID. Bot Token stored in .env via TELEGRAM_BOT_TOKEN. API credentials in environment variables, not hardcoded. Event loop persistence via _async_loop for stability under concurrent messages.

## Booking Agency Security
Patient identification by cédula/RUC/passport with validation algorithm. doc_id serves as universal patient key across channels. Rate limiting: 15 msg/min Telegram. Input sanitization: max 500 chars, control characters stripped. Prompt injection defenses on all LLM calls. DeepSeek Flash API with JSON mode for structured outputs. Session state in Redis keyed by doc_id with 2h TTL, isolated per patient. Email queue respects Mail.ru 1/min rate limit with double protection. Patient data only accessible via authenticated doc_id. /reset unlinks telegram_chat_id without deleting records. All Redis operations async via run_in_executor. get_or_create_patient prioritizes doc_id as universal key, handles UniqueViolationError on telegram_chat_id merge.

## Accounting Worker Security
Invoice data extracted via deterministic XML parser (no LLM injection risk). PDF extraction uses regex only. IMAP polling restricted to UNSEEN emails with invoice-matching attachments. Duplicate detection via UNIQUE(numero_factura, ruc_emisor). Invoices table isolated from patient data. No email responses sent. Async pool with run_in_executor for sync operations.

## Marketing Worker Security
OpenDesign API on localhost:34095 only. Output saved to output/design/ and output/marketing/approved/. CLI-based approval requires local shell access. Email notifications use send_email_simple respecting Mail.ru rate limit. Campaign templates are static prompts, no user input injection.

## Sub-Graph Security
Each worker runs in isolated sub-graph with independent state: code_worker (CodeWorkerState), design_worker (DesignWorkerState), codewhale_worker (CoworkState), booking_worker (BookingState), accounting_worker (AccountingState). Sub-graphs cannot access each other's state. All wrappers propagate errors to state.errors for proper diagnosis. OpenDesign daemon on port 34095 bound to localhost only. OpenDesign artifacts in .od/projects/ directory, gitignored.

## Workers Directory Security
All worker binaries and services consolidated in workers/: codewhale (CodeWhale TUI with dynamic path detection), opencode-pro (reserved for future assistant), open-design (OpenDesign daemon, gitignored artifacts). OpenCode Pro assistant at ~/opencode-pro/ runs in read-only consultative mode.

## Security Improvements Summary (v3.4.1 + Phase 35-36)

Shell injection: shlex.split() + shell=False. Path traversal: os.path.realpath(). DB credentials: separate parameters. Redis: shared pool, _redis_safe() wrapper. Prompt injection: -- flag on subprocess. Interpreter: sys.executable. Async Redis: run_in_executor wrappers. Exception handling: specific, no bare except. Hardcoded paths: dynamic detection. Webhook n8n: token auth. Plan cache: hashlib.sha256. History: lrange(-6, -1). continue_session: resets iteration_count. JSON extraction: balanced bracket parser. MCP chat: disabled. Dead code removed: graph/nodes/, chat.py, Step class, plan system, graph_mcp.py, plan()/review(). googledrive removed from mcp_client.py and .mcp.json. Email constraint relaxed (UNIQUE removed, doc_id is universal key). link_doc_to_patient uses transaction with FOR UPDATE. telegram_chat_id merge handles UniqueViolationError.

## Best Practices

Never commit dotenv file. Use strong PostgreSQL passwords. Review MCP allowed paths. Keep Docker sandbox enabled for untrusted code. Rotate API keys periodically. Use dedicated bot accounts for all integrations.

## Supported Versions

Version 3.4.1 with 5 workers via sub-graph architecture + Mail.ru email + Booking Agency (Telegram) + Accounting (IMAP) + Marketing (CLI). Workers consolidated in workers/ directory. 26+ bugs fixed, production ready.

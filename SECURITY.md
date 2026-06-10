# Security Policy

## Reporting

Email the maintainer directly. Do not open public issues.

## Principles

API Keys: Never hardcoded. Loaded via os.getenv from environment variables. dotenv file excluded from Git. Zero API keys in committed code.

Tool Restrictions: Filesystem MCP whitelisted paths only. Shell MCP whitelisted commands with destructive commands blocked. Git MCP read-only. Docker MCP read-only.

Docker Sandbox: Full container isolation. No network access. Read-only filesystem. Resource limits. No privilege escalation. SELinux compatible.

Prompt Injection Defenses: Pattern-based detection. Input sanitization. Tool argument validation. Length limits on input. JSON mode for structured LLM outputs prevents injection in booking and planner. Subprocess calls use -- flag to separate arguments from prompt data.

Database: Credentials via environment variables only. No default passwords. 8 tables with UUID primary keys and audit timestamps.

File Watcher Security: Monitors specified directories only. Filters by file extension. Ignores temp files. Auto-execution disabled by default.

Graph Security: LangGraph loop limited to 5 iterations. DeepSeek planner uses JSON mode with response_format json_object. OpenCode and CodeWhale workers run via subprocess with timeout protection. Multi-worker flows share COWORK_DIR as cwd for collaboration. All Redis operations wrapped in _redis_safe() for resilience — graph never crashes on Redis failure. Subprocess calls use sys.executable for interpreter safety. Prompt arguments protected with -- flag to prevent injection.

Integration Security: Mail.ru and Telegram use dedicated bot accounts (josue.martinez.593@mail.ru, @byron92m_bot), never personal credentials. Calendar uses email invitations via ICS files sent through Mail.ru SMTP, no OAuth tokens stored. All external API calls use environment variables for authentication.

OpenCode Worker Security: OpenCode CLI runs as subprocess with 600 second timeout. deepseek/deepseek-v4-flash model accessed via DeepSeek API direct, not OpenCode hosted. Worker uses agent mode with native tools (Read, Write, Glob, Shell). Prompt protected with -- flag to prevent injection. Execution uses sys.executable (not hardcoded "python"). Script execution validated via returncode and "OK" check. Both workers share COWORK_DIR as cwd for full project visibility.

CodeWhale Worker Security: CodeWhale runs as subprocess with 120 second timeout in agent mode (exec --auto). deepseek-v4-flash model via DeepSeek API direct. Binary at workers/codewhale/codewhale with dynamic path detection.

Booking Worker Security: All Redis operations use async wrappers (save_booking_state_async, delete_booking_state_async) with run_in_executor to avoid event loop blocking. Session state keyed by doc_id with 2h TTL.

## Audit Results June 2026

Zero API keys committed. Zero personal emails exposed. Zero local IPs exposed. All sensitive data in dotenv excluded from Git. Project unified into single folder. Anthropic proxy removed, reducing attack surface. OpenCode CLI direct integration eliminates proxy translation layer. Workers consolidated in workers/ directory. 26+ bugs fixed across 5 audit rounds. 212 Python files syntax-verified. Dead code removed: graph/nodes/, graph_mcp.py, Step class, plan steps system, deepseek_client plan()/review().

## PDF Processing Security
PDF files read via pypdf with no shell execution. Extracted text sanitized. No PDF rendering or JavaScript execution. Path validated before access.

## Code Generation Security
Generated scripts saved to output/projects/ directory. OpenCode uses agent mode with native tools — no forced JSON format. Scripts executed via subprocess.run with timeout using sys.executable. Main script auto-detected from generated files (prioritizes main.py, app.py, or largest .py file). Output captured, not printed directly to terminal. Execution validated: returncode and "OK" check determine pass/fail.

## Redis Security
Redis runs locally without password on port 6379. Not exposed externally. All operations wrapped in _redis_safe() — never crashes on connection failure. Booking sessions keyed by doc_id with 2h TTL. Keys have TTL (5 minutes to 1 hour) to auto-expire and prevent memory buildup. No sensitive data stored permanently in Redis. Async wrappers for booking operations prevent event loop blocking.

## n8n Security
n8n API key stored in dotenv file excluded from Git. MCP server uses JWT authentication. Webhook endpoints protected by n8n internal auth with N8N_WEBHOOK_TOKEN. Credentials configured via n8n UI, not exposed in workflow JSON exports.

## Graphify Security
Graphify output stored in graphify-out/ directory. GRAPH_REPORT.md contains function names and file paths only, no secrets. Excluded from Git. Regenerated via graphify update . after code changes.

## Telegram Bot Security
Chat ID open for patient bookings. Rate limiting (15 msg/min) and input sanitization replace whitelist for booking mode. Legacy Cowork mode restricted to authorized Chat ID. Telegram Bot Token stored in .env via TELEGRAM_BOT_TOKEN variable. API credentials in environment variables, not hardcoded.

## Booking Agency Security
Patient identification by cédula/RUC/passport with validation algorithm (Ecuadorian ID checksum, RUC format, passport format). doc_id serves as universal patient key across Telegram and Email channels, preventing cross-channel identity confusion. Rate limiting: 15 messages per minute per Telegram user, 3 emails per hour per address. Input sanitization: max 500 chars (Telegram) or 1000 chars (Email), control characters stripped. Prompt injection defenses applied to all LLM calls. DeepSeek Flash API used with JSON mode for structured outputs preventing injection. Session state in Redis keyed by doc_id (2h TTL), isolated per patient. Email IMAP polling restricted to UNSEEN messages from last 5 minutes, max 5 per cycle. Email queue respects Mail.ru 1 email/minute rate limit with double protection (APScheduler 60s interval + last_sent_time check). Patient data only accessible via authenticated doc_id. /reset command unlinks telegram_chat_id without deleting patient records. APScheduler runs in-process within Telegram bot, no external cron exposure. All Redis operations async via run_in_executor.

## Tool Security

tool_shell uses shlex.split() + shell=False (shell injection fixed). tool_web requires --confirm flag. tool_edit has path traversal protection (os.path.realpath). Without confirmation, user receives warning message. --confirm is stripped from actual command before execution. Playwright browsers isolated in /browsers/ directory within project.

## Sub-Graph Security
Each worker runs in its own isolated sub-graph with independent state. code_worker uses CodeWorkerState, design_worker uses DesignWorkerState, codewhale_worker shares CoworkState. Sub-graphs cannot access each other state. All wrappers propagate errors to state.errors for proper diagnosis. OpenDesign daemon runs on fixed port 34095 bound to localhost only.

## OpenDesign Security
OpenDesign daemon auto-detects coding agents on PATH. Only connects to localhost. API key passed via environment variable, not stored in OpenDesign config. Design artifacts stored in .od/projects/ directory, gitignored. Daemon located at workers/open-design/.

## Workers Directory Security
All worker binaries and services consolidated in workers/:
- workers/codewhale/ — CodeWhale TUI binary with dynamic path detection
- workers/opencode-pro/ — Reserved for future assistant, currently empty
- workers/open-design/ — OpenDesign daemon, gitignored artifacts

## v3.4.1 Security Improvements (22 + Phase 35)
- Shell injection: shlex.split() + shell=False in tool_shell
- Path traversal: os.path.realpath() validation in tool_edit
- DB credentials: separate parameters (host/user/password/database), no URL construction
- Redis: shared connection pool via graph/redis_client.py singleton, _redis_safe() wrapper on all operations
- Exception handling: specific exceptions (no bare except), logger.warning for Redis errors
- Hardcoded paths: replaced with dynamic os.path.dirname detection
- Webhook n8n: N8N_WEBHOOK_TOKEN header support
- Plan cache: hashlib.sha256 instead of non-deterministic hash()
- History loading: lrange(-6, -1) instead of loading all messages
- continue_session: resets iteration_count and errors
- JSON extraction: balanced bracket parser for nested objects
- MCP chat: disabled (redirects to codewhale-tui)
- Dead code: graph/nodes/ removed, chat.py deleted, Step class removed, plan system removed
- Prompt injection: -- flag protection on subprocess calls
- Interpreter safety: sys.executable instead of hardcoded "python"
- Async Redis: run_in_executor wrappers for booking operations
- googledrive: removed from mcp_client.py and .mcp.json

## Best Practices

Never commit dotenv file. Use strong PostgreSQL passwords. Review MCP allowed paths. Keep Docker sandbox enabled for untrusted code. Rotate API keys periodically. Review worker_prompt.txt before deployment. Use dedicated bot accounts for all integrations.

## Supported Versions

Version 3.4.1 with 4 workers via sub-graph architecture + Mail.ru email + Booking Agency (Telegram + Email). Workers consolidated in workers/ directory. 26+ bugs fixed, production ready.

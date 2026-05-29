# Security Policy

## Reporting

Email the maintainer directly. Do not open public issues.

## Principles

API Keys: Never hardcoded. Loaded via os.getenv from environment variables. dotenv file excluded from Git. Zero API keys in committed code.

Tool Restrictions: Filesystem MCP whitelisted paths only. Shell MCP whitelisted commands with destructive commands blocked. Git MCP read-only. Docker MCP read-only.

Docker Sandbox: Full container isolation. No network access. Read-only filesystem. Resource limits. No privilege escalation. SELinux compatible.

Prompt Injection Defenses: Pattern-based detection. Input sanitization. Tool argument validation. Length limits on input.

Database: Credentials via environment variables only. No default passwords. 8 tables with UUID primary keys and audit timestamps.

File Watcher Security: Monitors specified directories only. Filters by file extension. Ignores temp files. Auto-execution disabled by default.

Graph Security: LangGraph loop limited to 5 iterations. DeepSeek planner uses JSON mode with response_format json_object. OpenCode worker runs via subprocess with timeout protection. Validation runs pytest in subprocess. Multi-file generation with path sanitization. Auto-install and auto-tests with timeout protection.

Integration Security: Gmail and Telegram use dedicated bot accounts, never personal credentials. Google Calendar uses email invitations via ICS files, no OAuth tokens stored. All external API calls use environment variables for authentication.

OpenCode Worker Security: OpenCode CLI runs as subprocess with 600 second timeout. Flash FREE model accessed via OpenCode configuration, no direct API key exposure. Worker prompt requests JSON format to avoid markdown injection. clean_code() removes non-ASCII characters and validates output before execution.

## Audit Results May 2026

Zero API keys committed. Zero personal emails exposed. Zero local IPs exposed. All sensitive data in dotenv excluded from Git. Project unified into single folder. Anthropic proxy removed, reducing attack surface. OpenCode CLI direct integration eliminates proxy translation layer.

## PDF Processing Security
PDF files read via pypdf with no shell execution. Extracted text sanitized. No PDF rendering or JavaScript execution. Path validated before access.

## Code Generation Security
Generated scripts saved to output/projects/ directory. Scripts executed via subprocess.run with timeout. Output captured, not printed directly to terminal. JSON validation before script extraction. Non-ASCII characters removed to prevent injection.

## Redis Security
Redis runs locally without password on port 6379. Not exposed externally. Keys have TTL (5 minutes to 1 hour) to auto-expire and prevent memory buildup. No sensitive data stored permanently in Redis.

## n8n Security
n8n API key stored in dotenv file excluded from Git. MCP server uses JWT authentication. Webhook endpoints protected by n8n internal auth. Credentials configured via n8n UI, not exposed in workflow JSON exports.

## Graphify Security
Graphify output stored in graphify-out/ directory. GRAPH_REPORT.md contains function names and file paths only, no secrets. Excluded from Git. Regenerated via graphify update . after code changes.

## Telegram Bot Security
Chat ID whitelist: only authorized user (8047752200) can interact with the bot. Unknown chat_ids receive rejection message. Telegram Bot Token stored in .env via TELEGRAM_BOT_TOKEN variable. API credentials in environment variables, not hardcoded.

## Tool Security

tool_shell and tool_web require --confirm flag for execution. Without confirmation, user receives warning message. --confirm is stripped from actual command before execution. Playwright browsers isolated in /browsers/ directory within project.

## Sub-Graph Security
Each worker runs in its own isolated sub-graph with independent state. code_worker uses CodeWorkerState, design_worker uses DesignWorkerState, mcp_worker shares CoworkState. Sub-graphs cannot access each other state. OpenDesign daemon runs on fixed port 34095 bound to localhost only.

## OpenDesign Security
OpenDesign daemon auto-detects coding agents on PATH. Only connects to localhost. API key passed via environment variable, not stored in OpenDesign config. Design artifacts stored in .od/projects/ directory, gitignored.

## Best Practices

Never commit dotenv file. Use strong PostgreSQL passwords. Review MCP allowed paths. Keep Docker sandbox enabled for untrusted code. Rotate API keys periodically. Review worker_prompt.txt before deployment. Use dedicated bot accounts for all integrations.

## Supported Versions

Version 3.2 with 3 workers via sub-graph architecture.

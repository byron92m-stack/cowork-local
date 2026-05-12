# Security Policy

## Reporting

Email the maintainer directly. Do not open public issues.

## Principles

API Keys: Never hardcoded. Loaded via os.getenv from environment variables. dotenv file excluded from Git. Zero API keys in committed code.

Tool Restrictions: Filesystem MCP whitelisted paths only. Shell MCP whitelisted commands with destructive commands blocked. Git MCP read-only. Docker MCP read-only.

Docker Sandbox: Full container isolation. No network access. Read-only filesystem. Resource limits. No privilege escalation. SELinux compatible.

Prompt Injection Defenses: Pattern-based detection. Input sanitization. Tool argument validation. Length limits on input.

Database: Credentials via environment variables only. No default passwords. 7 tables with UUID primary keys and audit timestamps.

File Watcher Security: Monitors specified directories only. Filters by file extension. Ignores temp files. Auto-execution disabled by default.

Graph Security: LangGraph loop limited to 4 iterations. DeepSeek planner uses JSON mode with response_format json_object. OpenCode worker runs via subprocess with timeout protection. Validation runs pytest in subprocess. Multi-file generation with path sanitization. Auto-install and auto-tests with timeout protection.

Integration Security: Gmail and Telegram use dedicated bot accounts, never personal credentials. Google Calendar uses email invitations via ICS files, no OAuth tokens stored. All external API calls use environment variables for authentication.

OpenCode Worker Security: OpenCode CLI v1.14.48 runs as subprocess with 180 second timeout. Flash FREE model accessed via OpenCode configuration, no direct API key exposure in graph code. Worker prompt loaded from external file for easy auditing.

## Audit Results May 2026

Zero API keys committed. Zero personal emails exposed. Zero local IPs exposed. All sensitive data in dotenv excluded from Git. Project unified into single folder. Anthropic proxy removed, reducing attack surface. OpenCode CLI direct integration eliminates proxy translation layer.

## Best Practices

Never commit dotenv file. Use strong PostgreSQL passwords. Review MCP allowed paths. Keep Docker sandbox enabled for untrusted code. Rotate API keys periodically. Review worker_prompt.txt before deployment. Use dedicated bot accounts for all integrations.

## Supported Versions

Version 3.2 with multi-agent OpenCode worker.

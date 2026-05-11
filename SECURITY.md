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

Proxy Security version 3.1.1: localhost only port 8080. API key via environment variable. Cowork mode executes via subprocess with timeout. CLAUDE.md auto-loaded as system prompt.

Graph Security version 3.1.1: LangGraph loop limited to 3 iterations. DeepSeek planner uses JSON mode. Qwen3 worker runs locally on GPU. Validation runs pytest in subprocess. Tools integrated with timeout protection.

## Audit Results May 2026

Zero API keys committed. Zero personal emails exposed. Zero local IPs exposed. All sensitive data in dotenv excluded from Git. Project unified into single folder. No orphan files.

## Best Practices

Never commit dotenv file. Use strong PostgreSQL passwords. Review MCP allowed paths. Keep Docker sandbox enabled for untrusted code. Rotate API keys periodically. Keep proxy on localhost only.

## Supported Versions

Version 3.1.1 Unified only.

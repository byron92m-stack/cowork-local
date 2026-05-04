# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please DO NOT open a public issue. Email the maintainer directly with details, steps to reproduce, and potential impact. Allow time for a fix before public disclosure.

## Security Principles

### API Keys
- Never hardcoded in source code
- Always loaded via os.getenv() from environment variables
- Template provided as .env.example with no real values
- .env excluded from Git via .gitignore
- Verified: zero API keys in committed code (audit May 2026)

### Tool Restrictions
- Filesystem MCP: Whitelisted paths only
- Shell MCP: Whitelisted commands, destructive commands blocked
- Git MCP: Read-only operations (status, diff, log, branch, show)
- Docker MCP: Read-only operations (ps, logs, inspect, stats)

### Docker VM Sandbox
- Full container isolation with no network access
- Read-only filesystem with tmpfs exceptions
- Resource limits (CPU, memory, PIDs)
- No privilege escalation (no-new-privileges, cap-drop=ALL)
- Automatic container cleanup after execution
- Timeout protection against infinite loops
- SELinux compatible for Fedora/RHEL systems

### Prompt Injection Defenses
- Pattern-based detection of injection attempts
- Input sanitization (control character removal)
- Tool argument validation before execution
- Length limits on user input (10,000 chars)

### Write Protection
All write operations require explicit user confirmation by default. Enable sandbox_mode to disable all write operations entirely.

### Database
- Credentials stored in environment variables only
- No default passwords, POSTGRES_PASSWORD is required
- Connection parameters from env vars, not config files
- 7 tables with UUID primary keys and audit timestamps

### File Watcher Security
- Monitors only specified directories
- Filters by file extension patterns
- Ignores temp files (__pycache__, venv, .git)
- Auto-execution disabled by default

## Audit Results (May 2026)

- Zero API keys in committed code
- Zero personal emails exposed
- Zero local IPs exposed
- All sensitive data in .env (excluded from Git)
- 80 files verified, no orphan or legacy files

## Best Practices for Users

1. Never commit .env file
2. Use strong PostgreSQL passwords in production
3. Review MCP allowed paths and configure only what you need
4. Keep Docker sandbox enabled when running untrusted code
5. Rotate API keys periodically
6. Review file watcher directories before enabling auto-execution

## Supported Versions

Latest version only is supported (v2.0).

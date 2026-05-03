# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please DO NOT open a public issue. Email the maintainer directly with details, steps to reproduce, and potential impact. Allow time for a fix before public disclosure.

## Security Principles

### API Keys
- Never hardcoded in source code
- Always loaded via os.getenv() from environment variables
- Template provided as .env.example with no real values
- .env excluded from Git via .gitignore

### Tool Restrictions
- Filesystem MCP: Whitelisted paths only
- Shell MCP: Whitelisted commands, destructive commands blocked
- Git MCP: Read-only operations (status, diff, log, branch, show)
- Docker MCP: Read-only operations (ps, logs, inspect, stats)

### Write Protection
All write operations require explicit user confirmation by default. Enable sandbox_mode to disable all write operations entirely.

### Database
- Credentials stored in environment variables only
- No default passwords, POSTGRES_PASSWORD is required
- Connection parameters from env vars, not config files

## Best Practices for Users

1. Never commit .env file
2. Use strong PostgreSQL passwords in production
3. Review MCP allowed paths and configure only what you need
4. Keep sandbox mode on when running untrusted queries
5. Rotate API keys periodically

## Supported Versions

Latest version only is supported.

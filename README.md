# Cowork-Local v3.1.1

Autonomous AI Development Assistant for Fedora 43.

Claude Code CLI as unified interface. DeepSeek Cloud brain. Qwen 3 14B GPU executor. 14 MCP Servers. 23 Skills. Gmail, Telegram, Calendar integration. 5/5 tests passing. Cost: approximately 0.50 dollars per month.

Architecture: 1 Brain (DeepSeek Cloud, 128K context) plus 1 Executor (Qwen 3 GPU, 32 tokens per second) plus LangGraph (6 nodes) plus 14 MCP Servers plus 23 Skills.

Two Modes: Cowork Mode (prefix "cowork:") for full autonomous graph execution. Code Mode (default) for DeepSeek code generation and analysis.

14 MCP Servers: Filesystem, Shell, Git, Docker, Browser, WebSearch, Code Sandbox, Docker Sandbox, File Watcher, Gmail, Google Drive, Notion, Calendar, Telegram, Skills.

23 Skills: PDF, Excel, PowerPoint, Charts, Tests, Code Review, Docs, Email, Web Search, GitHub, GitLab, Slack, Notion.

Integrations: Gmail (read and send), Telegram (notifications and commands), Google Calendar (events via email), File Watcher (auto-trigger on changes).

Testing: 5 tests passing, Tool Caller with 5 format detection at 90 percent reliability, PostgreSQL memory with 7 tables.

Quick Start: cd /media/SSD1T/cowork-local, source ./activate-unificado.sh, claude-code/node_modules/.bin/claude --model deepseek-chat.

License: MIT.

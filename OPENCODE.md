# OPENCODE.md — Cowork-Local v3.1.1 (OpenCode Edition)

## Operation Modes

### COWORK MODE (prefix "cowork:")
Full autonomous graph. DeepSeek Flash plans, generates multi-file projects, pytest validates, DeepSeek Flash reviews, loop decides. Execute: ./apps/cli/loop.sh "task". Multi-file JSON output with auto-install and auto-tests.

### CODE MODE (default)
DeepSeek V4 Pro via OpenCode CLI. Native tool calling. Generate code, explain, analyze. Fast responses with automatic testing.

## Rules
- Prioritize code generation over explanations
- Do not modify files without asking
- Use absolute paths: /media/SSD1T/cowork-local/
- When user asks to create/generate code, use ./apps/cli/loop.sh

## Tools

### Code Generation
- ./apps/cli/loop.sh "task" — full autonomous graph with multi-file JSON output, auto-install and auto-tests
- opencode run "prompt" — fast code generation with native tool calls
- python apps/cli/execute_command.py write-file /path — create file via stdin
- python apps/cli/execute_command.py write-json /path — create file via JSON
- python apps/cli/cowork_graph.py "task" — direct graph execution

### Search
- python apps/cli/search_tools.py search "query" — grep code across the project
- python apps/cli/search_tools.py find "*.py" — find files by pattern
- python apps/cli/search_tools.py modules — list all Python modules

### Code Manipulation
- python apps/cli/apply_diff.py change file "old" "new" — replace text in file
- python apps/cli/apply_diff.py line file N "new" — replace a specific line
- python apps/cli/tool_caller.py — detects and executes tool calls in 5 formats at 90 percent reliability

### Memory
- python apps/cli/session_memory.py save "query" — save session to PostgreSQL
- python apps/cli/session_memory.py load 5 — load recent session history from PostgreSQL

### AI Skills via MCP Skills Server
- generate_tests: Generate pytest unit tests for any code
- review_code: Review code for bugs, performance issues, and best practices
- generate_docs: Generate docstrings and full documentation
- generate_pdf: Create formatted PDF documents
- generate_excel: Create formatted Excel spreadsheets
- generate_pptx: Create PowerPoint presentations with themes
- generate_chart: Create charts as PNG images with bar, line, pie, and scatter types
- web_search: Search the web via DuckDuckGo for current information

### Integrations
- Gmail: Read emails with gmail_read, send emails with gmail_send via dedicated bot account
- Telegram: Send notifications with telegram_send, read messages with telegram_read via @byron92m_bot
- Google Calendar: Create events via email invitations with calendar_add
- File Watcher: Auto-detects file changes and triggers graph via auto_watcher.py

## Testing
- pytest tests/ -v — run all tests, currently 5 out of 5 passing

# OPENCODE.md — Cowork-Local v3.2.0

## Operation Modes

### COWORK MODE (multi-agent)
Full autonomous graph. DeepSeek V4 Pro plans, OpenCode + DeepSeek V4 Flash FREE generates multi-file projects, pytest validates, DeepSeek V4 Pro reviews, loop decides up to 4 iterations. Execute: python apps/cli/cowork_graph.py "task". Multi-file output with auto-install and auto-tests. Cost: approximately $0.002 per project.

### CODE MODE (default)
DeepSeek V4 Pro via OpenCode CLI. Native tool calling. Generate code, explain, analyze. Fast responses with automatic testing. Execute: opencode run "prompt".

## Models
- Planner: deepseek/deepseek-v4-pro (paid)
- Worker: opencode/deepseek-v4-flash-free (FREE)
- Reviewer: deepseek/deepseek-v4-pro (paid)
- Local backup: qwen3:14b via Ollama on port 11434

## Rules
See `rules/` for detailed conventions:
- `rules/api.md` — FastAPI patterns, Pydantic validation, Swagger docs
- `rules/security.md` — Secrets management, env vars, input sanitization

Core rules:
- Prioritize code generation over explanations
- Do not modify files without asking
- Use absolute paths: /media/SSD1T/cowork-local/
- When user asks to create/generate code, use python apps/cli/cowork_graph.py "task"

## Agents
See `agents/` for agent definitions:
- `agents/code-reviewer.md` — Reviews diffs for bugs, performance, best practices. Returns JSON with issues array.
- `agents/test-generator.md` — Generates pytest tests with mocks. Covers success, errors, edge cases. Minimum 15 tests.

## Tools

### Code Generation
- python apps/cli/cowork_graph.py "task" — full autonomous graph with OpenCode worker, auto-install and auto-tests, up to 4 iterations
- opencode run "prompt" — fast code generation with native tool calls
- ./apps/cli/loop.sh "task" — simplified wrapper with formatted output
- python apps/cli/execute_command.py write-file /path — create file via stdin
- python apps/cli/execute_command.py write-json /path — create file via JSON

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

### MCP Servers
15 MCP servers configured in `.mcp.json`: filesystem, shell, git, docker, browser, websearch, code_sandbox, filewatcher, docker_sandbox, gmail, googledrive, notion, skills, telegram, calendar.

## Testing
- pytest tests/ -v — run all tests, currently 5 out of 5 passing
- Auto-tests run on every cowork_graph.py execution
- Loop retries up to 4 iterations if tests fail

## Hooks
- `hooks/pre-commit.sh` — runs pytest and git status before commit
- `hooks/post-generate.sh` — runs pytest after code generation

## Project Structure
- apps/ — API (FastAPI), CLI tools (cowork_graph.py, loop.sh, search_tools.py, apply_diff.py, session_memory.py, auto_watcher.py)
- graph/ — LangGraph orchestrator (planner, worker_opencode, validation, review, decision)
- tools/ — 15 MCP servers (browser, calendar, code_sandbox, docker, docker_sandbox, filesystem, filewatcher, git, gmail, googledrive, notion, shell, skills, telegram, websearch)
- models/ — DeepSeek client and Qwen Ollama client
- config/ — settings.yaml and models.yaml
- rules/ — Coding conventions (api.md, security.md)
- agents/ — AI agent definitions (code-reviewer.md, test-generator.md)
- hooks/ — Automation scripts (pre-commit.sh, post-generate.sh)
- infra/ — Docker Compose for PostgreSQL
- output/ — Generated projects
- plugins/ — Skill marketplace with templates

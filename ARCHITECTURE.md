# Architecture — Cowork-Local v3.1.1

## Overview

Cowork-Local v3.1.1: Claude Code CLI as unified interface (cowork + code modes). DeepSeek Cloud brain. LangGraph 6-node orchestrator with integrated tools. Qwen 3 14B GPU executor. 12 MCP Servers. Gmail + Telegram integration. Tool Caller with 5 format detection. File Watcher with auto-execution. PostgreSQL memory.

Cost: ~$0.50/month.

## Two Modes Unified

### Cowork Mode ("cowork:")
1. task_intake — receives task + searches repo
2. deepseek_planner — DeepSeek JSON plan
3. qwen_worker — Qwen 3 GPU code generation
4. validation — pytest + auto-save PostgreSQL
5. supervisor_review — DeepSeek evaluation
6. loop_decision — complete or repeat (max 3 iterations)

### Code Mode (default)
DeepSeek Cloud via proxy. Anthropic format translation. CLAUDE.md auto-injected.

## Components

### Claude Code CLI
v2.1.138. Proxy port 8080. Dual mode. CLAUDE.md auto-loaded.

### Proxy (claude-code/proxy.py)
Flask. Port 8080. Anthropic↔DeepSeek translation.

### LangGraph (graph/graph.py)
6 nodes: intake, planner, worker, validation, review, decision.
Integrated: search_tools, apply_diff, session_memory, skills (tests, review, docs).

### CLI Tools
- loop.sh: Graph execution with output
- execute_command.py: write-file (3 modes), run-command, list-files, git-status, run-tests
- search_tools.py: grep, find, modules
- apply_diff.py: change text, replace lines, patches
- session_memory.py: PostgreSQL save/load
- tool_caller.py: 5 format tool call detection (90% reliability)
- auto_watcher.py: File change → auto graph

### Integrations
- Gmail: Read/send emails (MCP server, dedicated bot account)
- Telegram: Send notifications, read messages (MCP server, @byron92m_bot)

### Qwen 3 14B on Ollama
qwen3:14b (Q4_K_M, 9.3 GB). Port 11434. 32 tokens/s.

### DeepSeek Cloud
deepseek-chat. 128K context. JSON mode. ~$0.50/month.

### MCP Servers (12)
Filesystem, Shell, Git, Docker, Browser, WebSearch, Code Sandbox, Docker Sandbox, File Watcher, Gmail, Google Drive, Notion, Skills (23+).

### PostgreSQL (7 tables)
sessions, steps, artifacts, tool_usage, errors, project_memory, scheduled_tasks.

## Security

API keys via .env (gitignored). Proxy localhost-only. Whitelisted paths/commands. Git/Docker read-only.

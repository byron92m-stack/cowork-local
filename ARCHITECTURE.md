# Architecture — Cowork-Local v3.1.1

## Overview

Cowork-Local v3.1.1 implements a unified agentic architecture with Claude Code CLI as the single interface offering two modes: Cowork (autonomous graph) and Code (generation). DeepSeek Cloud is the brain, LangGraph orchestrates a 6-node graph with integrated tools, Qwen 3 14B on Ollama GPU is the executor, and 12 MCP servers provide real file operations.

Total cost: approximately 0.50 USD per month (DeepSeek API only).

## Two Modes Unified

### Cowork Mode (prefix "cowork:")
Proxy intercepts and calls loop.sh which executes the full LangGraph pipeline:
1. task_intake — receives task + searches repo for context
2. deepseek_planner — DeepSeek generates JSON plan
3. qwen_worker — Qwen 3 GPU generates code (or uses skills: tests, review, docs)
4. validation — pytest + auto-saves session to PostgreSQL
5. supervisor_review — DeepSeek reviews results
6. loop_decision — completes or repeats up to 3 iterations

### Code Mode (default)
Forwarded to DeepSeek Cloud through proxy. Anthropic format translation.

## Tools Integrated into Graph

All CLI tools are now connected to the graph nodes:
- search_tools.py → task_intake (auto-context from repo)
- apply_diff.py → qwen_worker (auto-fix on generated code)
- session_memory.py → validation (auto-save to PostgreSQL)
- generate_tests, review_code, generate_docs → qwen_worker (via skills)

## Components

### Claude Code CLI
v2.1.138. Proxy on localhost:8080. CLAUDE.md auto-loaded as system prompt.

### Proxy (claude-code/proxy.py)
Flask. Port 8080. Dual mode detection. CLAUDE.md injection.

### LangGraph (graph/graph.py)
6 nodes: intake, planner, worker, validation, review, decision.
Integrated: search, diffs, memory, skills.

### CLI Tools
- loop.sh: Clean graph output with progress
- execute_command.py: write-file (args, stdin, JSON), run-command, list-files, git-status, run-tests
- search_tools.py: grep, find, modules
- apply_diff.py: change text, replace lines, apply patches
- session_memory.py: PostgreSQL save/load
- auto_watcher.py: File change detection → auto graph execution

### Qwen 3 14B on Ollama
qwen3:14b (Q4_K_M, 9.3 GB). Port 11434. 32 tokens/s. Visible reasoning.

### DeepSeek Cloud
deepseek-chat. 128K context. JSON mode for planning. ~0.50 USD/month.

### MCP Servers (12)
Filesystem, Shell, Git, Docker, Browser, WebSearch, Code Sandbox, Docker Sandbox, File Watcher, Gmail, Google Drive, Notion, Skills (23+).

### PostgreSQL (7 tables)
sessions, steps, artifacts, tool_usage, errors, project_memory, scheduled_tasks.

## Security Model

API keys via .env (gitignored). Proxy localhost-only. Filesystem MCP whitelisted paths. Shell MCP whitelisted commands. Git/Docker MCP read-only. Docker Sandbox no network, read-only, resource limits.

## Why This Architecture?

DeepSeek Cloud (Brain): 0.50 USD/month, 128K context, excellent reasoning.
Qwen 3 14B GPU (Executor): 0 USD, local code generation, 32 tokens/s.
LangGraph (Orchestrator): 0 USD, 6 nodes, conditional routing with integrated tools.
Claude Code CLI (Interface): 0 USD, unified with two modes.

This split maximizes quality while minimizing cost. Cloud for strategy. Local for execution. Graph for automation. Single interface for simplicity.

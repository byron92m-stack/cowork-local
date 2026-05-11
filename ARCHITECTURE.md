# Architecture — Cowork-Local v3.1.1

## Overview

Claude Code CLI as unified interface with two modes. DeepSeek Cloud brain. LangGraph 6-node orchestrator with integrated tools. Qwen 3 14B GPU executor. 14 MCP Servers. Gmail, Telegram, Calendar integration. Tool Caller with 5 format detection. File Watcher with auto-execution. PostgreSQL memory. 5 tests passing. Cost: approximately 0.50 dollars per month.

## Two Modes

Cowork Mode (prefix "cowork:"): task_intake searches repo, deepseek_planner generates JSON plan, qwen_worker generates code via GPU, validation runs pytest and saves to PostgreSQL, supervisor_review evaluates, loop_decision completes or repeats up to 3 iterations.

Code Mode (default): DeepSeek Cloud via proxy with Anthropic format translation and CLAUDE.md auto-injection.

## Components

Claude Code CLI v2.1.138 with proxy on port 8080. Dual mode detection. CLAUDE.md auto-loaded as system prompt.

Proxy is Flask on port 8080 translating Anthropic format to DeepSeek format.

LangGraph with 6 nodes: intake, planner, worker, validation, review, decision. Integrated tools: search_tools, apply_diff, session_memory, skills for tests, review, and docs.

CLI Tools: loop.sh for graph execution, execute_command.py with 3 write modes plus run-command, list-files, git-status, run-tests. search_tools.py for grep, find, modules. apply_diff.py for text changes, line replacement, patches. session_memory.py for PostgreSQL save and load. tool_caller.py with 5 format detection at 90 percent reliability. auto_watcher.py for file change detection triggering graph.

Integrations: Gmail read and send via MCP server with dedicated bot account. Telegram send and read via MCP server using at byron92m_bot. Google Calendar event creation via email invitations.

Qwen 3 14B on Ollama using Q4_K_M quantization at 9.3 GB on port 11434 generating 32 tokens per second.

DeepSeek Cloud using deepseek-chat model with 128K context and JSON mode at approximately 0.50 dollars per month.

14 MCP Servers: Filesystem, Shell, Git, Docker, Browser, WebSearch, Code Sandbox, Docker Sandbox, File Watcher, Gmail, Google Drive, Notion, Calendar, Telegram, Skills with 23 plus tools.

PostgreSQL with 7 tables: sessions, steps, artifacts, tool_usage, errors, project_memory, scheduled_tasks.

## Security

API keys via dotenv file excluded from git. Proxy localhost only. Whitelisted paths and commands. Git and Docker read-only. Docker Sandbox with no network and resource limits.

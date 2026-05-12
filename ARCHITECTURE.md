# Architecture — Cowork-Local v3.1.1

## Overview

OpenCode CLI v1.14.48 as unified interface with two modes. DeepSeek Cloud brain using V4 Pro for Code Mode and V4 Flash for Cowork Mode. LangGraph 6-node orchestrator with multi-file JSON project generation. 14 MCP Servers. 23 Skills. Gmail, Telegram, Calendar integration. Tool Caller with 5 format detection. File Watcher with auto-execution. PostgreSQL memory with 7 tables. 5 tests passing. Cost: approximately 0.50 dollars per month.

## Two Modes

Cowork Mode via loop.sh: task_intake receives the task, deepseek_planner generates a JSON plan using DeepSeek Flash, worker generates multi-file projects via JSON using DeepSeek Flash with auto-install and auto-tests, validation runs pytest and saves to PostgreSQL, supervisor_review evaluates using DeepSeek Flash, loop_decision completes or repeats up to 3 iterations. Multi-file output includes main code, tests, README, and pyproject.toml.

Code Mode via OpenCode CLI: DeepSeek V4 Pro with native tool calling. Fast code generation with automatic testing and README generation. No proxy needed, direct API access.

## Components

OpenCode CLI v1.14.48 installed globally via npm. Direct connection to DeepSeek Cloud without proxy translation layer. OPENCODE.md auto-loaded as project context.

LangGraph with 6 nodes: intake, planner, worker, validation, review, decision. Worker uses DeepSeek V4 Flash with JSON mode for multi-file project generation. Auto-install via pip install and auto-tests via pytest after file creation. Integrated tools: search_tools, apply_diff, session_memory, skills for tests, review, and docs.

CLI Tools: loop.sh for graph execution with multi-file detection. execute_command.py with 3 write modes plus run-command, list-files, git-status, run-tests. search_tools.py for grep, find, modules. apply_diff.py for text changes, line replacement, patches. session_memory.py for PostgreSQL save and load. tool_caller.py with 5 format detection at 90 percent reliability. auto_watcher.py for file change detection triggering graph. cowork_graph.py for direct graph execution.

Worker: DeepSeek V4 Flash via API with system prompt loaded from worker_prompt.txt. Generates JSON with files array containing name and content for each project file. Supports two JSON formats: files array and content dictionary. Auto-installs project dependencies and runs pytest after generation.

Integrations: Gmail read and send via MCP server with dedicated bot account. Telegram send and read via MCP server using at byron92m_bot. Google Calendar event creation via email invitations using dot ICS files.

Qwen 3 14B on Ollama using Q4_K_M quantization at 9.3 GB on port 11434 generating 32 tokens per second. Available as backup worker.

DeepSeek Cloud using deepseek-chat model for both V4 Flash and V4 Pro. 128K context and JSON mode for structured outputs. Approximately 0.50 dollars per month.

14 MCP Servers: Filesystem, Shell, Git, Docker, Browser, WebSearch, Code Sandbox, Docker Sandbox, File Watcher, Gmail, Google Drive, Notion, Calendar, Telegram, Skills with 23 plus tools.

PostgreSQL with 7 tables: sessions, steps, artifacts, tool_usage, errors, project_memory, scheduled_tasks.

## Security

API keys via dotenv file excluded from git. Whitelisted paths and commands. Git and Docker read-only. Docker Sandbox with no network and resource limits.

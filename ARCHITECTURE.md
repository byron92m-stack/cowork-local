# Architecture — Cowork-Local v3.2

## Overview

Multi-agent system with DeepSeek V4 Pro planner and OpenCode Flash FREE worker. LangGraph orchestrator with 5 nodes. 5 real tools (filesystem, document, web, shell, code generation). 16 MCP Servers. PostgreSQL + Redis. Telegram assistant 24/7 with multi-session support and conversation memory. Playwright for web automation. Graphify for code intelligence. 6 projects 100% tests. Cost ~$0.50/month.

## Multi-Agent Pipeline

**Planner** (DeepSeek V4 Pro): Classifies user intent into 6 types (code_generation, tool_filesystem, tool_document, tool_web, tool_shell, chat). Generates structured JSON plan. Loads conversation history from Redis for contextual responses. Caches plans for 1 hour.

**Worker** (OpenCode Flash FREE): For code_generation, generates complete Python projects with pytest. For tool_* and chat, executes MCP tools directly (os.walk, pypdf, pandas, Playwright, subprocess). Requires --confirm for dangerous operations (tool_shell, tool_web).

**Validation**: Processes pytest output for code projects. Counts passed/failed tests.

**Review**: Evaluates completeness. If all tests pass, marks complete.

**Decision**: Routes to planner (retry) or END. Saves conversation history to Redis. Sends Telegram notification via n8n on completion.

Maximum 5 iterations. Worker timeout: 600s. DeepSeek timeout: 180s.

## Intent Classification

DeepSeek Pro classifies every message into one of 6 types:
- **code_generation**: Create Python projects/CLI/API/library
- **tool_filesystem**: Find, list, search files with os.walk
- **tool_document**: Read PDF, Excel, CSV, TXT, MD, JSON, LOG
- **tool_web**: Navigate internet with Playwright (Chromium headless)
- **tool_shell**: Execute commands with subprocess (requires --confirm)
- **chat**: Answer questions, use conversation history for context

## Telegram Assistant

API endpoint `/chat/assistant` receives messages from Telegram bot. Bot polls every 10s. Multi-session via Redis: each chat_id has independent session with commands /list, /switch, /nueva, /cerrar, /estado, /pc. Conversation history stored in Redis with 1h TTL. Security: Chat ID whitelist, --confirm for tool_shell and tool_web.

## Models

Planner/Reviewer: deepseek-v4-pro (~$0.001/call). Worker: opencode/deepseek-v4-flash-free (FREE). Local backup: qwen3:14b via Ollama.

## Tools (execute_mcp_tool)

- **tool_filesystem**: os.walk with path extraction, extension filtering, 50 file limit
- **tool_document**: pypdf (PDF), pandas (Excel/CSV), direct file read (TXT/MD/JSON/LOG)
- **tool_web**: Playwright async API, Chromium headless, 15s timeout, text extraction
- **tool_shell**: subprocess.run with case-insensitive command extraction, --confirm required
- **code_generation**: OpenCode CLI with Flash FREE, auto-install, pytest validation

## Infrastructure

- PostgreSQL: 7 tables (sessions, steps, artifacts, tool_usage, errors, project_memory, scheduled_tasks)
- Redis: chat history, graph state, planner cache, session management
- n8n: port 5678, MCP native, Telegram notifications on project completion
- Graphify: 771 nodes, 1145 edges, 42 communities. Planner reads GRAPH_REPORT.md
- Playwright: Chromium headless in /browsers/ (~290MB)
- 16 MCP servers in .mcp.json + n8n-mcp + postgresql

## Security

API keys in .env (excluded from git). Telegram token and API password in environment variables. Chat ID whitelist (only authorized user). --confirm required for shell and web tools. Rate limiting via Redis. MCP servers use whitelisted paths and read-only modes.

## Hardware

Fedora 43. AMD Ryzen Starship Matisse. NVIDIA RTX 4060 Ti 16GB VRAM. 32GB RAM. NVMe 2TB (Btrfs) + SSD 1TB (ext4). Docker for PostgreSQL, Redis, n8n. Ollama qwen3:14b. Node.js v24.15.0.

## Monthly Cost

DeepSeek API ~$0.50/month. All other components free and open-source. Hardware already owned.

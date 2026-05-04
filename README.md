# Cowork-Local v2.0

## Agentic Development Assistant - Running Locally on Fedora 43

Cowork-Local is a fully autonomous AI-powered development assistant that plans, executes, reviews, and remembers, all running on your own hardware. It combines DeepSeek Cloud for strategic reasoning with Qwen 3 14B running locally on GPU for code generation, orchestrated by LangGraph with persistent memory via PostgreSQL.

## System Architecture

The system has five layers: Supervisor (DeepSeek Cloud, plans), Executor (Qwen 3 14B GPU, generates real code), Reviewer (DeepSeek Cloud, evaluates), 12 MCP Tools (Filesystem, Shell, Git, Docker, Browser, WebSearch, Docker Sandbox, Code Sandbox, File Watcher, Gmail, Google Drive, Notion, Skills), and PostgreSQL with 7 tables for persistent memory. All orchestrated by LangGraph with four interfaces: CLI, API REST with SSE streaming, Streamlit Web UI, and Qwen CLI direct chat.

## Agentic Flow

User query flows through: MEMORY loads context from PostgreSQL, SUPERVISOR generates JSON plan with DeepSeek (5-7 steps), TOOLS execute system operations (read files, list directories), EXECUTOR generates real code with Qwen 3 GPU, REVIEWER evaluates results with DeepSeek, MEMORY saves generated files to disk and persists everything to PostgreSQL. Cycle repeats until all steps complete.

## Key Features

- Multi-Agent Architecture: Supervisor plans, Executor generates real code, Reviewer evaluates
- Local GPU Execution: Qwen 3 14B on NVIDIA RTX 4060 Ti 16GB VRAM with visible reasoning
- 12 MCP Servers: Filesystem, Shell, Git, Docker, Browser, WebSearch, Code Sandbox, Docker Sandbox, File Watcher, Gmail, Google Drive, Notion, Skills
- Docker VM Sandbox: Secure isolated code execution with no network, read-only filesystem, resource limits
- SSE Streaming: Real-time token streaming like Claude Cowork
- File Watcher: Detects file changes and auto-triggers agents
- 20+ Advanced Skills: PDF, Excel, PowerPoint, Charts, Email, Web Search, GitHub, Slack, GitLab, Notion
- Persistent Memory: PostgreSQL with 7 tables (sessions, steps, artifacts, tool_usage, errors, project_memory, scheduled_tasks)
- Multiple Interfaces: CLI, REST API with SSE streaming, Streamlit Web UI with dark theme, Qwen CLI direct chat
- Plugin Marketplace: YAML-based skill templates with versioning
- Knowledge Base: Document storage with search
- Workspace Manager: Multi-project persistent workspaces
- Prompt Injection Defenses: Pattern-based detection and input sanitization
- Ultra Low Cost: approximately 0.50 USD per month for DeepSeek API only
- 100 Percent Yours: No cloud dependencies, fully open-source (MIT), runs on your hardware

## Hardware and Infrastructure

- Operating System: Fedora 43
- CPU: AMD Ryzen (Starship/Matisse)
- GPU: NVIDIA RTX 4060 Ti 16GB VRAM
- RAM: 32 GB
- System Disk: NVMe 2TB (Btrfs)
- Project Disk: SSD 1TB (ext4)
- Local Model: Qwen 3 14B (Q4_K_M quantization, 9.3 GB)

## Monthly Costs

Hardware is 0 dollars already owned. DeepSeek API approximately 0.50 dollars for heavy usage. Qwen 3 Local GPU is 0 dollars running on your GPU. Streamlit, FastAPI, PostgreSQL, and MCP Servers are all 0 dollars open-source. Total approximately 0.50 dollars per month.

## Project Structure

- apps: API (FastAPI REST + SSE streaming), CLI (check, status, run), Web (Streamlit Dashboard, Real-time Chat, Pro UI)
- config: settings.yaml (global configuration with env vars), models.yaml (AI model settings)
- graph: Main LangGraph graph, CoworkState definition, 5 nodes (supervisor, executor, reviewer, tools_node, memory_manager)
- models: DeepSeek Cloud HTTP client, Ollama Qwen client
- tools: 12 MCP servers (filesystem, shell, git, docker, browser, websearch, code_sandbox, docker_sandbox, filewatcher, gmail, googledrive, notion, skills), unified MCP client, PostgreSQL helpers, scheduler, security, knowledge_base, workspace_manager, auto_executor, notifier
- infra: Docker Compose for PostgreSQL, database schema SQL with 7 tables
- plugins: Plugin manager, skill template YAML, catalog directory
- data: Generated files, logs, chats, knowledge base, workspaces
- Documentation: README, ARCHITECTURE, CONTRIBUTING, SECURITY, LICENSE, COWORK_PLAN
- Scripts: cowork (main CLI), cowork_chat.sh (direct Qwen 3 chat)

## PostgreSQL Schema

Seven tables provide complete persistence:
- sessions: conversation and task registry
- steps: plan steps with description, status, assigned_to
- artifacts: generated results (code, analysis, PDFs)
- tool_usage: audit trail for every tool call
- errors: debugging and error tracking
- project_memory: cross-session persistent context
- scheduled_tasks: CRON-based recurring tasks

## MCP Servers (12 Total)

- Filesystem: read_file, write_file, list_directory, search_files with whitelisted paths
- Shell: execute_command with whitelisted commands
- Git: git_operation read-only (status, diff, log, branch, show)
- Docker: docker_operation read-only (ps, logs, inspect, stats, version)
- Browser: navigate, click, fill, screenshot, extract
- WebSearch: search, news, fetch_page via DuckDuckGo
- Code Sandbox: execute_python, execute_shell, install_package
- Docker Sandbox: execute_python, execute_shell with full VM isolation (no network, read-only, resource limits)
- File Watcher: start_watching, stop_watching, get_changes, analyze_and_act
- Gmail: send_email, read_emails via OAuth/App Password
- Google Drive: list_files, upload_file, download_file, share_file
- Notion: create_page, search_pages
- Skills: 20+ advanced tools

## Advanced Skills

PDF Generator uses reportlab for formatted PDF files. Excel Generator uses openpyxl for formatted XLSX files. PowerPoint uses python-pptx for themed PPTX files. Charts uses matplotlib for bar, line, pie, and scatter PNG files. Data Analysis uses pandas for descriptive statistics. Email Sender uses yagmail for Gmail integration. Web Search uses ddgs for DuckDuckGo search. GitHub uses PyGithub for repos, issues, and code access. GitLab uses python-gitlab for repository access. Slack uses slack-sdk for channel messages.

## User Interfaces

- CLI Agentic: ./cowork run --query "your task" --project /path
- CLI Check: ./cowork check (verifies all services)
- Direct Qwen Chat: ./cowork_chat.sh (interactive chat with Qwen 3)
- Native Qwen CLI: ollama run qwen3:14b
- REST API: python -m apps.api.main on port 8000
- SSE Streaming: /stream/run, /stream/chat, /stream/qwen, /stream/demo
- Swagger UI: http://localhost:8000/docs
- Web UI: Streamlit Dashboard on port 8501

## Quick Start

Prerequisites: Python 3.12+ with venv, Docker for PostgreSQL, Ollama with qwen3:14b pulled, DeepSeek API key from platform.deepseek.com.

Installation: git clone the repo, create and activate venv, pip install -r requirements.txt, ollama pull qwen3:14b, cp .env.example .env and edit with your keys, docker compose -f infra/docker-compose.yml up -d, run ./cowork check to verify.

Usage: ./cowork check verifies services, ./cowork status shows system state, ./cowork run --query "your task" executes an agentic task, ./cowork_chat.sh opens direct chat with Qwen 3. REST API via python -m apps.api.main on port 8000 with Swagger UI at /docs. Streamlit Web UI on port 8501.

## Key Achievements

- Complete agentic system with DeepSeek planning + Qwen 3 GPU code generation
- 12 MCP servers operational
- 20+ advanced skills
- Real-time SSE streaming like Claude Cowork
- Docker VM sandbox for secure code execution
- File watcher with auto-execution
- REST API with Swagger and SSE streaming
- PostgreSQL with 7 tables for complete persistence
- Plan-Execute-Review-Persist cycle fully functional
- Autonomous project generation (generated complete FastAPI library API with 5 files)
- Plugin marketplace with YAML templates
- Knowledge base with search
- Multi-workspace support
- Prompt injection defenses
- Open-source (MIT), multiplatform, no cloud vendor lock-in
- Total cost: approximately 0.50 USD per month

## Compare with Claude Cowork

Claude Cowork costs 60 dollars per month, runs only on macOS, and is proprietary. Cowork-Local costs 0.50 dollars per month, runs on Linux, macOS, and Windows, and is fully open-source. Both have: multi-agent architecture, real-time streaming, sandbox execution, file watching, scheduled tasks, web search, email integration, knowledge base, and plugin systems.

## License

MIT License. See LICENSE file for details.

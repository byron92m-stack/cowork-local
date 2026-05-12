# Cowork-Local v3.1.1

## Autonomous AI Development Assistant for Fedora 43

OpenCode CLI as unified interface with two modes. DeepSeek Cloud brain using V4 Pro and V4 Flash. LangGraph 6-node orchestrator with multi-file JSON project generation. 14 MCP Servers. 23 Skills. Gmail, Telegram, Calendar integration. PostgreSQL memory with 7 tables. 5 of 5 tests passing. File Watcher with auto-execution. Tool Caller with 5 format detection at 90 percent reliability.

Cost: approximately 0.50 dollars per month. Everything else runs locally on your hardware.

## System Architecture

Five layers, one system. Interface is OpenCode CLI v1.14.48 providing single input and output. Brain is DeepSeek Cloud with V4 Pro for Code Mode and V4 Flash for Cowork Mode, both with 128K context. Orchestrator is LangGraph with 6 nodes for task intake, DeepSeek planning, worker execution, validation, supervisor review, and loop decision. Worker is DeepSeek V4 Flash generating multi-file projects via JSON with auto-install and auto-tests. Tools are 14 MCP Servers for file operations, commands, Git, Docker, and Skills.

## Two Modes Unified in One CLI

Cowork Mode prefix "cowork:" activates the full autonomous graph. DeepSeek Flash generates a JSON plan, DeepSeek Flash generates multi-file projects via JSON output, the system validates with pytest and auto-installs dependencies, DeepSeek Flash reviews the result, and the loop decides whether to repeat or finish. Zero human supervision. Multi-file output with auto-install and auto-tests.

Code Mode is the default. DeepSeek V4 Pro via OpenCode CLI with native tool calling. Answers questions, explains concepts, analyzes code, suggests improvements. Fast code generation with automatic testing and README generation.

## Autonomous Loop

Step 1: INTAKE receives the task and searches the repository for context. Step 2: PLANNER using DeepSeek generates a JSON plan with concrete steps. Step 3: WORKER using DeepSeek V4 Flash generates multi-file projects via JSON with all files including main code, tests, README, and pyproject.toml. Step 4: VALIDATION runs pytest and auto-installs dependencies, then auto-saves the session to PostgreSQL. Step 5: REVIEW using DeepSeek evaluates results. Step 6: DECISION completes or repeats the loop. Maximum 3 iterations by default. Configurable with COWORK_MAX_ITER.

## Key Features

OpenCode CLI v1.14.48 with two modes for cowork and code. Autonomous graph loop for plan, generate, validate, review, and decide. Multi-file JSON project generation with auto-install and auto-tests. DeepSeek Cloud Brain with 128K context and JSON planning. LangGraph Orchestrator with 6 nodes and conditional routing with integrated tools. 14 MCP Servers including Filesystem, Shell, Git, Docker, Browser, WebSearch, Code Sandbox, Docker Sandbox, File Watcher, Gmail, Google Drive, Notion, Calendar, Telegram, and Skills. 23 plus Advanced Skills including PDF, Excel, PowerPoint, Charts, Email, Web Search, GitHub, Slack, GitLab, Notion, Test Generator, Code Review, and Doc Generator. Gmail Integration for reading and sending emails via dedicated bot account. Telegram Integration for sending notifications and reading commands via bot. Google Calendar Integration for creating events via email invitations. File Watcher that auto-detects changes and triggers the graph. Tool Caller that detects and executes tool calls in 5 formats at 90 percent reliability. PostgreSQL Memory with 7 tables for complete persistence. Docker VM Sandbox for secure isolated code execution. Prompt Injection Defenses. Plugin Marketplace with YAML templates.

## Hardware and Infrastructure

Operating System is Fedora 43. CPU is AMD Ryzen using Starship and Matisse architecture. GPU is NVIDIA RTX 4060 Ti with 16GB VRAM. RAM is 32 GB. System Disk is NVMe 2TB using Btrfs. Project Disk is SSD 1TB using ext4 at /media/SSD1T/. Local Model is Qwen 3 14B using Q4_K_M quantization at 9.3 GB via Ollama on port 11434, available as backup worker.

## Monthly Costs

DeepSeek API is approximately 0.50 dollars per month for both V4 Pro and V4 Flash usage. LangGraph is 0 dollars as open-source. OpenCode CLI is 0 dollars as open-source. All MCP Servers and tools are 0 dollars. Everything else is 0 dollars running locally. Total cost is approximately 0.50 dollars per month.

## Project Structure

The apps directory contains the API built with FastAPI, CLI tools including loop.sh, execute_command.py, tool_caller.py, search_tools.py, apply_diff.py, session_memory.py, auto_watcher.py, and Web UI built with Streamlit. The graph directory contains the LangGraph orchestrator with 6 nodes. The tools directory contains 14 MCP servers, unified client, and PostgreSQL helpers. The models directory contains the DeepSeek Cloud client and Qwen Ollama client. The config directory contains settings.yaml and models.yaml. The infra directory contains Docker Compose for PostgreSQL. The tests directory contains 5 tests passing at 100 percent. The output directory contains generated code and projects.

## Quick Start

Prerequisites are Python 3.12 plus, Node.js 22 plus, Docker, Ollama with qwen3 colon 14b as backup, and DeepSeek API key. Commands: cd /media/SSD1T/cowork-local, source ./activate-unificado.sh. For Code Mode use opencode run "your prompt". For Cowork Mode use ./apps/cli/loop.sh "your task".

## Key Achievements for version 3.1.1

OpenCode CLI with two integrated modes for cowork and code. Autonomous graph where DeepSeek plans, DeepSeek Flash generates multi-file projects, and the system validates. 6-node LangGraph with loop decision. 14 MCP servers operational. 23 plus advanced skills. Gmail, Telegram, and Calendar integration. PostgreSQL with 7 tables. Docker VM sandbox. File watcher with auto-execution. Tool Caller with 5 format detection. 5 of 5 tests passing. Open-source under MIT license with no cloud vendor lock-in. Total cost approximately 0.50 dollars per month.

## License

MIT License.

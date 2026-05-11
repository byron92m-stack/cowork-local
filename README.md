# Cowork-Local v3.1.1

## Autonomous AI Development Assistant for Fedora 43

Claude Code CLI as unified interface with two modes. DeepSeek Cloud brain. Qwen 3 14B GPU executor. LangGraph orchestrator with 6 nodes and integrated tools. 14 MCP Servers. 23 Skills. Gmail, Telegram, Calendar integration. PostgreSQL memory with 7 tables. 5/5 tests passing. File Watcher with auto-execution. Tool Caller with 5 format detection at 90 percent reliability.

Cost: approximately 0.50 dollars per month. Everything else runs locally on your hardware.

## System Architecture

Five layers, one system:

- Interface: Claude Code CLI v2.1.138 - single input/output, conversation memory
- Brain: DeepSeek Cloud - strategic reasoning, code generation, review (128K context)
- Orchestrator: LangGraph with 6 nodes - task_intake, deepseek_planner, qwen_worker, validation, supervisor_review, loop_decision
- Worker: Qwen 3 14B on Ollama GPU - real code generation (32 tokens per second, visible reasoning)
- Tools: 14 MCP Servers - file operations, commands, Git, Docker, Skills

## Two Modes Unified in One CLI

### Cowork Mode (prefix "cowork:")
Activates the full autonomous graph. DeepSeek generates a JSON plan, Qwen3 writes code on GPU, the system validates with pytest, DeepSeek reviews the result, and the loop decides whether to repeat or finish. Zero human supervision.

### Code Mode (default)
DeepSeek Cloud answers questions, explains concepts, analyzes code, suggests improvements. Code generation with DeepSeek.

## Autonomous Loop

1. INTAKE receives the task and searches the repo for context
2. PLANNER (DeepSeek) generates JSON plan with concrete steps
3. WORKER (Qwen3 GPU) generates real code using skills (tests, review, docs)
4. VALIDATION runs pytest and auto-saves session to PostgreSQL
5. REVIEW (DeepSeek) evaluates results
6. DECISION completes or repeats the loop

Maximum 3 iterations by default. Configurable with COWORK_MAX_ITER.

## Key Features

- Unified Claude Code CLI with two modes: cowork and code
- Autonomous graph loop: plan, generate, validate, review, decide
- DeepSeek Cloud Brain: 128K context, JSON planning, quality review
- Qwen 3 14B on Ollama GPU: local code generation at 32 tokens per second
- LangGraph Orchestrator: 6 nodes with conditional routing and integrated tools
- 14 MCP Servers: Filesystem, Shell, Git, Docker, Browser, WebSearch, Code Sandbox, Docker Sandbox, File Watcher, Gmail, Google Drive, Notion, Calendar, Telegram, Skills
- 23 plus Advanced Skills: PDF, Excel, PowerPoint, Charts, Email, Web Search, GitHub, Slack, GitLab, Notion, Test Generator (Qwen3), Code Review (Qwen3), Doc Generator (Qwen3)
- Gmail Integration: Read and send emails via dedicated bot account
- Telegram Integration: Send notifications and read commands via bot
- Google Calendar Integration: Create events via email invitations
- File Watcher: Auto-detects changes and triggers graph
- Tool Caller: Detects and executes tool calls in 5 formats (90 percent reliability)
- PostgreSQL Memory: 7 tables for complete persistence
- Docker VM Sandbox: Secure isolated code execution
- Prompt Injection Defenses
- Plugin Marketplace: YAML templates

## Hardware and Infrastructure

- OS: Fedora 43
- CPU: AMD Ryzen (Starship/Matisse)
- GPU: NVIDIA RTX 4060 Ti 16GB VRAM
- RAM: 32 GB
- System Disk: NVMe 2TB (Btrfs)
- Project Disk: SSD 1TB (ext4) at /media/SSD1T/
- Local Model: Qwen 3 14B (Q4_K_M, 9.3 GB) via Ollama on port 11434

## Monthly Costs

DeepSeek API: approximately 0.50 dollars per month. Qwen 3 GPU: 0 dollars (local). Ollama: 0 dollars. LangGraph: 0 dollars. Claude Code CLI: 0 dollars. Everything else: 0 dollars. Total: approximately 0.50 dollars per month.

## Project Structure

- claude-code/ - Claude Code CLI v2.1.138 with proxy
- apps/ - API (FastAPI), CLI (loop.sh, execute_command.py, tool_caller.py, search_tools.py, apply_diff.py, session_memory.py, auto_watcher.py), Web UI (Streamlit)
- graph/ - LangGraph orchestrator with 6 nodes
- tools/ - 14 MCP servers, unified client, PostgreSQL helpers
- models/ - DeepSeek Cloud client, Qwen Ollama client
- config/ - settings.yaml, models.yaml
- infra/ - Docker Compose for PostgreSQL
- tests/ - 5 tests passing (100 percent)
- output/ - Generated code and projects

## Quick Start

Prerequisites: Python 3.12 plus, Node.js 22 plus, Docker, Ollama with qwen3:14b, DeepSeek API key

Commands:
  cd /media/SSD1T/cowork-local
  source ./activate-unificado.sh
  claude-code/node_modules/.bin/claude --model deepseek-chat

Cowork Mode: cowork: Create a calculator in Python
Code Mode: Explain what LangGraph is
Terminal: ./apps/cli/loop.sh "Create a currency converter"

## Key Achievements (v3.1.1)

- Unified Claude Code CLI with two integrated modes
- Autonomous graph: DeepSeek plans, Qwen3 generates, system validates
- 6-node LangGraph with loop decision
- 14 MCP servers operational
- 23 plus advanced skills
- Gmail, Telegram, and Calendar integration
- PostgreSQL with 7 tables
- Docker VM sandbox
- File watcher with auto-execution
- Tool Caller with 5 format detection
- 5/5 tests passing
- Open-source (MIT), no cloud vendor lock-in
- Total cost: approximately 0.50 dollars per month

## License

MIT License.

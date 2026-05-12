# Cowork-Local v3.2 — Autonomous Multi-Agent Development Assistant

AI-powered system that generates complete, tested, production-ready Python CLI projects with zero human supervision. Built on LangGraph with DeepSeek V4 Pro planner and FREE Flash worker via OpenCode CLI. Runs locally on Fedora 43 with GPU acceleration.

## Results Summary

Four consecutive projects generated in a single iteration with FREE model, all tests passing:

webreq 34/34 passing. CLI for HTTP requests with six argparse flags, requests library, unittest.mock tests for all HTTP methods, JSON parsing, timeout handling, and verbose output. 12 CLI tests, 22 core tests.

logview 32/32 passing. Log file analyzer with six argparse flags, LogAnalyzer class with parse, filter, tail, to_json, and stats methods. Regex-based log level detection (ERROR, WARN, INFO, DEBUG). 32 pytest tests using temp files.

gitstat 48/48 passing. Git repository statistics with six argparse flags, GitStats class using subprocess to run git commands. Per-author commit counts, insertions, deletions, file changes. Output formats: table, JSON, CSV. 48 tests with temp git repos.

tcpdump-cli 41/41 passing. Network packet analyzer CLI with seven argparse flags using scapy library. Interface selection, port filtering, protocol filtering, BPF filter support, verbose mode, output file. 41 tests with mocks.

## Architecture

Multi-agent LangGraph pipeline with six nodes. Planner node uses DeepSeek V4 Pro to generate a structured JSON plan from natural language. Worker node executes plan via OpenCode CLI with DeepSeek V4 Flash FREE model, generating all project files simultaneously. Validation node runs pytest automatically. Review node evaluates test results against original requirements. Decision node determines whether project is complete or requires additional iterations. Maximum four iterations configured, all recent projects completed in one.

System operates with sub-cent cost per project. Planner calls DeepSeek Pro once at approximately 0.001 dollars. Worker uses completely free Flash model for unlimited code generation. No cloud vendor lock-in. Entire pipeline runs on local hardware.

## Technical Stack

LangGraph for agent orchestration with conditional routing between nodes. OpenCode CLI v1.14.48 as unified interface and worker execution engine. DeepSeek API for cloud models with response_format json_object for structured planning and code generation. PostgreSQL with seven tables for session persistence, step tracking, artifact storage, tool usage logging, error tracking, project memory, and scheduled tasks. Docker Compose for infrastructure. Ollama with qwen3:14b as local backup model.

Fifteen MCP servers provide tool access: filesystem operations, shell command execution with whitelist, git repository analysis, Docker container monitoring, headless browser automation, DuckDuckGo web search, subprocess code sandbox, Docker VM sandbox with network isolation, Watchdog file monitoring with auto-execution, Gmail integration via OAuth, Google Drive API, Notion API, Google Calendar, Telegram bot, and advanced skills server. Skills server includes PDF generation via reportlab, Excel generation via openpyxl, PowerPoint generation via python-pptx, matplotlib charts, pandas data analysis, yagmail email sending, PyGithub and python-gitlab API clients, and slack-sdk messaging.

Additional tools include semantic code search across projects, file pattern matching, AST-safe code manipulation with diff application, PostgreSQL session memory with save and load, and automatic file watching that triggers graph execution on changes. Security includes prompt injection defenses, command whitelisting, and path restrictions on all MCP servers.

## Interfaces

CLI via OpenCode with two modes. Cowork Mode executes full autonomous graph via python apps/cli/cowork_graph.py. Code Mode executes direct generation via opencode run. FastAPI REST API on port 8000 with SSE streaming support and Swagger documentation. Streamlit web dashboard on port 8501. VS Code extension with chat panel and contextual commands for code explanation and optimization. Direct chat with local Qwen model via cowork_chat.sh.

## Infrastructure

Fedora 43 operating system. AMD Ryzen processor, Starship Matisse architecture. NVIDIA RTX 4060 Ti with 16GB VRAM for local model inference. 32GB system RAM. NVMe 2TB system disk with Btrfs. SSD 1TB project disk with ext4 at /media/SSD1T. Docker for PostgreSQL and sandbox containers. Ollama serving qwen3:14b Q4_K_M at 9.3GB on port 11434. Node.js v24.15.0 for OpenCode CLI.

## Monthly Cost Breakdown

DeepSeek API approximately 0.50 dollars for intensive usage. All other components free and open-source including LangGraph, OpenCode CLI, FastAPI, Streamlit, PostgreSQL, Docker, Ollama, and fifteen MCP servers. Hardware already owned. Total monthly cost approximately 0.50 dollars.

## Comparison

Claude Code and Cursor charge 10 to 60 dollars monthly for cloud-only AI coding assistance. Cowork-Local provides equivalent or superior functionality at 0.50 dollars monthly with local execution, no rate limits, no data leaving the machine, and full MCP tool integration.

## License

MIT. Open-source, no restrictions.

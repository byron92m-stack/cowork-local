# Cowork-Local v3.2 — Autonomous Multi-Agent Development Assistant

AI-powered system that generates complete, tested, production-ready Python CLI projects with zero human supervision. Built on LangGraph with DeepSeek V4 Pro planner and FREE Flash worker via OpenCode CLI. Runs locally on Fedora 43 with GPU acceleration.

## Results Summary

Six consecutive projects generated in a single iteration with FREE model, all tests passing:

webreq 34/34. HTTP requests CLI with six argparse flags, unittest.mock tests for all HTTP methods, JSON parsing, timeout handling. 12 CLI tests, 22 core tests.

logview 32/32. Log file analyzer with six flags, LogAnalyzer class with parse, filter, tail, to_json, and stats. Regex-based log level detection. 32 pytest tests using temp files.

gitstat 48/48. Git repository statistics with six flags, GitStats class using subprocess. Per-author commit counts, insertions, deletions. Output formats: table, JSON, CSV. 48 tests with temp git repos.

tcpdump-cli 41/41. Network packet analyzer with seven flags using scapy. Interface selection, port filtering, protocol filtering, BPF support, verbose mode. 41 tests with mocks.

ai-reviewer 52/52. Code reviewer using DeepSeek API with seven flags. CodeReviewer class, multiple output formats (text/json/markdown), severity levels. 52 tests with unittest.mock.

graph-report 34/34. CLI that reads Graphify output. ReportParser class, top N nodes, community filtering. 34 tests with temp files.

## Architecture

Multi-agent LangGraph pipeline with five nodes. Planner uses DeepSeek V4 Pro to generate structured JSON plan. Worker executes via OpenCode CLI with DeepSeek V4 Flash FREE model, generating all project files. Validation runs pytest automatically. Review evaluates results. Decision determines completion or loop retry. Maximum five iterations. Telegram notification via n8n on every completion.

Redis provides fast state sharing between iterations and planner response caching. PostgreSQL persists sessions, steps, artifacts, errors, and project memory across seven tables. Graphify maps the codebase into 771 nodes and 1145 edges for architectural awareness.

## Technical Stack

LangGraph for agent orchestration. OpenCode CLI as unified interface and worker engine. DeepSeek API for cloud models. PostgreSQL + Redis for persistence and caching. Docker Compose for PostgreSQL, Redis, and n8n. Ollama with qwen3:14b as local backup model. n8n on port 5678 with native MCP server for workflow automation.

Sixteen MCP servers: filesystem, shell, git, docker, browser, websearch, code_sandbox, docker_sandbox, filewatcher, gmail, googledrive, notion, calendar, telegram, skills, postgresql, plus n8n-mcp. Skills server includes PDF, Excel, PowerPoint generation, matplotlib charts, pandas analysis, email sending, GitHub/GitLab APIs, and Slack messaging.

## Interfaces

Cowork Mode via python apps/cli/cowork_graph.py. Code Mode via opencode run. FastAPI REST API on port 8000 with SSE streaming and Swagger. OpenCode Web UI. VS Code via opencode-vscode extension with chat panel and contextual commands. Direct chat with Qwen via cowork_chat.sh. n8n dashboard on port 5678.

## Infrastructure

Fedora 43. AMD Ryzen Starship Matisse. NVIDIA RTX 4060 Ti 16GB VRAM. 32GB RAM. NVMe 2TB (Btrfs) + SSD 1TB (ext4). Docker for PostgreSQL, Redis, n8n. Ollama qwen3:14b Q4_K_M 9.3GB. Node.js v24.15.0.

## Monthly Cost

DeepSeek API approximately 0.50 dollars for intensive usage. All other components free and open-source. Hardware already owned. Total approximately 0.50 dollars per month.

## Comparison

Claude Code and Cursor charge 10 to 60 dollars monthly for cloud-only AI coding assistance. Cowork-Local provides equivalent or superior functionality at 0.50 dollars monthly with local execution, no rate limits, no data leaving the machine, and full MCP tool integration.

## License

MIT. Open-source, no restrictions.

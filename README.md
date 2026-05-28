# Cowork-Local v3.2 — Autonomous Multi-Agent Development Assistant

AI-powered system that generates complete, tested, production-ready Python CLI projects with zero human supervision. Built on LangGraph with DeepSeek V4 Pro planner and 3 specialized workers via sub-graph architecture. Runs locally on Fedora 43 with GPU acceleration.

## Results Summary

Six consecutive projects generated in a single iteration with FREE model, all tests passing: webreq 34/34, logview 32/32, gitstat 48/48, tcpdump-cli 41/41, ai-reviewer 52/52, graph-report 34/34. Average 40 tests per project. Zero iterations needed.

webreq: HTTP requests CLI with 6 argparse flags, unittest.mock tests for all HTTP methods, JSON parsing, timeout handling. 12 CLI tests, 22 core tests.

logview: Log file analyzer with LogAnalyzer class, regex-based level detection (ERROR, WARN, INFO, DEBUG). 32 pytest tests using temp files.

gitstat: Git repository statistics using subprocess. Per-author commit counts, insertions, deletions. Output formats: table, JSON, CSV. 48 tests with temp git repos.

tcpdump-cli: Network packet analyzer with 7 flags using scapy. Interface selection, port filtering, BPF support, verbose mode. 41 tests with mocks.

ai-reviewer: Code reviewer using DeepSeek API with 7 flags. Multiple output formats (text/json/markdown), severity levels. 52 tests with unittest.mock.

graph-report: CLI that reads Graphify output. ReportParser class, top N nodes, community filtering. 34 tests with temp files.

## Architecture

LangGraph with independent sub-graphs per worker. Planner uses DeepSeek V4 Pro to classify intent into 7 types and route to the correct worker. Three specialized workers: code_worker uses OpenCode plus Flash FREE to generate Python projects with pytest validation. design_worker uses OpenDesign API on port 34095 to generate UI, UX, landing pages, dashboards, and presentations. mcp_worker runs 5 local tools: filesystem via os.walk, document via pypdf and pandas, web via Playwright, shell via subprocess, and chat via DeepSeek.

Sub-graph architecture with independent state per worker. CodeWorkerState for code generation. DesignWorkerState for design tasks. CoworkState shared for MCP tools with Redis memory. Planner classification without hardcoded rules — DeepSeek Pro decides based on natural language.

Redis provides chat history with 24 hour TTL and planner response caching. PostgreSQL persists sessions, steps, artifacts, errors across 8 tables. Graphify maps the codebase into 2349 nodes with 3620 edges for architectural awareness.

## Telegram Assistant

Autonomous assistant via @byron92m_bot with all 5 tools accessible through natural language. Works 24/7 with polling every 10 seconds. Multi-session support with commands: list, switch, nueva, cerrar, estado, pc, ayuda. Conversation memory via Redis with 24 hour TTL. Intent classification via DeepSeek Pro. Security: Chat ID whitelist restricts access to authorized user only. Confirm flag required for shell and web tools.

## Technical Stack

LangGraph with sub-graphs for agent orchestration. OpenCode CLI as code generation engine. OpenDesign for design workflows. DeepSeek API for cloud models. PostgreSQL plus Redis for persistence. Playwright with Chromium headless for web automation. Graphify for codebase knowledge graph with 2349 nodes and 3620 edges. n8n on port 5678 for workflow automation. FastAPI plus Uvicorn on port 8000 with JWT auth and SSE streaming. Ollama with qwen3 colon 14b as local backup model. 16 MCP servers.

## Cost Analysis

DeepSeek V4 Pro planner costs approximately 0.001 dollars per project. DeepSeek Flash FREE worker costs zero dollars. OpenDesign API worker costs zero dollars. Local MCP tools cost zero dollars. PostgreSQL plus Redis plus n8n cost zero dollars. Playwright plus Graphify cost zero dollars. Total per project approximately 0.001 dollars. Total monthly for intensive use approximately 0.50 dollars.

## Comparison

Claude Code charges 20 dollars monthly for cloud-only single agent. Cursor charges 20 dollars monthly for cloud-only single agent. Copilot charges 10 dollars monthly for cloud-only single agent. Cowork-Local costs 0.50 dollars monthly with local execution and 3 specialized workers. No rate limits. No data leaving the machine. Design and UI generation included. Web browsing with Playwright included. Telegram bot 24/7 included. File system tools included.

## Quick Start

git clone https://github.com/byron92m-stack/cowork-local.git and cd cowork-local. source venv/bin/activate. export DEEPSEEK_API_KEY equals your key. python apps/cli/cowork_graph.py for Cowork Mode. python api-chat/telegram_bot.py for Telegram bot. opencode run for Code Mode. graphify update dot for knowledge graph.

## Infrastructure

Fedora 43 operating system. AMD Ryzen Starship Matisse processor. NVIDIA RTX 4060 Ti with 16GB VRAM. 32GB RAM. NVMe 2TB with Btrfs plus SSD 1TB with ext4. Docker for PostgreSQL, Redis, and n8n. Ollama serving qwen3 colon 14b Q4 underscore K underscore M at 9.3GB. Node.js v24.15.0.

## Security

API keys in dotenv file excluded from git. Chat ID whitelist for Telegram bot. Confirm flag required for shell and web tools. JWT authentication on API. MCP servers use whitelisted paths and read-only modes. Docker sandbox without network and with resource limits. Zero API keys committed to repository.

## License

MIT. Open-source, no restrictions.

# Cowork-Local v3.2 — Autonomous Multi-Agent Development Assistant

AI-powered system that generates complete, tested, production-ready Python CLI projects with zero human supervision. Built on LangGraph with DeepSeek V4 Pro planner and 3 specialized workers (OpenCode, OpenDesign, MCP) via sub-graph architecture. Runs locally on Fedora 43 with GPU acceleration.

## Results Summary

Six consecutive projects generated in a single iteration with FREE model, all tests passing:
webreq 34/34, logview 32/32, gitstat 48/48, tcpdump-cli 41/41, ai-reviewer 52/52, graph-report 34/34.

## Architecture

LangGraph with independent sub-graphs per worker. Planner uses DeepSeek V4 Pro to classify intent and route to the correct worker. Three specialized workers:

- **code_worker**: OpenCode + Flash FREE → generates Python projects with pytest validation
- **design_worker**: OpenDesign API → generates UI/UX, landing pages, dashboards, presentations
- **mcp_worker**: 5 local tools → filesystem (os.walk), document (pypdf/pandas), web (Playwright), shell (subprocess), chat (DeepSeek)

Redis provides chat history and planner caching. PostgreSQL persists sessions across 8 tables. Graphify maps the codebase for architectural awareness.

## Telegram Assistant

Autonomous assistant via Telegram (@byron92m_bot) with all 5 tools accessible through natural language. Multi-session support with /list, /switch, /nueva, /cerrar, /estado, /pc. Conversation memory via Redis. Intent classification via DeepSeek Pro. Security: Chat ID whitelist, --confirm for dangerous actions.

## Technical Stack

LangGraph with sub-graphs for agent orchestration. OpenCode CLI as code generation engine. OpenDesign for design workflows. DeepSeek API for cloud models. PostgreSQL + Redis for persistence. Playwright for web automation. 16 MCP servers. Ollama with qwen3:14b as local backup.

## Interfaces

Cowork Mode via python apps/cli/cowork_graph.py. Code Mode via opencode run. FastAPI REST API on port 8000. Telegram bot 24/7. VS Code via opencode-vscode.

## Infrastructure

Fedora 43. AMD Ryzen Starship Matisse. NVIDIA RTX 4060 Ti 16GB VRAM. 32GB RAM. NVMe 2TB + SSD 1TB. Docker for PostgreSQL, Redis, n8n.

## Monthly Cost

DeepSeek API approximately 0.50 dollars for intensive usage. All other components free and open-source. Hardware already owned. Total approximately 0.50 dollars per month.

## License

MIT. Open-source, no restrictions.

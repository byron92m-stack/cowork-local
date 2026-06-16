# Contributing to Cowork-Local v3.4.1

Multi-agent development assistant with DeepSeek V4 Pro planner and 5 specialized workers via LangGraph sub-graph architecture. 16 MCP Servers. PostgreSQL plus Redis. Mail.ru email integration. 158 Python files, production ready.

## Development Setup

git clone https://github.com/byron92m-stack/cowork-local.git
cd cowork-local
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker compose -f infra/docker-compose.yml up -d
ollama pull qwen3:14b
cp .env.example .env

## Prerequisites

Python 3.13 plus with venv. Node.js 22 plus with npm. Docker and Docker Compose. Ollama with qwen3:14b as backup worker. DeepSeek API key. Git. OpenCode CLI installed globally. Langcli installed locally (~/chat-colaborativo/).

## Architecture Guidelines

Adding a Worker Sub-Graph: Create graph/graph_new.py with build function returning compiled graph. Define state class in graph/state.py. Add wrapper function in graph/graph.py that invokes the sub-graph and maps results to CoworkState. Register worker node in build_graph and add routing in route_to_worker. For standalone workers (booking, accounting), use independent sub-graphs with their own public API (run_* function), invoked via CLI or Telegram.

Adding an MCP Server: Create tools/mcp/name/server.py. Implement call_tool. Register in tools/mcp_client.py. Add security rules to config/settings.yaml. Add to .mcp.json.

Adding a Tool to codewhale_worker: Add routing in graph/graph.py route_to_worker(). Add classification example in planner_system.txt. Add type to project_type list. Update COWORK.md.

Updating Graphify: Run graphify update . after significant code changes. Commit updated graphify-out/GRAPH_REPORT.md.

## Code Style

PEP 8. 4 spaces indentation. Max 100 chars per line. Type hints on public functions. Google-style docstrings. Spanish for conversation, English for code and documentation.

## Pull Request Process

Fork repo. Create feature branch. Make changes with clear commits. Update documentation. Submit PR.

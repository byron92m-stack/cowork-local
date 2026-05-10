# Contributing to Cowork-Local v3.1.1 (Unified)

Thanks for your interest in contributing to Cowork-Local v3.1.1. This version unifies Claude Code CLI as the single interface with two modes: Cowork (autonomous graph) and Code (generation). DeepSeek Cloud is the brain, LangGraph orchestrates 6 nodes with integrated tools, Qwen 3 14B on Ollama GPU is the executor, and 12 MCP Tools execute real operations.

## Development Environment Setup

git clone https://github.com/byron92m-stack/cowork-local.git
cd cowork-local
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker compose -f infra/docker-compose.yml up -d
ollama pull qwen3:14b
cp .env.example .env
npm install --prefix claude-code
./cowork check

## Prerequisites

Python 3.12+ with venv. Node.js 22+ with npm. Docker and Docker Compose. Ollama installed and running with qwen3:14b. DeepSeek API key from platform.deepseek.com. Git.

## Project Statistics

Claude Code CLI v2.1.138 with dual-mode unified interface. 6-node LangGraph (intake, planner, worker, validation, review, decision) with integrated tools (search, diffs, memory, skills). 12 MCP Servers. 7 PostgreSQL tables. 23+ advanced skills. Architecture: 1 Brain (DeepSeek) + 1 Executor (Qwen3) + 12 MCP Servers.

## Code Style

PEP 8 for Python. 4 spaces indentation. Max 100 chars per line. black and isort for formatting. Type hints on all public functions. Google-style docstrings.

## Architecture Guidelines

### Adding a New Graph Node
Add function to graph/graph.py. Register with workflow.add_node(). Add routing logic in conditional edges. Update state.py if new fields needed.

### Adding a New MCP Server
Create tools/mcp/name/ with server.py. Implement call_tool function. Register in tools/mcp_client.py. Add security rules to config/settings.yaml.

### Adding a New Skill
Add tool definition to tools/mcp/skills/server.py. Implement handler. Add package to requirements.txt. Update docs.

### Adding a New CLI Tool
Create script in apps/cli/. Integrate into LangGraph node if needed. Update CLAUDE.md with usage. Update documentation.

## Pull Request Process

Fork repo. Create feature branch. Make changes with clear commits. Run tests. Update documentation. Submit PR.

## Questions?
Open an issue or start a discussion.

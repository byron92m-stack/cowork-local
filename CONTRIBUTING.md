# Contributing to Cowork-Local v3.1 (Unified)

Thanks for your interest in contributing to Cowork-Local v3.1. This version unifies Claude Code CLI as the single interface with two modes: Cowork (autonomous graph) and Chat (DeepSeek conversation). DeepSeek Cloud is the brain, LangGraph orchestrates 6 nodes, Qwen 3 14B on Ollama GPU generates code, and 12 MCP Tools execute real operations.

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

Claude Code CLI v2.1.138 with dual-mode unified interface. 6-node LangGraph (intake, planner, worker, validation, review, decision). 12 MCP Servers (filesystem, shell, git, docker, browser, websearch, code_sandbox, docker_sandbox, filewatcher, gmail, googledrive, notion, skills). 7 PostgreSQL tables. 20+ advanced skills. 4 layers: Interface (Claude Code), Brain (DeepSeek), Orchestrator (LangGraph), Executor (Qwen3 + MCP).

## Code Style

PEP 8 for Python. 4 spaces indentation. Max 100 chars per line. black and isort for formatting. Type hints on all public functions. Google-style docstrings.

## Architecture Guidelines

### Adding a New Graph Node
Add function to graph/graph.py. Register with workflow.add_node(). Add routing logic in conditional edges. Update state.py if new fields needed.

### Adding a New MCP Server
Create tools/mcp/name/ with server.py. Implement call_tool function. Register in tools/mcp_client.py. Add security rules to config/settings.yaml.

### Adding a New Skill
Add tool definition to tools/mcp/skills/server.py. Implement handler. Add package to requirements.txt. Update docs.

### Adding a New execute_command Action
Add handler to apps/cli/execute_command.py. Available via "cowork execute" from CLI.

## Pull Request Process

Fork repo. Create feature branch. Make changes with clear commits. Run tests. Update documentation. Submit PR.

## Questions?
Open an issue or start a discussion.

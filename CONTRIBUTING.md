# Contributing to Cowork-Local v3.1.1

Thanks for your interest in contributing. Claude Code CLI as unified interface with two modes. DeepSeek Cloud brain. LangGraph orchestrates 6 nodes with integrated tools. Qwen 3 14B GPU executor. 14 MCP Servers. 23 Skills. 5 tests passing.

## Development Setup

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

Python 3.12 plus with venv. Node.js 22 plus with npm. Docker and Docker Compose. Ollama with qwen3:14b. DeepSeek API key. Git.

## Project Statistics

Claude Code CLI v2.1.138. 6-node LangGraph with integrated tools. 14 MCP Servers. 7 PostgreSQL tables. 23 plus Skills. 5 tests passing. Architecture: 1 Brain (DeepSeek) plus 1 Executor (Qwen3) plus 14 MCP Servers.

## Code Style

PEP 8. 4 spaces indentation. Max 100 chars per line. Type hints on public functions. Google-style docstrings.

## Architecture Guidelines

Adding a Graph Node: Add function to graph.py. Register with workflow.add_node. Update routing logic. Update state.py if needed.

Adding an MCP Server: Create tools/mcp/name/server.py. Implement call_tool. Register in tools/mcp_client.py. Add security rules to config/settings.yaml.

Adding a Skill: Add tool definition to tools/mcp/skills/server.py. Implement handler. Add package to requirements.txt. Update docs.

Adding a CLI Tool: Create script in apps/cli. Integrate into LangGraph node if needed. Update CLAUDE.md.

## Pull Request Process

Fork repo. Create feature branch. Make changes with clear commits. Run tests with pytest tests/ -v. Update documentation. Submit PR.

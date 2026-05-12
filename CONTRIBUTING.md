# Contributing to Cowork-Local v3.2

Multi-agent development assistant with DeepSeek V4 Pro planner and OpenCode Flash FREE worker. LangGraph 6-node orchestrator. 15 MCP Servers. PostgreSQL memory. 5 tests passing.

## Development Setup

git clone https://github.com/byron92m-stack/cowork-local.git
cd cowork-local
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker compose -f infra/docker-compose.yml up -d
ollama pull qwen3:14b
cp .env.example .env
npm install -g opencode-ai
./cowork check

## Prerequisites

Python 3.12 plus with venv. Node.js 22 plus with npm. Docker and Docker Compose. Ollama with qwen3:14b as backup worker. DeepSeek API key. Git. OpenCode CLI installed globally.

## Architecture Guidelines

Adding a Graph Node: Add function to graph/graph.py. Register with workflow.add_node. Update routing logic. Update state.py if needed.

Adding an MCP Server: Create tools/mcp/name/server.py. Implement call_tool. Register in tools/mcp_client.py. Add security rules to config/settings.yaml.

Adding a Skill: Add tool definition to tools/mcp/skills/server.py. Implement handler. Add package to requirements.txt. Update OPENCODE.md.

Adding a CLI Tool: Create script in apps/cli. Integrate into LangGraph node if needed. Update OPENCODE.md.

## Code Style

PEP 8. 4 spaces indentation. Max 100 chars per line. Type hints on public functions. Google-style docstrings.

## Pull Request Process

Fork repo. Create feature branch. Make changes with clear commits. Run tests with pytest tests/ -v. Update documentation. Submit PR.

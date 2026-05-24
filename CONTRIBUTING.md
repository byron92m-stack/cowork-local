# Contributing to Cowork-Local v3.2

Multi-agent development assistant with DeepSeek V4 Pro planner and OpenCode Flash FREE worker. LangGraph 5-node orchestrator. 16 MCP Servers. PostgreSQL memory. 6 projects 100% tests.

## Development Setup

git clone https://github.com/byron92m-stack/cowork-local.git
cd cowork-local
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker compose -f infra/docker-compose.yml up -d
ollama pull qwen3:14b
cp .env.example .env
npm install -g opencode-ai && opencode plugin opencode-vscode -g
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

Adding an n8n Workflow: Create JSON via Cowork (python apps/cli/cowork_graph.py "task"). Import via n8n API or UI on port 5678. Configure credentials in n8n UI. Activate toggle.

Adding a Tool: Add elif block in execute_mcp_tool() in graph/graph.py. Add classification example in PLANNER_SYSTEM. Add type to project_type list. Update OPENCODE.md tools section.

Updating Graphify: Run graphify update . after significant code changes. Commit updated graphify-out/GRAPH_REPORT.md. Planner reads it automatically.

## Pull Request Process

Fork repo. Create feature branch. Make changes with clear commits. Run tests with pytest tests/ -v. Update documentation. Submit PR.

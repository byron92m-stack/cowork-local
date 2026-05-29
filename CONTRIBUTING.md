# Contributing to Cowork-Local v3.2

Multi-agent development assistant with DeepSeek V4 Pro planner and 3 specialized workers via LangGraph sub-graph architecture. 16 MCP Servers. PostgreSQL plus Redis. 6 projects 100 percent tests.

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

Python 3.13 plus with venv. Node.js 22 plus with npm. Docker and Docker Compose. Ollama with qwen3:14b as backup worker. DeepSeek API key. Git. OpenCode CLI installed globally.

## Architecture Guidelines

Adding a Worker Sub-Graph: Create graph/graph_new.py with build function returning compiled graph. Define state class in graph/state.py. Add wrapper function in graph/graph.py that invokes the sub-graph and maps results to CoworkState. Register worker node in build_graph and add routing in route_to_worker.

Adding an MCP Server: Create tools/mcp/name/server.py. Implement call_tool. Register in tools/mcp_client.py. Add security rules to config/settings.yaml.

Adding a Tool to mcp_worker: Add elif block in execute_tool in graph/graph_mcp.py. Add classification example in PLANNER_SYSTEM. Add type to project_type list. Update OPENCODE.md.

Fixing PDF Processing: Ensure tool_document uses state.project_path as priority. Remove limits on pages (reader.pages not reader.pages[:5]). Remove limits on text (remove [:1000]). For long content, save to file and reference path.

Fixing Code Generation: Prompt must request JSON format. clean_code() must handle JSON responses, markdown blocks, and remove non-ASCII characters. Scripts must be saved AND executed automatically via subprocess.run.

Adding an n8n Workflow: Create JSON via Cowork. Import via n8n API or UI on port 5678. Configure credentials in n8n UI. Activate toggle.

Updating Graphify: Run graphify update . after significant code changes. Commit updated graphify-out/GRAPH_REPORT.md. Planner reads it automatically.

## Code Style

PEP 8. 4 spaces indentation. Max 100 chars per line. Type hints on public functions. Google-style docstrings.

## Pull Request Process

Fork repo. Create feature branch. Make changes with clear commits. Run tests with pytest tests/ -v. Update documentation. Submit PR.

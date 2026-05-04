# Contributing to Cowork-Local

Thanks for your interest in contributing to Cowork-Local.

## Development Environment Setup

git clone https://github.com/byron92m-stack/cowork-local.git
cd cowork-local
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker compose -f infra/docker-compose.yml up -d
ollama pull qwen3:14b
cp .env.example .env
./cowork check

## Prerequisites

- Python 3.12+ with venv
- Docker and Docker Compose
- Ollama installed and running
- DeepSeek API key (platform.deepseek.com)
- Git

## Project Statistics

- 80 files total, 56 Python files, 4,781 lines of code
- 12 MCP Servers (filesystem, shell, git, docker, browser, websearch, code_sandbox, docker_sandbox, filewatcher, gmail, googledrive, notion, skills)
- 5 LangGraph nodes (supervisor, executor, reviewer, tools_node, memory_manager)
- 7 PostgreSQL tables (sessions, steps, artifacts, tool_usage, errors, project_memory, scheduled_tasks)
- 10 Git commits, clean history

## Code Style

- Follow PEP 8
- Use 4 spaces for indentation
- Max line length: 100 characters
- Use black and isort for formatting
- All public functions must have type hints
- Google-style docstrings

## Architecture Guidelines

### Adding a New Agent Node
1. Create node function in graph/nodes/
2. Import and register in graph/graph.py
3. Update routing logic in conditional edges
4. Add Artifact types in state.py if needed

### Adding a New MCP Server
1. Create tools/mcp/name/ with __init__.py and server.py
2. Implement call_tool(tool_name, arguments) function
3. Register in tools/mcp_client.py in the server mapping
4. Add security rules to config/settings.yaml

### Adding a New Skill
1. Add tool definition to tools/mcp/skills/server.py
2. Implement handler function
3. Add package to requirements.txt
4. Update documentation

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make changes with clear commit messages
4. Run tests and ensure nothing is broken
5. Update documentation if needed
6. Submit pull request with clear description

## Questions?

Open an issue or start a discussion.

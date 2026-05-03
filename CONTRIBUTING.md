# Contributing to Cowork-Local

Thanks for your interest in contributing to Cowork-Local!

## Development Environment Setup

git clone https://github.com/YOUR_USERNAME/cowork-local.git
cd cowork-local
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker compose -f infra/docker-compose.yml up -d
ollama pull qwen2.5:14b
cp .env.example .env
./cowork check

## Prerequisites

- Python 3.12+ with venv
- Docker and Docker Compose
- Ollama installed and running
- DeepSeek API key (platform.deepseek.com)
- Git

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
1. Create tools/mcp/name/server.py with call_tool function
2. Register in tools/mcp_client.py
3. Add security rules to config/settings.yaml

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

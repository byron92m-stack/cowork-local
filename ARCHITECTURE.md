# Architecture

## Overview

Cowork-Local implements a multi-agent architecture using LangGraph as the orchestrator. Three specialized agents collaborate through a structured cycle: Memory → Plan → Execute → Review → Persist.

The system splits intelligence across two models for cost efficiency: DeepSeek Cloud handles high-level reasoning (planning and reviewing), while Qwen 2.5 14B runs locally on GPU for code generation and analysis — all for ~$0.50/month.

## System Architecture

The system has five main layers: Supervisor (plans), Executor (codes), Reviewer (evaluates), MCP Tools (filesystem, shell, git, docker, skills), and PostgreSQL (persistent memory). All orchestrated by LangGraph with four interfaces: CLI, REST API, Streamlit, and Swagger.

## Agentic Flow

The flow follows this sequence: MEMORY loads context from PostgreSQL, SUPERVISOR generates a JSON plan using DeepSeek Cloud, TOOLS execute system operations when needed, EXECUTOR runs code generation on Qwen 14B GPU, REVIEWER evaluates results with DeepSeek, and MEMORY persists everything back to PostgreSQL. The cycle repeats until all steps are complete.

## Nodes

### Supervisor (DeepSeek Cloud)
- Role: Strategic planner and quality reviewer
- Model: deepseek-chat via OpenAI-compatible API
- Client: models/deepseek_client.py
- System Prompt: Defined in config/models.yaml
- Responsibilities: Analyzes user queries, generates structured JSON plans, assigns steps to roles, reviews results, limits plans to 7 steps
- Temperature: 0.1 for deterministic planning
- JSON Mode: Enabled for structured outputs

### Executor (Qwen 2.5 14B - Local GPU)
- Role: Technical executor and code generator
- Model: qwen2.5:14b via Ollama (Q4_K_M quantization, 8.9 GB)
- Hardware: NVIDIA RTX 4060 Ti 16GB VRAM
- Client: models/qwen_ollama_client.py
- System Prompt: Defined in config/models.yaml
- Responsibilities: Analyzes code and architecture, generates code/diffs/patches, refactors modules, creates configurations and scripts, reports errors
- Temperature: 0.2 for precise code generation
- Context Window: 4096 tokens

### Reviewer (DeepSeek Cloud)
- Role: Quality assurance
- Model: deepseek-chat (same as Supervisor, different system prompt)
- Responsibilities: Evaluates execution results against original query, returns structured JSON with status/feedback/corrections, triggers re-execution if needed, decides when a step is complete

### Tools Node
- Role: System operations gateway
- Implementation: graph/nodes/tools_node.py
- Backend: 5 MCP (Model Context Protocol) servers
- Unified Client: tools/mcp_client.py
- Security: Whitelisted paths, whitelisted commands, read-only Git/Docker

### Memory Manager
- Role: Persistence layer
- Implementation: graph/nodes/memory_manager.py
- Backend: PostgreSQL with 6 tables
- Operations: Pre-run loads project memory and recent context, Post-run saves session/steps/artifacts/errors/tool usage

## State: CoworkState

Defined in graph/state.py. Central data contract flowing through all LangGraph nodes.

Fields:
- session_id: UUID
- user_query: str
- project_path: str
- max_iterations: int
- iteration_count: int
- plan: List of Step objects (each with id, description, status, assigned_to, step_type)
- artifacts: List of Artifact objects (each with id, type, path, content)
- current_step_id: UUID or None
- errors: List of strings
- metadata: Dict

Step statuses: pending -> in_progress -> done/failed
Step assignments: supervisor, executor, tools
Step types: analysis, code_generation, review, tool_call
Artifact types: file_diff, analysis, plan, log, code, error, review

## Graph Flow Details

1. START enters at MEMORY (pre-run)
2. MEMORY loads project_memory and recent sessions from PostgreSQL
3. If first run, goes to SUPERVISOR. If session already saved, goes to END
4. SUPERVISOR generates JSON plan with steps. If no pending steps, goes to MEMORY
5. ROUTING checks assigned_to field: tools goes to TOOLS, executor goes to EXECUTOR
6. TOOLS executes system operations via MCP
7. EXECUTOR generates/analyzes code via Qwen GPU
8. REVIEWER evaluates result. If needs correction, back to executor/tools. If done, continues
9. If more steps pending, back to SUPERVISOR. If all done, goes to MEMORY (post-run)
10. MEMORY persists everything to PostgreSQL
11. END delivers final result

## MCP Protocol

The Model Context Protocol (MCP) enables LLMs to interact with external tools through a standardized interface. Each server is independent with a call_tool(tool_name, arguments) function.

Unified client at tools/mcp_client.py:
- call_sync(server, tool, arguments) for synchronous calls
- call(server, tool, arguments) for async calls

Available servers:
- Filesystem: read_file, write_file, list_directory, search_files (path whitelist)
- Shell: execute_command (command whitelist + blocklist)
- Git: git_operation (read-only: status, diff, log, branch, show)
- Docker: docker_operation (read-only: ps, logs, inspect, stats, version)
- Skills: 10 advanced tools (PDF, Excel, PPTX, Charts, Email, Web, GitHub, GitLab, Slack)

## Database Schema

PostgreSQL provides persistent memory. Schema in infra/postgres_init.sql.

sessions: id, user_query, project_path, status, metadata, created_at, updated_at
steps: id, session_id, step_sequence, description, status, assigned_to, metadata
artifacts: id, session_id, step_id, type, path, content, metadata
tool_usage: id, session_id, step_id, tool_name, tool_input, tool_output, duration_ms
errors: id, session_id, step_id, error_message, error_type
project_memory: id, project_path (unique), summary, architecture_notes, key_decisions, last_analyzed

## Configuration

Two YAML files with environment variable support (${VAR:-default}):

config/settings.yaml: paths, database, providers, MCP servers, logging, security
config/models.yaml: model definitions, system prompts, generation parameters

## Security Model

- API keys: Never hardcoded, always via os.getenv()
- Filesystem MCP: Whitelisted paths only
- Shell MCP: Whitelisted commands, destructive commands blocked
- Git/Docker MCP: Read-only operations
- Write operations: Require user confirmation
- Sandbox mode: Available for maximum safety
- Database: No default passwords, POSTGRES_PASSWORD required

## Why Two Models?

DeepSeek Cloud (Supervisor/Reviewer): ~$0.50/month, 128K context, 0.1 temperature, strengths in reasoning and structure
Qwen 14B Local (Executor): $0 (your GPU), 4K context, 0.2 temperature, strengths in code expertise and speed

This hybrid approach maximizes quality while minimizing cost.

## Extensibility

Adding a new agent node:
1. Create function in graph/nodes/
2. Register in graph/graph.py
3. Update routing logic
4. Add Artifact types in state.py if needed

Adding a new MCP server:
1. Create tools/mcp/<name>/server.py
2. Implement call_tool(tool_name, arguments)
3. Register in tools/mcp_client.py
4. Add security rules to config/settings.yaml

Adding a new skill:
1. Add tool definition to tools/mcp/skills/server.py
2. Implement handler function
3. Add package to requirements.txt
4. Update documentation

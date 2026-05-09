# Cowork-Local Development Plan

## Completed Phases

### Phase 1: Core Agentic Architecture
LangGraph orchestration with 5 nodes. Supervisor (DeepSeek Cloud), Executor (Qwen 3 GPU), Reviewer (DeepSeek Cloud). Tools node with MCP integration, Memory Manager with PostgreSQL plus disk save.

### Phase 2: Qwen 3 14B Integration
Upgraded from Qwen 2.5 to Qwen 3 14B. Visible reasoning mode. Direct chat via ./cowork_chat.sh and ollama run qwen3:14b.

### Phase 3: 12 MCP Servers
Filesystem, Shell, Git, Docker, Browser, WebSearch, Code Sandbox, Docker Sandbox, File Watcher, Gmail, Google Drive, Notion, Skills (20+ tools).

### Phase 4: Docker VM Sandbox
Isolated code execution with no network. Read-only filesystem, resource limits. SELinux compatible for Fedora.

### Phase 5: SSE Streaming
Real-time token streaming via Server-Sent Events.

### Phase 6: File Watcher + Auto-Execution
Watchdog-based directory monitoring. Automatic agent triggering on file changes.

### Phase 7: Autonomous Code Generation
Executor calls Qwen 3 GPU for real code generation.

### Phase 8: Security
Prompt injection defenses. Tool argument validation. .env excluded from Git.

### Phase 9: PostgreSQL Persistence
7 tables: sessions, steps, artifacts, tool_usage, errors, project_memory, scheduled_tasks.

### Phase 10: Plugin System
YAML-based skill templates with versioning. Plugin manager with catalog.

### Phase 11: Knowledge Base
Document storage with metadata. Keyword-based search.

### Phase 12: Workspace Manager
Multi-project persistent workspaces.

### Phase 13: Scheduled Tasks
CRON-based recurring tasks in PostgreSQL.

### Phase 14: Documentation
README, ARCHITECTURE, CONTRIBUTING, SECURITY, COWORK_PLAN, MIT LICENSE.

### Phase 15: Claude Code CLI Integration (v3.0)
Claude Code CLI v2.1.138 installed as unified interface. Proxy translates Anthropic-format calls to DeepSeek API. MCP HTTP Server on port 8765. execute_command.py bridges Claude Code to MCP Tools. auto-build.sh autonomous loop. Weather-cli project generated without supervision (12 files).

### Phase 16: Unified Dual-Mode Interface (v3.1)
Claude Code CLI now supports two modes in one interface. Cowork mode (prefix "cowork:") triggers autonomous graph: intake, DeepSeek planner, Qwen3 worker, validation, DeepSeek review, loop decision. Chat mode (default) forwards to DeepSeek Cloud for conversation. 6-node LangGraph with DeepSeek JSON planning and Qwen3 GPU code generation. loop.sh provides clean output for CLI. execute_command.py supports stdin for multiline code.

## Current Capabilities (v3.1)

- Unified Claude Code CLI with two modes: cowork + chat
- Autonomous graph loop: plan, generate, validate, review, decide
- DeepSeek Cloud for planning and review (JSON mode)
- Qwen 3 14B GPU for real code generation (32 tokens/s)
- 6-node LangGraph with conditional routing
- 12 MCP Servers + 20+ Skills
- PostgreSQL persistence (7 tables)
- Plugin Marketplace, Knowledge Base, Workspace Manager
- Docker VM Sandbox, File Watcher
- 4 Interfaces (Claude Code CLI, Qwen Chat, REST API, Streamlit)
- Total cost: approximately 0.50 USD/month

## Comparison with Claude Cowork (60 USD/month)

Both have: multi-agent architecture, real-time streaming, sandbox execution, file watching, scheduled tasks, web search, email integration, knowledge base, plugin systems. Cowork-Local adds: open-source (MIT), multiplatform, local GPU models, unified dual-mode Claude Code CLI, autonomous 6-node graph loop, and runs for 0.50 USD/month.

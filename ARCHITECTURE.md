# Architecture — Cowork-Local v3.1 (Unified)

## Overview

Cowork-Local v3.1 implements a unified agentic architecture with Claude Code CLI as the single interface offering two modes: Cowork (autonomous graph execution) and Chat (conversational DeepSeek). DeepSeek Cloud is the brain, LangGraph orchestrates a 6-node graph, Qwen 3 14B on Ollama GPU generates code, and 12 MCP servers provide real file operations.

Total cost: approximately 0.50 USD per month (DeepSeek API only).

## Two Modes Unified

### Cowork Mode (prefix: "cowork:")
When the user types "cowork: task", the proxy intercepts the message before sending to DeepSeek. Instead, it calls apps/cli/loop.sh which executes the full LangGraph pipeline:

1. task_intake — receives the task
2. deepseek_planner — DeepSeek generates a JSON plan with concrete steps
3. qwen_worker — Qwen 3 14B GPU generates real Python code via Ollama
4. validation — pytest runs on generated code
5. supervisor_review — DeepSeek reviews results and errors
6. loop_decision — completes or repeats up to 3 iterations

The output is returned directly to Claude Code as clean code without logs.

### Chat Mode (default)
Any message not starting with "cowork:" is forwarded to DeepSeek Cloud through the proxy. The proxy translates between Anthropic format (Claude Code) and OpenAI format (DeepSeek). Responses maintain conversation memory across turns.

## How Claude Code Connects to DeepSeek via Proxy

Claude Code communicates exclusively with the Anthropic API format. DeepSeek uses OpenAI-compatible format. The Flask proxy on port 8080 bridges them.

Configuration: activate-unificado.sh sets ANTHROPIC_BASE_URL=http://localhost:8080 redirecting Claude Code to the proxy. ANTHROPIC_AUTH_TOKEN holds the DeepSeek API key.

Translation flow: Claude Code sends Anthropic-format request to proxy. Proxy extracts messages, rebuilds into DeepSeek format (model, messages, temperature), forwards to api.deepseek.com/v1/chat/completions. DeepSeek responds with choices[0].message.content. Proxy wraps it into Anthropic format (id, type, role, content array, model, stop_reason). Claude Code displays it natively.

## Autonomous Graph (graph.py)

6 nodes with conditional routing:

- task_intake: Receives and normalizes the task
- deepseek_planner: Calls DeepSeek with system prompt "Eres arquitecto de software. Solo respondes JSON válido." Gets structured plan with steps
- qwen_worker: Calls Ollama API (qwen3:14b) with the step description. Extracts both response and thinking fields. Saves generated code to output/
- validation: Runs pytest on generated files
- supervisor_review: DeepSeek evaluates results, returns JSON with complete: true/false
- loop_decision: Returns END if complete or max iterations reached, otherwise loops back to planner

## Components

### Claude Code CLI
Package: @anthropic-ai/claude-code v2.1.138. Location: claude-code/node_modules/. Communicates with proxy on localhost:8080.

### Proxy (claude-code/proxy.py)
Framework: Flask. Port: 8080. Dual mode: detects "cowork:" prefix to activate graph mode, otherwise forwards to DeepSeek for chat mode.

### LangGraph (graph/graph.py)
6 nodes as described above. Custom helpers: call_deepseek for DeepSeek API calls, call_qwen for Ollama API, execute_command for pytest validation.

### Loop Script (apps/cli/loop.sh)
Bash wrapper that calls cowork_graph.py, cleans output, shows only generated code and iteration count.

### execute_command.py (apps/cli/execute_command.py)
Accepts stdin for multiline content. Actions: write-file (path + stdin content), run-command, list-files, git-status, run-tests.

### Qwen 3 14B on Ollama
Model: qwen3:14b (Q4_K_M, 9.3 GB). Port: 11434. Generates code at ~32 tokens/s with visible reasoning. call_qwen extracts both response and thinking fields.

### DeepSeek Cloud
Model: deepseek-chat. 128K context. JSON mode for planning. Temperature 0.1 for deterministic outputs. Approximately 0.50 USD/month.

### MCP Servers (12 Total)
Filesystem, Shell, Git, Docker, Browser, WebSearch, Code Sandbox, Docker Sandbox, File Watcher, Gmail, Google Drive, Notion, Skills (20+).

### PostgreSQL (7 tables)
sessions, steps, artifacts, tool_usage, errors, project_memory, scheduled_tasks.

## Security Model

API keys via .env (gitignored). Proxy localhost-only. Filesystem MCP whitelisted paths. Shell MCP whitelisted commands. Git/Docker MCP read-only. Docker Sandbox no network, read-only, resource limits.

## Why This Architecture?

DeepSeek Cloud (Brain): 0.50 USD/month, 128K context, excellent reasoning.
Qwen 3 14B GPU (Worker): 0 USD, local code generation, 32 tokens/s.
LangGraph (Orchestrator): 0 USD, 6 nodes, conditional routing.
Claude Code CLI (Interface): 0 USD, unified with two modes.

This split maximizes quality while minimizing cost. Cloud for strategy. Local for execution. Graph for automation. Single interface for simplicity.

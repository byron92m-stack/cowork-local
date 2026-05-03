# Cowork-Local

## Agentic Development Assistant — Running Locally on Fedora 43

Cowork-Local is a fully autonomous AI-powered development assistant that plans, executes, reviews, and remembers — all running on your own hardware. It combines DeepSeek Cloud for reasoning with Qwen 2.5 14B running locally on GPU for code generation, orchestrated by LangGraph with persistent memory via PostgreSQL.

## System Architecture

The system has five layers: Supervisor (DeepSeek Cloud, plans), Executor (Qwen 14B GPU, codes), Reviewer (DeepSeek Cloud, evaluates), MCP Tools (Filesystem, Shell, Git, Docker, Skills), and PostgreSQL (persistent memory). All orchestrated by LangGraph with four interfaces: CLI, REST API, Streamlit Dashboard, and Swagger UI.

## Agentic Flow

User query flows through: MEMORY loads context from PostgreSQL, SUPERVISOR generates JSON plan with DeepSeek, TOOLS execute system operations when needed, EXECUTOR generates code on Qwen GPU, REVIEWER evaluates results with DeepSeek, MEMORY persists everything back to PostgreSQL. Cycle repeats until all steps complete.

## Key Features

- Multi-Agent Architecture: Supervisor plans, Executor codes, Reviewer evaluates
- Local GPU Execution: Qwen 2.5 14B on NVIDIA RTX 4060 Ti 16GB VRAM
- Real System Tools: Filesystem, Shell, Git, Docker via MCP protocol
- 14 Advanced Skills: PDF, Excel, PowerPoint, Charts, Email, Web Search, GitHub, Slack, GitLab, Notion
- Persistent Memory: PostgreSQL with 6 tables for sessions, steps, artifacts, tool usage, errors, project memory
- Multiple Interfaces: CLI, REST API with Swagger, Streamlit Chat with live progress, Streamlit Dashboard
- Ultra Low Cost: approximately 0.50 USD per month for DeepSeek API only
- 100 Percent Yours: No cloud dependencies, fully open-source, runs on your hardware

## Hardware and Infrastructure

- Operating System: Fedora 43
- CPU: AMD Ryzen (Starship/Matisse)
- GPU: NVIDIA RTX 4060 Ti 16GB VRAM
- RAM: 32 GB
- System Disk: NVMe 2TB (Btrfs)
- Project Disk: SSD 1TB (ext4)
- Local Model: Qwen 2.5 14B (Q4_K_M quantization, 8.9 GB)

## Monthly Costs

Hardware is 0 dollars already owned. DeepSeek API approximately 0.50 dollars for heavy usage. Qwen Local GPU is 0 dollars running on your GPU. Streamlit, FastAPI, PostgreSQL, and MCP Servers are all 0 dollars open-source. Total approximately 0.50 dollars per month.

## Project Structure

cowork-local directory contains:
- apps with api (FastAPI REST 6 endpoints), cli (check status run commands), and web with Streamlit Dashboard and Real-time Agentic Chat
- config with settings.yaml for global configuration and models.yaml for AI model settings
- graph with main LangGraph graph, CoworkState definition, and nodes for supervisor, executor, reviewer, tools_node, and memory_manager
- models with DeepSeek Cloud HTTP client and Ollama Qwen client
- tools with MCP servers for filesystem, shell, git, docker, and skills, plus unified MCP client and PostgreSQL helper functions
- infra with Docker Compose for PostgreSQL and database schema SQL with 6 tables
- data directories for generated files and execution logs
- requirements.txt, cowork executable script, and .env.example template

## PostgreSQL Schema

Six tables provide complete persistence:
- sessions: conversation and task registry with id, user_query, project_path, status, metadata, timestamps
- steps: plan steps with id, session_id, step_sequence, description, status, assigned_to, metadata
- artifacts: generated results with id, session_id, step_id, type, path, content, metadata
- tool_usage: audit trail with id, session_id, step_id, tool_name, tool_input, tool_output, duration_ms
- errors: debugging with id, session_id, step_id, error_message, error_type
- project_memory: cross-session context with id, project_path unique, summary, architecture_notes, key_decisions, last_analyzed

## MCP Servers and Tools

Five MCP servers provide system access:
- Filesystem: read_file, write_file, list_directory, search_files with whitelisted paths
- Shell: execute_command with whitelisted commands and destructive commands blocked
- Git: git_operation read-only for status, diff, log, branch, show
- Docker: docker_operation read-only for ps, logs, inspect, stats, version
- Skills: 10 advanced tools for PDF, Excel, PowerPoint, Charts, Email, Web Search, GitHub, GitLab, Slack, Data Analysis

## Advanced Skills

PDF Generator uses reportlab for formatted PDF files. Excel Generator uses openpyxl for formatted XLSX files. PowerPoint uses python-pptx for themed PPTX files. Charts uses matplotlib for bar, line, pie, and scatter PNG files. Data Analysis uses pandas for descriptive statistics. Email Sender uses yagmail for Gmail integration. Web Search uses ddgs for DuckDuckGo search. GitHub uses PyGithub for repos, issues, and code access. GitLab uses python-gitlab for repository access. Slack uses slack-sdk for channel messages.

## User Interfaces

CLI available via ./cowork run, check, status commands in terminal. Chat Realtime on port 8502 at localhost with live progress display. Dashboard on port 8501 at localhost as control panel. REST API on port 8000 at localhost with HTTP endpoints. Swagger UI on port 8000 at localhost/docs for interactive documentation.

## Python Packages

Key packages include: langgraph for agentic orchestration, pydantic for data validation, fastapi and uvicorn for REST API, streamlit for web UI, mcp for Model Context Protocol, openai for DeepSeek client, httpx for async HTTP, psycopg2 for PostgreSQL, reportlab for PDF, openpyxl for Excel, python-pptx for PowerPoint, matplotlib for charts, pandas for data analysis, yagmail for email, ddgs for web search, PyGithub for GitHub, slack-sdk for Slack, notion-client for Notion, python-gitlab for GitLab, google-api-python-client for Google APIs.

## Quick Start

Prerequisites: Python 3.12 plus with venv, Docker for PostgreSQL, Ollama with qwen2.5:14b pulled, DeepSeek API key from platform.deepseek.com.

Installation: git clone the repo, create and activate venv, pip install -r requirements.txt, ollama pull qwen2.5:14b, cp .env.example .env and edit with your keys, docker compose -f infra/docker-compose.yml up -d, run ./cowork check to verify.

Usage: ./cowork check verifies services, ./cowork status shows system state, ./cowork run --query "your task" executes a task. Streamlit Dashboard on port 8501. Real-time Chat on port 8502. REST API via python -m apps.api.main on port 8000, with Swagger UI at localhost:8000/docs.

## Key Achievements

Complete agentic system with DeepSeek plus Qwen GPU working together. Five MCP servers operational for Filesystem, Shell, Git, Docker, and Skills. Fourteen advanced skills including PDF, Excel, PowerPoint, Charts, Email, Web, GitHub. Real-time chat with step-by-step progress display. REST API with Swagger for external integrations. Web dashboard with statistics and monitoring. PostgreSQL with six tables for complete persistence. Plan to Execute to Review to Persist cycle fully functional. Open-source, fully yours, no cloud vendor lock-in. Total cost approximately 0.50 dollars per month for DeepSeek API only.

## License

MIT License. See LICENSE file for details.

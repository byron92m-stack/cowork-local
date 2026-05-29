# Architecture — Cowork-Local v3.2

## Overview

Multi-agent system with DeepSeek V4 Pro planner and 3 specialized workers via LangGraph sub-graph architecture. 6 real tools. 16 MCP Servers. PostgreSQL plus Redis. Telegram assistant 24/7. Playwright for web automation. Graphify for code intelligence. 6 projects 100 percent tests. Cost approximately 0.50 dollars per month.

## Multi-Agent Pipeline

Planner uses DeepSeek V4 Pro to classify user intent into 8 types: code_generation, tool_design, tool_filesystem, tool_document, tool_web, tool_edit, tool_shell, chat. Routes to the correct worker via conditional edges.

Three workers implemented as independent sub-graphs. code_worker uses OpenCode plus Flash FREE to generate Python projects with pytest. Now also generates and EXECUTES scripts automatically. Response format: JSON {"code": "script here"}. clean_code() handles JSON, markdown, and removes non-ASCII characters.

design_worker uses OpenDesign API to generate UI, UX, landing pages, and dashboards via port 34095.

mcp_worker runs 6 local tools: filesystem via os.walk, document via pypdf and pandas (uses state.project_path, extracts ALL pages and ALL text with no limits), web via Playwright, shell via subprocess, chat via OpenCode + Flash FREE, edit via OpenCode + Flash FREE.

Each worker has its own sub-graph with isolated state. CodeWorkerState for code generation, DesignWorkerState for design tasks. MCP worker shares CoworkState for chat history access.

Review evaluates completeness. If tests pass or tool completes, marks done. Decision routes to planner for retry or END. Saves conversation history to Redis. Maximum 5 iterations.

## PDF Processing (Updated)

tool_document now prioritizes state.project_path over searching in user_query. Extracts ALL pages (no limit of 5). Extracts ALL text (no limit of 1000 characters). For long content, save to file and reference path in prompt.

## Code Generation (Updated)

Prompt requests JSON format: {"code": "the complete Python script here"}. clean_code() extracts code from JSON or markdown blocks. Removes non-ASCII characters (em dash, smart quotes, accents). Script is saved AND executed automatically. Output captured in reply.

## Sub-Graph Architecture

Main graph in graph.py contains planner, review, and decision nodes. Three sub-graphs: graph_code.py with CodeWorkerState, graph_design.py with DesignWorkerState, graph_mcp.py with CoworkState. All state definitions in state.py.

## Telegram Assistant

API endpoint /chat/assistant receives messages from Telegram bot polling every 10 seconds. Multi-session via Redis with commands: /list, /switch, /nueva, /cerrar, /estado, /pc, /ayuda. Conversation history stored in Redis with 24 hour TTL. Security: Chat ID whitelist, confirm flag required for shell and web tools.

## Infrastructure

PostgreSQL with 8 tables for sessions, steps, artifacts, tool usage, errors, project memory, scheduled tasks, and invoices. Redis for chat history, graph state, planner cache, and session management. n8n on port 5678 with native MCP for workflow automation. Graphify maps the codebase into nodes and edges for architectural awareness. Playwright with Chromium headless in /browsers/ directory. 16 MCP servers in .mcp.json plus n8n-mcp plus postgresql.

## Security

API keys in .env excluded from git. Telegram token and API password in environment variables. Chat ID whitelist restricts access to authorized user only. Confirm flag required for shell and web tools. Rate limiting via Redis. MCP servers use whitelisted paths and read-only modes.

## Hardware

Fedora 43. AMD Ryzen Starship Matisse. NVIDIA RTX 4060 Ti 16GB VRAM. 32GB RAM. NVMe 2TB with Btrfs plus SSD 1TB with ext4. Docker for PostgreSQL, Redis, and n8n. Ollama serving qwen3:14b. Node.js v24.15.0.

## Monthly Cost

DeepSeek API approximately 0.50 dollars per month for intensive usage across all models. All other components free and open-source including LangGraph, OpenCode CLI, FastAPI, Streamlit, PostgreSQL, Docker, Ollama, and 16 MCP servers. Hardware already owned. Total approximately 0.50 dollars per month.

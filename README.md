# Cowork-Local v3.1.1 — Unified Agentic Development Assistant

## Running Locally on Fedora 43

Cowork-Local is a fully autonomous AI-powered development assistant that plans, executes, reviews, and remembers — all running on your own hardware. Version 3.1.1 unifies Claude Code CLI as the single interface with two modes: **Cowork mode** (autonomous graph execution) and **Code mode** (code generation).

## System Architecture (v3.1.1 — UNIFIED)

Five layers, one system:

- Interface: Claude Code CLI v2.1.138 — single input/output, conversation memory
- Brain: DeepSeek Cloud — strategic reasoning, code generation, review (128K context)
- Orchestrator: LangGraph with 6 nodes — task_intake → deepseek_planner → qwen_worker → validation → supervisor_review → loop_decision
- Worker: Qwen 3 14B on Ollama GPU — real code generation (32 tokens/s, visible reasoning)
- Tools: 12 MCP Servers — file operations, commands, Git, Docker, Skills

## Two Modes Unified in One CLI

### Cowork Mode (prefix: "cowork:")
Activa el grafo autónomo completo. DeepSeek genera un plan JSON, Qwen3 escribe el código en GPU, el sistema valida con pytest, DeepSeek revisa el resultado, y el loop decide si repetir o terminar. Sin supervisión humana.

Input: cowork: Crea una calculadora en Python
Output: Código funcional generado y validado

### Code Mode (default)
DeepSeek Cloud responde preguntas, explica conceptos, analiza código, sugiere mejoras. Generación de código con DeepSeek.

Input: qué es LangGraph?
Output: Explicación detallada con ejemplos

## Autonomous Loop (cowork_graph.py)

1. INTAKE recibe la tarea
2. PLANNER (DeepSeek) genera plan JSON con pasos concretos
3. WORKER (Qwen3 GPU) genera código real
4. VALIDATION ejecuta pytest
5. REVIEW (DeepSeek) evalúa resultado
6. DECISION completa o repite el loop

Máximo 3 iteraciones por defecto. Configurable con COWORK_MAX_ITER.

## Key Features

- Unified Claude Code CLI with two modes: cowork + code
- Autonomous graph loop: plan → generate → validate → review → decide
- DeepSeek Cloud Brain: 128K context, JSON planning, quality review
- Qwen 3 14B on Ollama GPU: local code generation at 32 tokens/s
- LangGraph Orchestrator: 6 nodes with conditional routing
- 12 MCP Servers: Filesystem, Shell, Git, Docker, Browser, WebSearch, Code Sandbox, Docker Sandbox, File Watcher, Gmail, Google Drive, Notion, Skills
- 23+ Advanced Skills: PDF, Excel, PowerPoint, Charts, Email, Web Search, GitHub, Slack, GitLab, Notion, Test Generator (Qwen3), Code Review (Qwen3), Doc Generator (Qwen3)
- PostgreSQL Memory: 7 tables for complete persistence
- Multiple Interfaces: Claude Code CLI, cowork CLI, REST API, Streamlit Web UI, Swagger docs
- Docker VM Sandbox: Secure isolated execution
- File Watcher: Auto-trigger on changes
- Prompt Injection Defenses
- Plugin Marketplace: YAML templates

## Hardware and Infrastructure

- OS: Fedora 43
- CPU: AMD Ryzen (Starship/Matisse)
- GPU: NVIDIA RTX 4060 Ti 16GB VRAM
- RAM: 32 GB
- System Disk: NVMe 2TB (Btrfs)
- Project Disk: SSD 1TB (ext4) at /media/SSD1T/
- Local Model: Qwen 3 14B (Q4_K_M, 9.3 GB) via Ollama on port 11434

## Monthly Costs

DeepSeek API: approximately 0.50 dollars per month. Everything else: 0 dollars. Total: approximately 0.50 dollars per month.

## Project Structure

- claude-code/ — Claude Code CLI v2.1.138 with proxy
- apps/ — API (FastAPI), CLI (cowork_graph.py, loop.sh, execute_command.py), Web UI (Streamlit)
- graph/ — LangGraph orchestrator with 6 nodes
- tools/ — 12 MCP servers, unified client, PostgreSQL helpers
- models/ — DeepSeek Cloud client, Qwen Ollama client
- config/ — settings.yaml, models.yaml
- infra/ — Docker Compose for PostgreSQL
- output/ — Generated code and projects

## Quick Start

Prerequisites: Python 3.12+, Node.js 22+, Docker, Ollama with qwen3:14b, DeepSeek API key

Commands:
  cd /media/SSD1T/cowork-local
  source ./activate-unificado.sh
  claude-code/node_modules/.bin/claude --model deepseek-chat

Modo Cowork:
  cowork: Crea una calculadora en Python

Modo Chat:
  Explicame qué es LangGraph

Terminal directo:
  ./apps/cli/loop.sh "Crea un conversor de monedas"

## Key Achievements (v3.1.1)

- Unified Claude Code CLI with two integrated modes
- Autonomous graph: DeepSeek plans, Qwen3 generates, system validates
- 6-node LangGraph with loop decision
- 12 MCP servers operational
- 23+ advanced skills
- PostgreSQL with 7 tables
- Docker VM sandbox
- File watcher with auto-execution
- REST API with SSE streaming + Swagger
- Open-source (MIT), no cloud vendor lock-in
- Total cost: approximately 0.50 dollars per month

## License

MIT License. See LICENSE file for details.

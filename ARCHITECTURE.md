# Architecture — Cowork-Local v3.2

## Overview

Multi-agent system with DeepSeek V4 Pro planner and OpenCode worker using DeepSeek V4 Flash FREE for code generation. LangGraph orchestrator with 6 nodes. 15 MCP Servers. PostgreSQL memory with 7 tables. File Watcher with auto-execution. VS Code extension. Gmail, Telegram, Calendar integrations. 5 tests passing. Cost approximately 0.50 dollars per month.

## Multi-Agent Pipeline

Planner node uses DeepSeek V4 Pro to generate a structured JSON plan from natural language input. Extracts project name, flags with defaults, and project description. Generates step-by-step task list for the worker.

Worker node executes via OpenCode CLI with DeepSeek V4 Flash FREE model. OpenCode generates all project files simultaneously including source code, tests, README, and pyproject.toml. Files are written directly to the project directory. Auto-install via pip install and auto-tests via pytest run immediately after file creation. On subsequent iterations, worker switches to surgical fix mode and only regenerates files with errors.

Validation node collects test results from pytest output. Counts passed and failed tests. Stores results as artifacts for review.

Review node evaluates test results and completeness. If all tests pass and project meets requirements, marks complete. Otherwise flags issues for replanning.

Decision node checks completion status. If complete with zero failing tests, ends execution. If maximum iterations reached, ends with warning. Otherwise routes back to planner for another attempt with accumulated error context.

Maximum 4 iterations configured. All recent projects completed in 1 iteration.

## Models

Planner and Reviewer use deepseek/deepseek-v4-pro via DeepSeek API with response_format json_object for structured outputs. One call each per iteration at approximately 0.001 dollars per call. Worker uses opencode/deepseek-v4-flash-free via OpenCode CLI with unlimited free generation. Local backup model qwen3:14b Q4_K_M at 9.3 GB available via Ollama on port 11434.

## LangGraph Nodes

Six nodes with conditional routing. Intake receives task and initializes state. Planner calls DeepSeek Pro for JSON plan. Worker calls OpenCode with Flash FREE for file generation. Validation processes pytest output. Review evaluates completeness. Decision routes to planner or END based on completion and iteration count.

## CLI Tools

cowork_graph.py executes the full multi-agent graph via python apps/cli/cowork_graph.py. loop.sh provides simplified wrapper with formatted output. execute_command.py handles file writes via stdin and JSON, plus run-command, list-files, git-status, and run-tests. search_tools.py provides grep search, file pattern matching, and module listing. apply_diff.py provides safe text replacement by line and by string. session_memory.py provides PostgreSQL save and load with configurable history depth. tool_caller.py detects and executes tool calls in 5 formats with 90 percent reliability. auto_watcher.py monitors file changes and triggers graph execution automatically.

## MCP Servers

15 servers operational. Filesystem for read, write, list, and search with path restrictions. Shell for command execution with whitelist. Git for status, diff, log, and branch in read-only mode. Docker for ps, logs, inspect, and stats in read-only mode. Browser for navigate, click, fill, screenshot, and extract in headless mode. WebSearch for DuckDuckGo search and page fetch. Code Sandbox for subprocess execution. Docker Sandbox for isolated execution without network. File Watcher using Watchdog for directory monitoring with auto-execution. Gmail for send and read via OAuth. Google Drive for list, upload, and download via API key. Notion for pages and databases via API token. Calendar for event creation via email invitations. Telegram for send and read via bot. Skills with 23 plus tools including PDF generation via reportlab, Excel via openpyxl, PowerPoint via python-pptx, charts via matplotlib, data analysis via pandas, email via yagmail, web search via ddgs, GitHub via PyGithub, GitLab via python-gitlab, and Slack via slack-sdk.

## PostgreSQL

Seven tables for complete persistence. sessions table records each conversation with user query, project path, status, timestamps, iteration count, and metadata. steps table tracks each plan step with description, type, assigned agent, status, and timestamps. artifacts table stores generated content including code, plans, reviews, test results, and documentation with type, content, and file path. tool_usage table logs every tool invocation with tool name, arguments, results, session reference, and timestamps. errors table records errors with type, description, step reference, and timestamps. project_memory table provides persistent context across sessions with key-value storage per project. scheduled_tasks table manages CRON-configured recurring tasks.

## Integrations

Gmail via dedicated bot account with OAuth for reading and sending emails. Telegram via at byron92m_bot for sending notifications and reading commands. Google Calendar via email invitations using ICS files for event creation. File Watcher using Watchdog library that detects changes in monitored directories and triggers graph execution automatically. VS Code extension with WebView chat panel and contextual commands bound to Ctrl+Shift+C for chat, Ctrl+Shift+E for explain, and Ctrl+Shift+O for optimize.

## Interfaces

OpenCode CLI v1.14.48 as primary interface with two modes. Cowork Mode executes full graph via python apps/cli/cowork_graph.py. Code Mode executes direct generation via opencode run. FastAPI REST API on port 8000 with SSE streaming and Swagger UI. Streamlit web dashboard on port 8501. VS Code extension with chat panel and contextual commands. Direct chat with local Qwen model via cowork_chat.sh.

## Security

API keys stored in dotenv file excluded from git. MCP servers use whitelisted paths and commands. Git and Docker servers operate in read-only mode. Docker Sandbox runs without network access and with CPU and memory limits. Prompt injection defenses on all user inputs. Input sanitization on shell commands.

## Hardware

Fedora 43 operating system. AMD Ryzen Starship Matisse processor. NVIDIA RTX 4060 Ti with 16GB VRAM. 32GB system RAM. NVMe 2TB system disk with Btrfs. SSD 1TB project disk with ext4 at /media/SSD1T. Docker for PostgreSQL and sandbox containers. Ollama serving qwen3:14b on port 11434.

## Project Structure

apps directory contains FastAPI REST API with SSE streaming, CLI command center with cowork_graph.py and loop.sh, and Streamlit web dashboard. graph directory contains LangGraph orchestrator with state management and six nodes. tools directory contains 15 MCP servers, unified client, PostgreSQL helpers, scheduler, security module, knowledge base, workspace manager, heartbeat monitor, auto-executor, and notifier. models directory contains DeepSeek cloud client and Qwen Ollama client. config directory contains settings.yaml and models.yaml. infra directory contains Docker Compose for PostgreSQL with initialization SQL. tests directory contains 5 tests currently passing. output directory stores generated projects. plugins directory contains skill marketplace with YAML templates and plugin manager.

## Monthly Cost

DeepSeek API approximately 0.50 dollars for intensive usage across all models. All other components free and open-source including LangGraph, OpenCode CLI, FastAPI, Streamlit, PostgreSQL, Docker, Ollama, and 15 MCP servers. Hardware already owned. Total approximately 0.50 dollars per month.

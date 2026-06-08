# Architecture — Cowork-Local v3.4.1

## Overview

Multi-agent system with DeepSeek V4 Pro planner and 4 specialized workers via LangGraph sub-graph architecture. 7 real tools + booking agency. 16 MCP Servers. PostgreSQL plus Redis. Telegram assistant 24/7. Playwright for web automation. Graphify for code intelligence. 6 projects 100 percent tests. Cost approximately 0.50 dollars per month. Booking worker adds ~0.30/month per 1000 appointments.

## Multi-Agent Pipeline

Planner uses DeepSeek Reasoner (Pro) to classify user intent into 9 types: code_generation, tool_design, tool_filesystem, tool_document, tool_web, tool_edit, tool_shell, booking, chat. Routes to the correct worker via conditional edges.

Four workers implemented as independent sub-graphs. code_worker uses OpenCode CLI with opencode/deepseek-v4-flash to generate Python projects with pytest. Now also generates and EXECUTES scripts automatically. Response format: JSON {"code": "script here"}. clean_code() handles JSON, markdown, and removes non-ASCII characters.

design_worker uses OpenDesign API to generate UI, UX, landing pages, and dashboards via port 34095.

mail_worker uses Mail.ru SMTP (port 465 SSL) and IMAP (port 993 SSL) to send/receive emails. Tools: mail_send, mail_read, calendar_add (ICS invitations). Auth via app password with 2FA. Config in .env: MAIL_USER, MAIL_PASSWORD, MAIL_SMTP_HOST, MAIL_SMTP_PORT, MAIL_IMAP_HOST, MAIL_IMAP_PORT.


booking_worker uses LangGraph state machine for medical appointment booking via Telegram and Email. Patient identification by cédula/RUC/passport with validation algorithm. Flow: ID → name+email → intent classification (deepseek-chat Flash API with JSON mode) → date (dateparser + Flash confirmation) → time (regex extraction) → confirm. Saves to PostgreSQL (patients, appointments, availability, email_queue, faqs, appointment_history tables). Redis session state keyed by doc_id with 2h TTL. ICS calendar invitations via email queue respecting Mail.ru 1/min rate limit. 24h reminders via APScheduler (Telegram for Telegram users, Email for email users). Security: rate limiting (15 msg/min Telegram, 3/hr email), input sanitization, prompt injection defense. BookingState with channel, user_id, doc_id, step, intent, selected_date, selected_slot.

mcp_worker runs 7 local tools: filesystem via os.walk, document via pypdf and pandas (uses state.project_path, extracts ALL pages and ALL text with no limits), web via Playwright, shell via subprocess, edit via OpenCode (opencode/deepseek-v4-flash, path traversal protected), chat disabled (use codewhale-tui), mail via Mail.ru SMTP/IMAP with app password.

Each worker has its own sub-graph with isolated state. CodeWorkerState for code generation, DesignWorkerState for design tasks. MCP worker shares CoworkState for chat history access.

Review evaluates completeness. If tests pass or tool completes, marks done. Decision routes to planner for retry or END. Saves conversation history to Redis. Maximum 5 iterations.

## PDF Processing (Updated)

tool_document now prioritizes state.project_path over searching in user_query. Extracts ALL pages (no limit of 5). Extracts ALL text (no limit of 1000 characters). For long content, save to file and reference path in prompt.

## Code Generation (Updated)

Prompt requests JSON format: {"code": "the complete Python script here"}. clean_code() extracts code from JSON or markdown blocks. Removes non-ASCII characters (em dash, smart quotes, accents). Script is saved AND executed automatically. Output captured in reply.

## Sub-Graph Architecture

Main graph in graph.py contains planner, review, and decision nodes. Four sub-graphs: graph_code.py with CodeWorkerState, graph_design.py with DesignWorkerState, graph_mcp.py with CoworkState. graph_booking.py with BookingState. All state definitions in state.py.

## Telegram Assistant

API endpoint /chat/assistant receives messages from Telegram bot polling every 10 seconds. Booking bot (@byron92m_bot) with commands: /start, /citas, /cancelar, /ayuda, /reset. Multi-session via Redis keyed by doc_id (2h TTL). Legacy Cowork commands: /list, /switch, /nueva, /cerrar, /estado, /pc. Security: rate limiting (15 msg/min), input sanitization, prompt injection defense. 24h reminders via APScheduler.

## Infrastructure

PostgreSQL with 8 Cowork tables (sessions, steps, artifacts, tool usage, errors, project memory, scheduled tasks, invoices) plus 6 booking tables (patients, appointments, availability, email_queue, faqs, appointment_history). Redis for chat history, graph state, planner cache, and session management. n8n on port 5678 with native MCP for workflow automation. Graphify maps the codebase into nodes and edges for architectural awareness. Playwright with Chromium headless in /browsers/ directory. 16 MCP servers in .mcp.json plus n8n-mcp plus postgresql. APScheduler for 24h appointment reminders and email queue processing.

## Security (v3.4.1)

API keys in .env excluded from git. Shell injection fixed (shlex.split + shell=False). Path traversal protected (os.path.realpath). DB credentials as separate parameters. Webhook n8n token auth support. Redis shared connection pool. Specific exception handling (no bare except). Hardcoded paths replaced with dynamic detection. Telegram token and API password in environment variables. Chat ID open for patient bookings. doc_id (cédula) as universal patient key across Telegram and Email channels. Confirm flag required for shell and web tools. Rate limiting via Redis. MCP servers use whitelisted paths and read-only modes.

## Hardware

Fedora 43. AMD Ryzen Starship Matisse. NVIDIA RTX 4060 Ti 16GB VRAM. 32GB RAM. NVMe 2TB with Btrfs plus SSD 1TB with ext4. Docker for PostgreSQL, Redis, and n8n. Ollama serving qwen3:14b. Node.js v24.15.0.

## Monthly Cost

DeepSeek API approximately 0.50 dollars per month for intensive usage across all models. All other components free and open-source including LangGraph, OpenCode CLI, FastAPI, Streamlit, PostgreSQL, Docker, Ollama, and 16 MCP servers. Hardware already owned. Total approximately 0.50 dollars per month. Booking agency adds ~0.30 dollars per 1000 appointments (DeepSeek Flash API for intent classification and conversation).

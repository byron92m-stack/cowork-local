# Cowork-Local v3.2

Asistente de desarrollo local multi-agente con 3 workers especializados corriendo sobre LangGraph.
Planner usa DeepSeek V4 Pro. Los 3 workers usan modelos gratuitos.
Costo total: ~$0.50/mes.

## Arquitectura

planner (DeepSeek Pro) -> clasifica intencion -> route_to_worker
  - code_worker -> graph_code.py -> OpenCode + Flash FREE -> proyectos Python, scripts, PowerPoints
  - design_worker -> graph_design.py -> OpenDesign API (puerto 34095) -> UI/UX, landing pages
  - mcp_worker -> graph_mcp.py -> 6 tools locales -> filesystem, document, web, shell, chat, edit

## Workers

### code_worker
- Genera y EJECUTA codigo Python automaticamente
- Formato de respuesta: JSON {"code": "script here"}
- clean_code() maneja JSON, markdown y caracteres no ASCII
- Proyectos con tests (pytest) cuando corresponde

### design_worker
- OpenDesign daemon en puerto 34095
- Genera web prototypes, landing pages, UI/UX
- Healthcheck antes de llamar

### mcp_worker
- filesystem: busqueda de archivos con os.walk
- document: lectura de PDF, Excel, CSV, TXT (usa state.project_path)
- web: navegacion con Playwright
- shell: ejecucion de comandos con --confirm
- chat: conversacion con memoria Redis
- edit: edicion de archivos via OpenCode

## PDF Processing (Importante)
- Usar parametro project_path, no incluir ruta en query string
- Extrae TODAS las paginas (sin limite de 5)
- Extrae TODO el texto (sin limite de 1000 caracteres)
- Para contenido largo: guardar en archivo y referenciar ruta

## Code Generation
- El prompt debe pedir JSON: {"code": "script here"}
- clean_code() extrae codigo de JSON o markdown
- Elimina caracteres no ASCII (em dash, smart quotes, acentos)
- El script se guarda y EJECUTA automaticamente

## Instalacion

cd /media/SSD1T/cowork-local
source venv/bin/activate
pip install -r requirements.txt

## Servicios Requeridos

PostgreSQL: cowork:coworkpass@127.0.0.1:5432/coworkdb
Redis: localhost:6379
OpenDesign daemon: http://127.0.0.1:34095

## Comandos Principales

Activar entorno:
cd /media/SSD1T/cowork-local && source venv/bin/activate

Iniciar API:
cd api-chat && python server.py &

Iniciar bot Telegram:
python api-chat/telegram_bot.py

Iniciar OpenDesign daemon:
cd /media/SSD1T/open-design && pnpm tools-dev run web --daemon-port 34095 --web-port 45125 &

Usar Cowork:
python apps/cli/cowork_graph.py "Creá un CLI con --name flag"

Limpiar cache Redis:
python3 -c "import redis; r=redis.Redis(host='localhost',port=6377); r.flushall()"

## Telegram Assistant

Bot: @byron92m_bot
Chat ID autorizado: 8047752200
Comandos: /list, /switch, /nueva, /cerrar, /estado, /pc, /ayuda
Memoria: Redis con TTL 24h por chat_id
Seguridad: whitelist Chat ID, --confirm para shell/web

## Capacidades

7 tipos de intencion:
- code_generation -> code_worker
- tool_design -> design_worker
- tool_filesystem, tool_document, tool_web, tool_shell, chat -> mcp_worker

6 proyectos con 100% tests: webreq, logview, gitstat, tcpdump-cli, ai-reviewer, graph-report

## Estructura del Proyecto

cowork-local/
  api-chat/              FastAPI + Telegram bot
  graph/                 LangGraph (3 sub-grafos)
  apps/cli/              CLI tools
  tools/mcp/             16 MCP servers
  infra/                 Docker Compose
  agents/                Sub-agentes
  rules/                 Reglas
  output/archive/        Proyectos generados
  venv/                  Python 3.13

## Reglas

- Generar codigo, no explicar
- Usar rutas absolutas
- No modificar archivos sin permiso
- Ver rules/api.md y rules/security.md

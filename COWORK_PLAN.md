# Cowork-Local → Claude Cowork Parity Plan

## Fase 1: Ejecución Paralela de Sub-agentes
- Modificar graph/graph.py para usar Send() API de LangGraph
- Permitir que el Supervisor spawnee múltiples Executors simultáneos
- Sincronizar resultados con reducer en CoworkState

## Fase 2: Browser MCP Server
- Crear tools/mcp/browser/server.py con Playwright
- Soporte para navegación, clicks, formularios, screenshots
- Modo headless para CI/CD

## Fase 3: Scheduled Tasks
- Agregar Redis a docker-compose.yml
- Implementar scheduler con APScheduler o Celery
- CRON integrado con PostgreSQL para persistencia

## Fase 4: Enterprise Connectors
- Google Drive MCP (listar, leer, escribir, compartir)
- Gmail MCP (leer, enviar, buscar emails)
- Salesforce MCP (consultas SOQL, objetos CRUD)

## Fase 5: Plugin System Portable
- Estandarizar skills como paquetes YAML+Markdown
- Sistema de versionado y distribución
- Marketplace local con catálogo de plugins

## Fase 6: Seguridad Enterprise
- Autenticación OAuth/SSO para API
- Prompt injection defenses
- Audit logs exportables (OTLP/OpenTelemetry)

## Fase 7: Workspace Persistente
- UI para gestionar múltiples proyectos
- Chat persistente entre sesiones
- Slash commands (/analyze, /generate, /deploy)

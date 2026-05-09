#!/bin/bash
COWORK_DIR="/media/SSD1T/cowork-local"
echo "🐄 Activando Cowork-Local Unificado..."
source "$COWORK_DIR/venv/bin/activate"

if ! curl -s http://localhost:8765/health > /dev/null 2>&1; then
    echo "🔧 Iniciando MCP HTTP Server..."
    python "$COWORK_DIR/apps/mcp_http_server.py" &
    sleep 2
fi

if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "🔄 Iniciando Proxy DeepSeek..."
    python "$COWORK_DIR/claude-code/proxy.py" &
    sleep 2
fi

export ANTHROPIC_BASE_URL="http://localhost:8080"
export ANTHROPIC_AUTH_TOKEN="sk-122139651350414899e1617d190c94f3"
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
export CLAUDE="$COWORK_DIR/claude-code/node_modules/.bin/claude"
export PATH="$COWORK_DIR/claude-code/node_modules/.bin:$PATH"

echo "✅ Cowork-Local Unificado listo"
echo "   Claude Code: $COWORK_DIR/claude-code/node_modules/.bin/claude --model deepseek-chat"

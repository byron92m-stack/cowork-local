#!/bin/bash
COWORK_DIR="/media/SSD1T/cowork-local"
echo "Cowork-Local v3.1.1 (OpenCode Edition)"
source "$COWORK_DIR/venv/bin/activate"
if ! curl -s http://localhost:8765/health > /dev/null 2>&1; then
    python "$COWORK_DIR/apps/mcp_http_server.py" &
    sleep 2
fi
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY}"
echo "MODO CODE: opencode run 'prompt'"
echo "MODO COWORK: ./apps/cli/loop.sh 'tarea'"

#!/bin/bash
# ============================================
# CLAUDE CODE CLI → Proxy Local → DeepSeek
# ============================================
export ANTHROPIC_BASE_URL="http://localhost:8080"
export ANTHROPIC_AUTH_TOKEN="sk-122139651350414899e1617d190c94f3"
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
echo "🦾 Claude Code activado (DeepSeek vía proxy local)"

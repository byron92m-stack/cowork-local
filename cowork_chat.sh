#!/bin/bash
echo "🐄 Cowork Chat - Qwen 3 14B"
while true; do
    read -p "🧑 Tú: " query
    [[ "$query" == "salir" ]] && break
    echo "🤖 Qwen 3:"
    ollama run qwen3:14b "$query" 2>/dev/null
    echo ""
done

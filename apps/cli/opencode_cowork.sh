#!/bin/bash
# Wrapper para OpenCode con OPENCODE.md como contexto
QUERY="$1"
OPENCODE_MD="/media/SSD1T/cowork-local/OPENCODE.md"

if [ -f "$OPENCODE_MD" ]; then
    CONTEXT=$(cat "$OPENCODE_MD")
    opencode run --prompt "$CONTEXT\n\nTarea: $QUERY"
else
    opencode run "$QUERY"
fi

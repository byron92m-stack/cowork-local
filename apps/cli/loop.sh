#!/bin/bash
QUERY="$*"
MAX="${COWORK_MAX_ITER:-3}"
OUTPUT_DIR="/media/SSD1T/cowork-local/output"

echo "🚀 $QUERY"

for i in $(seq 1 $MAX); do
    python /media/SSD1T/cowork-local/apps/cli/cowork_graph.py "$QUERY" 2>/dev/null > /tmp/cowork_output.txt
    
    # Buscar el archivo más reciente en output/
    ARCHIVO=$(ls -t "$OUTPUT_DIR"/gen_*.py 2>/dev/null | head -1)
    
    if [ -f "$ARCHIVO" ] && [ -s "$ARCHIVO" ]; then
        echo "✅ Generado ($(wc -c < "$ARCHIVO") chars)"
        echo ""
        cat "$ARCHIVO"
        echo ""
        echo "🏁 Fin"
        exit 0
    fi
done

echo "🏁 Fin (máx $MAX iteraciones)"

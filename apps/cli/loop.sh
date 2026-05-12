#!/bin/bash
QUERY="$*"
OUTPUT_DIR="/media/SSD1T/cowork-local/output"

echo "🚀 $QUERY"

# Ejecutar grafo y capturar output
python /media/SSD1T/cowork-local/apps/cli/cowork_graph.py "$QUERY" 2>/dev/null > /tmp/cowork_output.txt

# Buscar archivos creados recientemente
ARCHIVOS=$(find "$OUTPUT_DIR" -type f -name "*.py" -mmin -2 | head -5)

if [ -n "$ARCHIVOS" ]; then
    echo "✅ Archivos creados:"
    echo "$ARCHIVOS" | while read f; do
        echo "   📁 $f ($(wc -c < "$f") bytes)"
    done
    
    # Mostrar el primer archivo .py
    PRIMERO=$(echo "$ARCHIVOS" | head -1)
    if [ -f "$PRIMERO" ]; then
        echo ""
        cat "$PRIMERO"
    fi
else
    # Fallback: mostrar output del grafo
    grep "WORKER\|archivos\|Tests" /tmp/cowork_output.txt
fi

echo ""
echo "🏁 Fin"

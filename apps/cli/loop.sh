#!/bin/bash
QUERY="$*"
COWORK_DIR="/media/SSD1T/cowork-local"

echo "🚀 $QUERY"
echo ""

# Ejecutar grafo y capturar logs
python "$COWORK_DIR/apps/cli/cowork_graph.py" "$QUERY" 2>/tmp/cowork_log.txt > /tmp/cowork_result.txt

# Extraer project_name del log
PROJECT=$(grep "project=" /tmp/cowork_log.txt | tail -1 | sed 's/.*project=//' | cut -d, -f1 | tr -d ' ')
OUTPUT_DIR="$COWORK_DIR/output/$PROJECT"

if [ -n "$PROJECT" ] && [ -d "$OUTPUT_DIR" ]; then
    echo "📁 $PROJECT/"
    find "$OUTPUT_DIR" -type f | sort | while read f; do
        size=$(wc -c < "$f")
        rel="${f#$OUTPUT_DIR/}"
        echo "   📄 $rel ($size bytes)"
    done
    echo ""
    
    cd "$OUTPUT_DIR"
    pip install -e . 2>&1 | tail -1
    python -m pytest tests/ -v 2>&1 | tail -20
    echo ""
    echo "✅ $PROJECT listo"
else
    echo "❌ Proyecto no encontrado"
    cat /tmp/cowork_log.txt | grep -E "SAVED|ERROR|FAILED|PASSED"
fi

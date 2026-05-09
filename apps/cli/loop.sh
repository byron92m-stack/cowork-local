#!/bin/bash
QUERY="$*"

echo "🚀 $QUERY"
echo ""

python /media/SSD1T/cowork-local/apps/cli/cowork_graph.py "$QUERY" 2>/dev/null > /tmp/cowork_output.txt

# Iteraciones
ITER=$(python -c "import json; d=json.load(open('/tmp/cowork_output.txt').read().split('📊 RESULTADO:')[1].split('📁')[0].strip()); print(d['iteraciones'])" 2>/dev/null)
echo "✅ Completado en $ITER iteraciones"
echo ""

# Mostrar código
ARCHIVO=$(grep "📁" /tmp/cowork_output.txt | head -1 | awk '{print $2}')
if [ -f "$ARCHIVO" ]; then
    cat "$ARCHIVO"
else
    # Extraer código del output
    awk '/```python/{flag=1; next} /```/{flag=0} flag' /tmp/cowork_output.txt
fi

echo ""
echo "🏁 Fin"

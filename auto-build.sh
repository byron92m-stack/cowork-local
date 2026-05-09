#!/bin/bash
# ============================================
# COWORK UNIFICADO - Loop con verificación real
# Claude Code genera → Cowork ejecuta → Verifica → Repite
# ============================================

COWORK_DIR="/media/SSD1T/cowork-local"
CLAUDE="$COWORK_DIR/claude-code/node_modules/.bin/claude"
TASK="$1"
MAX_LOOPS="${2:-5}"
OUTPUT_DIR="/media/SSD1T/cowork-local/output"

mkdir -p "$OUTPUT_DIR"

[ -z "$TASK" ] && { echo "Uso: ./auto-build.sh 'crea un proyecto X' [max_intentos]"; exit 1; }

source "$COWORK_DIR/activate-unificado.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 COWORK UNIFICADO - Loop con Ejecución Real"
echo "   Tarea: $TASK"
echo "   Output: $OUTPUT_DIR"
echo "   Máx. iteraciones: $MAX_LOOPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for i in $(seq 1 $MAX_LOOPS); do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔄 Iteración $i de $MAX_LOOPS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 1. CLAUDE CODE PLANIFICA
    echo "🧠 Claude Code planificando..."
    PLAN=$($CLAUDE --model deepseek-chat --print "$TASK" 2>&1 | grep -v "HEAD / HTTP\|POST /v1\|INFO:\|Press CTRL\|🔄\|🐄\|✅")
    
    echo "$PLAN" | head -30
    
    # 2. COWORK EJECUTA (buscar comandos cowork execute en el plan)
    EXECUTED=0
    while IFS= read -r line; do
        if echo "$line" | grep -q "cowork execute"; then
            ACTION=$(echo "$line" | grep -oP 'cowork execute \K\S+')
            DATA=$(echo "$line" | grep -oP 'cowork execute \S+ \K.*' | sed "s/^'//;s/'$//")
            
            if [ -n "$ACTION" ] && [ -n "$DATA" ]; then
                echo "🦾 Ejecutando: cowork execute $ACTION '$DATA'"
                RESULT=$(python "$COWORK_DIR/apps/cli/execute_command.py" "$ACTION" "$DATA" 2>&1)
                echo "   ✅ $RESULT"
                EXECUTED=$((EXECUTED + 1))
            fi
        fi
    done <<< "$PLAN"
    
    # 3. VERIFICAR RESULTADOS
    echo ""
    echo "🔍 Verificando resultados..."
    
    # Buscar archivos creados en esta iteración
    NEW_FILES=$(find "$OUTPUT_DIR" -type f -newer "$COWORK_DIR/auto-build.sh" 2>/dev/null | head -10)
    if [ -n "$NEW_FILES" ]; then
        echo "   Archivos creados:"
        echo "$NEW_FILES" | while read f; do
            echo "   📁 $f ($(wc -c < "$f") bytes)"
        done
    fi
    
    # 4. CLAUDE CODE REVISA
    if [ $EXECUTED -gt 0 ]; then
        echo ""
        echo "🔍 Claude Code revisando..."
        REVIEW=$($CLAUDE --model deepseek-chat --print "Revisa el resultado de ejecutar: $PLAN. ¿Funcionó? ¿Hay errores? Responde SOLO con 'OK' si funcionó, o 'ERROR: <descripción>' si falló." 2>&1 | grep -v "HEAD / HTTP\|POST /v1\|INFO:\|Press CTRL")
        
        echo "   Revisión: $REVIEW"
        
        if echo "$REVIEW" | grep -q "^OK"; then
            echo ""
            echo "✅ ¡PROYECTO COMPLETADO Y VERIFICADO EN $i ITERACIONES!"
            exit 0
        else
            TASK="Corrige los errores: $REVIEW"
            echo "⚠️ Errores detectados, reintentando con: $TASK"
        fi
    else
        echo "   ⚠️ No se ejecutaron comandos cowork execute"
        TASK="$TASK (IMPORTANTE: usa 'cowork execute write-files' para crear archivos, NO solo describas)"
    fi
done

echo ""
echo "🏁 Finalizado después de $MAX_LOOPS iteraciones"
echo "   Revisa los archivos en $OUTPUT_DIR"

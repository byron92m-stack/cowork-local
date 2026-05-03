"""
Test del grafo usando solo Qwen local (sin DeepSeek).
"""
import sys
from pathlib import Path

# Detectar automáticamente el directorio del proyecto
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from graph.state import CoworkState
from graph.nodes.executor import executor_node

print("🧪 Probando executor Qwen local...\n")

state = CoworkState(
    user_query="Analiza la estructura del proyecto cowork-local y dime qué archivos hay",
    project_path=str(PROJECT_ROOT),
)

# Agregar un paso manual
state.add_step(
    description="Analiza la estructura del proyecto y lista los archivos principales",
    assigned_to="executor",
)

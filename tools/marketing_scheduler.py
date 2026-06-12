"""Marketing CLI wrapper: invoca el design_worker para campañas."""
import sys, os
sys.path.insert(0, "/media/SSD1T/cowork-local")
from dotenv import load_dotenv
load_dotenv()

from graph.graph_design import build_design_graph
from graph.state import DesignWorkerState

ACTIONS = {
    "generate": "campaign_generate",
    "view": "campaign_view",
    "approve": "campaign_approve",
    "list": "campaign_list",
}

def run(action: str):
    skill = ACTIONS.get(action, "campaign_generate")
    state = DesignWorkerState(query="", skill=skill)
    graph = build_design_graph()
    result = graph.invoke(state)
    print(result.get("reply", "Sin respuesta"))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python tools/marketing_scheduler.py [generate|view|approve|list]")
        sys.exit(1)
    run(sys.argv[1])

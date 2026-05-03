"""Workspace Manager - Multi-project persistent workspaces."""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class WorkspaceManager:
    def __init__(self, workspaces_dir: str = "data/workspaces"):
        self.workspaces_dir = Path(workspaces_dir)
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)
    
    def create_workspace(self, name: str, description: str = "", instructions: str = "") -> Dict:
        ws_dir = self.workspaces_dir / name
        ws_dir.mkdir(exist_ok=True)
        
        config = {
            "name": name,
            "description": description,
            "instructions": instructions,
            "created_at": str(__import__('datetime').datetime.now()),
            "files": [],
            "memory": {},
            "scheduled_tasks": []
        }
        
        with open(ws_dir / "config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        return config
    
    def get_workspace(self, name: str) -> Optional[Dict]:
        config_file = self.workspaces_dir / name / "config.json"
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        return None
    
    def list_workspaces(self) -> List[str]:
        return [d.name for d in self.workspaces_dir.iterdir() if d.is_dir()]
    
    def update_memory(self, name: str, key: str, value: Any):
        ws = self.get_workspace(name)
        if ws:
            ws["memory"][key] = value
            with open(self.workspaces_dir / name / "config.json", 'w') as f:
                json.dump(ws, f, indent=2)

workspace_manager = WorkspaceManager()
print(f"Workspace Manager ready with {len(workspace_manager.list_workspaces())} workspaces")

"""Plugin Manager for Cowork-Local."""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class PluginManager:
    def __init__(self, plugins_dir: str = "plugins/catalog"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.plugins = {}
        self._load_plugins()
    
    def _load_plugins(self):
        for yaml_file in self.plugins_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    plugin = yaml.safe_load(f)
                    self.plugins[plugin["name"]] = plugin
            except Exception as e:
                logger.error(f"Error loading plugin {yaml_file}: {e}")
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        return [{"name": p["name"], "version": p["version"], "description": p.get("description", "")} for p in self.plugins.values()]

plugin_manager = PluginManager()
print(f"Plugin Manager ready with {len(plugin_manager.plugins)} plugins")

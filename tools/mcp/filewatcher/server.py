"""File Watcher MCP Server.

Monitors directories for changes and can trigger agentic actions
when files are modified, created, or deleted.
"""
import os
import json
import time
import logging
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Estado global del watcher
_active_watchers: Dict[str, Any] = {}
_change_history: List[Dict] = []

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    
    class CoworkFileHandler(FileSystemEventHandler):
        """Handler que registra cambios en archivos."""
        
        def __init__(self, watch_id: str, callback=None):
            self.watch_id = watch_id
            self.callback = callback
            self.changes = []
        
        def on_modified(self, event):
            if not event.is_directory:
                change = {
                    "type": "modified",
                    "path": event.src_path,
                    "watch_id": self.watch_id,
                    "timestamp": str(datetime.now())
                }
                self.changes.append(change)
                _change_history.append(change)
                logger.info(f"File modified: {event.src_path}")
                if self.callback:
                    self.callback(change)
        
        def on_created(self, event):
            if not event.is_directory:
                change = {
                    "type": "created",
                    "path": event.src_path,
                    "watch_id": self.watch_id,
                    "timestamp": str(datetime.now())
                }
                self.changes.append(change)
                _change_history.append(change)
                logger.info(f"File created: {event.src_path}")
                if self.callback:
                    self.callback(change)
        
        def on_deleted(self, event):
            if not event.is_directory:
                change = {
                    "type": "deleted",
                    "path": event.src_path,
                    "watch_id": self.watch_id,
                    "timestamp": str(datetime.now())
                }
                self.changes.append(change)
                _change_history.append(change)
                logger.info(f"File deleted: {event.src_path}")
                if self.callback:
                    self.callback(change)
    
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("watchdog not installed. Install with: pip install watchdog")


async def call_tool(tool_name: str, arguments: Dict[str, Any]):
    """Execute file watcher operations."""
    
    if tool_name == "start_watching":
        directory = arguments.get("directory", os.getcwd())
        watch_id = arguments.get("watch_id", f"watch-{len(_active_watchers)}")
        patterns = arguments.get("patterns", ["*.py", "*.yaml", "*.json", "*.md", "*.txt"])
        auto_execute = arguments.get("auto_execute", False)
        
        if not WATCHDOG_AVAILABLE:
            return [type('obj', (object,), {
                'text': "❌ watchdog not installed. Run: pip install watchdog"
            })()]
        
        if not os.path.exists(directory):
            return [type('obj', (object,), {
                'text': f"❌ Directory not found: {directory}"
            })()]
        
        if watch_id in _active_watchers:
            return [type('obj', (object,), {
                'text': f"⚠️ Watcher already running: {watch_id}"
            })()]
        
        def on_change(change):
            """Callback when files change - puede disparar agentes."""
            if auto_execute:
                logger.info(f"Auto-execute triggered by: {change['path']}")
        
        try:
            handler = CoworkFileHandler(watch_id, callback=on_change if auto_execute else None)
            observer = Observer()
            observer.schedule(handler, directory, recursive=True)
            observer.start()
            
            _active_watchers[watch_id] = {
                "observer": observer,
                "handler": handler,
                "directory": directory,
                "patterns": patterns,
                "auto_execute": auto_execute,
                "started_at": str(datetime.now())
            }
            
            return [type('obj', (object,), {
                'text': f"✅ Watching {directory}\nID: {watch_id}\nPatterns: {patterns}\nAuto-execute: {auto_execute}"
            })]
        except Exception as e:
            return [type('obj', (object,), {
                'text': f"❌ Error starting watcher: {e}"
            })]
    
    elif tool_name == "stop_watching":
        watch_id = arguments.get("watch_id")
        
        if not watch_id:
            return [type('obj', (object,), {
                'text': "❌ Specify watch_id to stop"
            })()]
        
        if watch_id in _active_watchers:
            try:
                _active_watchers[watch_id]["observer"].stop()
                _active_watchers[watch_id]["observer"].join(timeout=2)
                del _active_watchers[watch_id]
                return [type('obj', (object,), {
                    'text': f"✅ Watcher stopped: {watch_id}"
                })]
            except Exception as e:
                return [type('obj', (object,), {
                    'text': f"❌ Error stopping watcher: {e}"
                })]
        else:
            return [type('obj', (object,), {
                'text': f"❌ Watcher not found: {watch_id}"
            })]
    
    elif tool_name == "list_watchers":
        if not _active_watchers:
            return [type('obj', (object,), {
                'text': "No active watchers"
            })()]
        
        info = []
        for wid, wdata in _active_watchers.items():
            info.append(
                f"ID: {wid}\n"
                f"  Directory: {wdata['directory']}\n"
                f"  Patterns: {wdata['patterns']}\n"
                f"  Auto-execute: {wdata['auto_execute']}\n"
                f"  Started: {wdata['started_at']}\n"
                f"  Changes detected: {len(wdata['handler'].changes)}"
            )
        
        return [type('obj', (object,), {
            'text': "📁 Active watchers:\n\n" + "\n\n".join(info)
        })]
    
    elif tool_name == "get_changes":
        watch_id = arguments.get("watch_id")
        limit = arguments.get("limit", 20)
        
        if watch_id and watch_id in _active_watchers:
            changes = _active_watchers[watch_id]["handler"].changes[-limit:]
        else:
            changes = _change_history[-limit:]
        
        if not changes:
            return [type('obj', (object,), {
                'text': "No changes detected"
            })()]
        
        formatted = []
        for c in reversed(changes):
            icon = {"modified": "✏️", "created": "➕", "deleted": "🗑️"}.get(c["type"], "📄")
            formatted.append(f"{icon} [{c['timestamp'][:19]}] {c['type']}: {c['path']}")
        
        return [type('obj', (object,), {
            'text': "📝 Recent changes:\n\n" + "\n".join(formatted)
        })]
    
    elif tool_name == "analyze_and_act":
        """Analiza cambios recientes y sugiere acciones."""
        directory = arguments.get("directory", os.getcwd())
        
        if not _change_history:
            return [type('obj', (object,), {
                'text': "No changes to analyze"
            })()]
        
        recent = _change_history[-10:]
        
        summary = []
        modified_files = set()
        
        for c in recent:
            if c["type"] == "modified":
                modified_files.add(c["path"])
        
        if modified_files:
            summary.append(f"📝 {len(modified_files)} files modified")
            for f in list(modified_files)[:5]:
                summary.append(f"   - {f}")
            
            summary.append(f"\n💡 Suggested actions:")
            summary.append(f"   ./cowork run --query 'Review recent changes in the project'")
            summary.append(f"   ./cowork run --query 'Run tests on modified files'")
        
        return [type('obj', (object,), {
            'text': "\n".join(summary) if summary else "No significant changes"
        })]
    
    else:
        return [type('obj', (object,), {
            'text': f"Unknown tool: {tool_name}. Available: start_watching, stop_watching, list_watchers, get_changes, analyze_and_act"
        })()]

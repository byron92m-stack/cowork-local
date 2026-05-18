from typing import Dict, Any
"""Code Sandbox MCP Server - Execute code in isolated environment."""
import os
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)

async def call_tool(tool_name: str, arguments: Dict[str, Any]):
    """Execute code in sandboxed environment."""
    
    if tool_name == "execute_python":
        code = arguments.get("code", "")
        timeout = arguments.get("timeout", 30)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ['python3', temp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd='/tmp'
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]:\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[exit code]: {result.returncode}"
            
            return [type('obj', (object,), {'text': output[:5000]})()]
        except subprocess.TimeoutExpired:
            return [type('obj', (object,), {'text': f"Timeout after {timeout}s"})()]
        finally:
            os.unlink(temp_path)
    
    elif tool_name == "execute_shell":
        command = arguments.get("command", "")
        timeout = arguments.get("timeout", 30)
        
        try:
            result = subprocess.run(
                command, shell=True,
                capture_output=True, text=True,
                timeout=timeout,
                cwd='/tmp'
            )
            output = result.stdout or result.stderr
            return [type('obj', (object,), {'text': output[:5000]})()]
        except subprocess.TimeoutExpired:
            return [type('obj', (object,), {'text': f"Timeout after {timeout}s"})()]
    
    elif tool_name == "install_package":
        package = arguments.get("package", "")
        try:
            result = subprocess.run(
                ['pip', 'install', package],
                capture_output=True, text=True, timeout=60
            )
            return [type('obj', (object,), {'text': result.stdout[-1000:]})()]
        except Exception as e:
            return [type('obj', (object,), {'text': f"Error: {e}"})()]
    
    else:
        return [type('obj', (object,), {'text': f"Unknown sandbox tool: {tool_name}"})()]

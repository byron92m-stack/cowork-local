"""Docker Sandbox MCP Server - VM-level isolation for code execution.

Compatible with SELinux (Fedora/RHEL) using :Z flag on volumes.
"""
import os
import json
import uuid
import logging
import tempfile
from typing import Dict, Any
import asyncio

logger = logging.getLogger(__name__)

SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "python:3.12-slim")
DEFAULT_TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT", "30"))
DEFAULT_MEMORY = os.getenv("SANDBOX_MEMORY", "512m")
DEFAULT_CPU = os.getenv("SANDBOX_CPU", "1.0")

async def call_tool(tool_name: str, arguments: Dict[str, Any]):
    """Execute operations in sandboxed Docker containers."""
    
    if tool_name == "execute_python":
        code = arguments.get("code", "")
        timeout = arguments.get("timeout", DEFAULT_TIMEOUT)
        
        container_id = uuid.uuid4().hex[:8]
        container_name = f"cowork-sandbox-{container_id}"
        
        tmp_path = None
        try:
            # Crear archivo temporal con código
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', delete=False, prefix='cowork_'
            ) as f:
                f.write(code)
                tmp_path = f.name
            
            # Asegurar permisos de lectura
            os.chmod(tmp_path, 0o644)
            
            # Construir comando docker
            cmd = [
                "docker", "run",
                "--rm",
                f"--name={container_name}",
                f"--memory={DEFAULT_MEMORY}",
                f"--cpus={DEFAULT_CPU}",
                "--network=none",
                "--tmpfs=/tmp:rw,noexec,nosuid,size=100m",
                "--security-opt=no-new-privileges",
                "--cap-drop=ALL",
                "--pids-limit=50",
                "-v", f"{tmp_path}:/code/script.py:ro,Z",
                "-w", "/tmp",
                SANDBOX_IMAGE,
                "sh", "-c", f"cat /code/script.py > /tmp/script.py && timeout {timeout} python /tmp/script.py"
            ]
            
            logger.info(f"Starting sandbox: {container_name}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout + 5
                )
            except asyncio.TimeoutError:
                try:
                    kill_proc = await asyncio.create_subprocess_exec(
                        "docker", "kill", container_name,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await kill_proc.communicate()
                except:
                    pass
                
                return [type('obj', (object,), {
                    'text': f"Timeout: Code execution exceeded {timeout}s limit"
                })()]
            
            output = stdout.decode('utf-8', errors='replace')
            stderr_output = stderr.decode('utf-8', errors='replace')
            
            if stderr_output:
                output += f"\n[stderr]:\n{stderr_output}"
            if process.returncode and process.returncode != 0:
                output += f"\n[exit code]: {process.returncode}"
            
            result = output[:5000]
            if len(output) > 5000:
                result += f"\n... (truncated, total {len(output)} chars)"
            
            return [type('obj', (object,), {
                'text': f"Sandbox output:\n{result}"
            })]
            
        except FileNotFoundError:
            return [type('obj', (object,), {
                'text': "Docker not installed. Install Docker to use the sandbox."
            })]
        except Exception as e:
            logger.error(f"Sandbox error: {e}")
            return [type('obj', (object,), {
                'text': f"Sandbox error: {str(e)}"
            })]
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except:
                    pass
    
    elif tool_name == "execute_shell":
        command = arguments.get("command", "")
        timeout = arguments.get("timeout", DEFAULT_TIMEOUT)
        
        container_id = uuid.uuid4().hex[:8]
        container_name = f"cowork-shell-{container_id}"
        
        cmd = [
            "docker", "run",
            "--rm",
            f"--name={container_name}",
            f"--memory={DEFAULT_MEMORY}",
            f"--cpus={DEFAULT_CPU}",
            "--network=none",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=100m",
            "--security-opt=no-new-privileges",
            "--cap-drop=ALL",
            "--pids-limit=50",
            SANDBOX_IMAGE,
            "sh", "-c", command
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout + 5
                )
            except asyncio.TimeoutError:
                try:
                    kill_proc = await asyncio.create_subprocess_exec(
                        "docker", "kill", container_name,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await kill_proc.communicate()
                except:
                    pass
                return [type('obj', (object,), {
                    'text': f"Timeout: Shell execution exceeded {timeout}s"
                })()]
            
            output = stdout.decode('utf-8', errors='replace')
            if not output:
                output = stderr.decode('utf-8', errors='replace')
            
            return [type('obj', (object,), {
                'text': f"Shell output:\n{output[:5000]}"
            })]
            
        except FileNotFoundError:
            return [type('obj', (object,), {
                'text': "Docker not installed"
            })]
        except Exception as e:
            return [type('obj', (object,), {
                'text': f"Shell sandbox error: {str(e)}"
            })]
    
    elif tool_name == "status":
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "info",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if process.returncode == 0:
                return [type('obj', (object,), {
                    'text': f"Docker sandbox ready\nImage: {SANDBOX_IMAGE}\nTimeout: {DEFAULT_TIMEOUT}s\nMemory: {DEFAULT_MEMORY}\nCPU: {DEFAULT_CPU}"
                })]
            else:
                return [type('obj', (object,), {
                    'text': "Docker is not running"
                })]
        except FileNotFoundError:
            return [type('obj', (object,), {
                'text': "Docker not installed"
            })]
    
    elif tool_name == "pull_image":
        image = arguments.get("image", SANDBOX_IMAGE)
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "pull", image,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return [type('obj', (object,), {
                'text': f"Image pulled:\n{stdout.decode()[-500:]}"
            })]
        except Exception as e:
            return [type('obj', (object,), {
                'text': f"Error pulling image: {e}"
            })]
    
    else:
        return [type('obj', (object,), {
            'text': f"Unknown sandbox tool: {tool_name}. Available: execute_python, execute_shell, status, pull_image"
        })()]

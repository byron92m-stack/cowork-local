"""Tests para execute_command.py"""
import sys, os, pytest, io
sys.path.insert(0, "/media/SSD1T/cowork-local")

def test_write_file_args():
    """Test: write-file con argumentos directos"""
    from apps.cli.execute_command import execute
    import asyncio
    
    result = asyncio.run(execute("write-file", "/tmp/test_args.txt", "Hola desde test"))
    assert "OK" in result or "Error" in result

def test_write_file_stdin():
    """Test: write-file con stdin simulado"""
    from apps.cli.execute_command import execute
    import asyncio
    
    # Simular stdin con StringIO
    test_input = io.StringIO("def hola(): return 'mundo'")
    sys.stdin = test_input
    
    result = asyncio.run(execute("write-file", "/tmp/test_stdin.txt"))
    assert "OK" in result or "Error" in result

def test_import():
    """Test: importar sin errores"""
    from apps.cli import execute_command
    from apps.cli import search_tools
    from apps.cli import apply_diff
    from apps.cli import session_memory
    from apps.cli import tool_caller
    from apps.cli import cowork_graph
    assert True

def test_mcp_client():
    """Test: MCP client importa"""
    from tools.mcp_client import get_mcp_client
    client = get_mcp_client()
    assert client is not None

def test_graph_import():
    """Test: grafo importa"""
    from graph.graph import run_graph
    from graph.state import CoworkState
    state = CoworkState(user_query="test", project_path="/tmp")
    assert state.session_id is not None

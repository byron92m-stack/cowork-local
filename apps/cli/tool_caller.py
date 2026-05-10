"""Tool Caller Robusto: Detecta y ejecuta tool calls de DeepSeek con múltiples formatos."""
import re, json, subprocess, os

COWORK = "/media/SSD1T/cowork-local"

def execute_tool(tool_name: str, args: dict) -> str:
    """Ejecuta una herramienta y devuelve el resultado."""
    try:
        if tool_name == "write_file":
            path = args.get("path", "")
            content = args.get("content", "")
            if path and content:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    f.write(content)
                return f"✅ Archivo creado: {path}"
            return "❌ Faltan path o content"
        
        elif tool_name == "execute_command":
            cmd = args.get("command", "")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout or result.stderr or "(ok)"
        
        elif tool_name == "search_code":
            query = args.get("query", "")
            result = subprocess.run(["grep", "-rn", query, COWORK], capture_output=True, text=True, timeout=15)
            return result.stdout[:2000] or "No encontrado"
        
        return f"✅ {tool_name}: ejecutado"
    except Exception as e:
        return f"❌ Error: {e}"

def extract_and_execute(text: str) -> list:
    """Extrae tool calls del texto y los ejecuta. Soporta 5 formatos."""
    results = []
    
    # Formato 1: cowork execute <tool> <args>
    matches = re.findall(r'cowork execute (\S+) (.+)', text)
    for tool, args_str in matches:
        try:
            args = json.loads(args_str) if args_str.startswith('{') else {"command": args_str}
        except:
            args = {"command": args_str}
        result = execute_tool(tool, args)
        results.append(f"[{tool}] {result}")
    
    # Formato 2: <tool_call> JSON
    matches = re.findall(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
    for json_str in matches:
        try:
            data = json.loads(json_str)
            if "tool" in data and "args" in data:
                result = execute_tool(data["tool"], data["args"])
                results.append(f"[{data['tool']}] {result}")
        except:
            pass
    
    # Formato 3: <tool_name>(args)
    matches = re.findall(r'(\w+)\((.*?)\)', text)
    for tool, args_str in matches:
        if tool in ("write_file", "execute_command", "search_code"):
            try:
                args = json.loads(args_str) if args_str.startswith('{') else {"command": args_str}
            except:
                args = {"command": args_str}
            result = execute_tool(tool, args)
            results.append(f"[{tool}] {result}")
    
    # Formato 4: XML tool calls
    matches = re.findall(r'<tool_name>(\w+)</tool_name>.*?<args>(.*?)</args>', text, re.DOTALL)
    for tool, args_str in matches:
        try:
            args = json.loads(args_str)
            result = execute_tool(tool, args)
            results.append(f"[{tool}] {result}")
        except:
            pass
    
    # Formato 5: Función Python directa
    if "write_file(" in text and "content=" in text:
        path_match = re.search(r'path\s*=\s*["\'](.+?)["\']', text)
        content_match = re.search(r'content\s*=\s*["\'](.+?)["\']', text)
        if path_match and content_match:
            result = execute_tool("write_file", {"path": path_match.group(1), "content": content_match.group(1)})
            results.append(f"[write_file] {result}")
    
    return results

if __name__ == "__main__":
    import sys
    text = sys.stdin.read() if not sys.stdin.isatty() else " ".join(sys.argv[1:])
    results = extract_and_execute(text)
    if results:
        print("\n".join(results))
    else:
        print("❌ No se detectaron tool calls")

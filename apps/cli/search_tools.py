"""Herramientas de búsqueda para Claude Code."""
import subprocess, sys, os

COWORK = "/media/SSD1T/cowork-local"

def search_code(query, path=None):
    """Busca texto en archivos del proyecto (grep)."""
    search_path = path or COWORK
    try:
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py", "--include=*.md", "--include=*.yaml", 
             "--include=*.yml", "--include=*.sh", query, search_path],
            capture_output=True, text=True, timeout=30,
            cwd=COWORK
        )
        output = result.stdout.strip()
        return output[:3000] if output else f"'{query}' no encontrado"
    except Exception as e:
        return f"Error: {e}"

def find_files(pattern, path=None):
    """Busca archivos por patrón (find)."""
    search_path = path or COWORK
    try:
        result = subprocess.run(
            ["find", search_path, "-name", pattern, "-not", "-path", "*/venv/*", 
             "-not", "-path", "*/node_modules/*", "-not", "-path", "*/.git/*"],
            capture_output=True, text=True, timeout=30,
            cwd=COWORK
        )
        output = result.stdout.strip()
        return output[:3000] if output else f"No se encontraron archivos: {pattern}"
    except Exception as e:
        return f"Error: {e}"

def list_modules(path=None):
    """Lista módulos Python del proyecto."""
    search_path = path or COWORK
    try:
        result = subprocess.run(
            ["find", search_path, "-name", "*.py", "-not", "-path", "*/venv/*",
             "-not", "-path", "*/node_modules/*", "-not", "-path", "*/.git/*",
             "-not", "-path", "*/output/*"],
            capture_output=True, text=True, timeout=30,
            cwd=COWORK
        )
        files = result.stdout.strip().split('\n')
        modules = [f.replace(search_path + '/', '').replace('/', '.').replace('.py', '') 
                   for f in files if f]
        return "\n".join(sorted(modules)[:50])
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: search_tools.py <search|find|modules> <query> [path]")
        sys.exit(1)
    
    action = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else ""
    path = sys.argv[3] if len(sys.argv) > 3 else None
    
    if action == "search":
        print(search_code(query, path))
    elif action == "find":
        print(find_files(query, path))
    elif action == "modules":
        print(list_modules(path))
    else:
        print(f"Acción desconocida: {action}")

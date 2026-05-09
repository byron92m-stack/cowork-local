"""Aplica cambios a archivos existentes (diff/patch)."""
import sys, os, re

COWORK = "/media/SSD1T/cowork-local"

def apply_change(filepath, old_text, new_text):
    """Reemplaza old_text por new_text en un archivo."""
    if not os.path.exists(filepath):
        return f"❌ Archivo no encontrado: {filepath}"
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        if old_text not in content:
            return f"❌ Texto no encontrado en {filepath}"
        
        new_content = content.replace(old_text, new_text, 1)
        
        with open(filepath, 'w') as f:
            f.write(new_content)
        
        return f"✅ {filepath}: cambio aplicado"
    except Exception as e:
        return f"❌ Error: {e}"

def apply_line_change(filepath, line_number, new_line):
    """Reemplaza una línea específica de un archivo."""
    if not os.path.exists(filepath):
        return f"❌ Archivo no encontrado: {filepath}"
    
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        if line_number < 1 or line_number > len(lines):
            return f"❌ Línea {line_number} fuera de rango (1-{len(lines)})"
        
        old_line = lines[line_number - 1].rstrip('\n')
        lines[line_number - 1] = new_line + '\n'
        
        with open(filepath, 'w') as f:
            f.writelines(lines)
        
        return f"✅ {filepath}: línea {line_number}: '{old_line[:50]}...' → '{new_line[:50]}...'"
    except Exception as e:
        return f"❌ Error: {e}"

def apply_diff_file(diff_file):
    """Aplica un archivo diff unificado con patch."""
    if not os.path.exists(diff_file):
        return f"❌ Diff no encontrado: {diff_file}"
    
    try:
        import subprocess
        result = subprocess.run(
            ["patch", "-p1", "-i", diff_file],
            capture_output=True, text=True, timeout=30,
            cwd=COWORK
        )
        return result.stdout.strip() or "✅ Diff aplicado"
    except Exception as e:
        return f"❌ Error: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: apply_diff.py <change|line|file> <args...>")
        print("  change <file> '<old>' '<new>'")
        print("  line <file> <num> '<new_line>'")
        print("  file <diff_file>")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "change":
        filepath = sys.argv[2]
        old_text = sys.argv[3]
        new_text = sys.argv[4] if len(sys.argv) > 4 else ""
        print(apply_change(filepath, old_text, new_text))
    
    elif action == "line":
        filepath = sys.argv[2]
        line_num = int(sys.argv[3])
        new_line = sys.argv[4] if len(sys.argv) > 4 else ""
        print(apply_line_change(filepath, line_num, new_line))
    
    elif action == "file":
        diff_file = sys.argv[2]
        print(apply_diff_file(diff_file))
    
    else:
        print(f"Acción desconocida: {action}")

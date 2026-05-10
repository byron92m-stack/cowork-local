"""Auto-ejecuta el grafo cuando detecta cambios en archivos Python."""
import sys, os, time, subprocess
sys.path.insert(0, "/media/SSD1T/cowork-local")

WATCH_DIR = sys.argv[1] if len(sys.argv) > 1 else "/media/SSD1T/cowork-local"
PATTERN = sys.argv[2] if len(sys.argv) > 2 else "*.py"

print(f"👁️  Observando {WATCH_DIR} ({PATTERN})")
print(f"   Cada cambio ejecutará el grafo automáticamente")
print(f"   Ctrl+C para detener")
print()

last_run = 0

try:
    while True:
        # Buscar archivos modificados recientemente (últimos 5 segundos)
        result = subprocess.run(
            ["find", WATCH_DIR, "-name", PATTERN, "-mmin", "-0.1",
             "-not", "-path", "*/venv/*", "-not", "-path", "*/node_modules/*",
             "-not", "-path", "*/output/*", "-not", "-path", "*/.git/*"],
            capture_output=True, text=True, timeout=10
        )
        
        changed = result.stdout.strip()
        now = time.time()
        
        if changed and (now - last_run) > 10:  # No ejecutar más de 1 vez cada 10s
            last_run = now
            files = changed.split('\n')[:3]  # Máximo 3 archivos
            
            print(f"🔄 Cambio detectado en: {', '.join(files)}")
            print("🧠 Ejecutando grafo...")
            
            task = f"Revisa los cambios en: {', '.join(files)}. Sugiere mejoras o corrige errores."
            
            result = subprocess.run(
                ["/media/SSD1T/cowork-local/apps/cli/loop.sh", task],
                capture_output=True, text=True, timeout=120,
                cwd=WATCH_DIR,
                env={**os.environ, "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY", "")}
            )
            
            # Solo mostrar las primeras 10 líneas
            output = result.stdout.strip().split('\n')[:10]
            print('\n'.join(output))
            print("✅ Listo. Esperando más cambios...\n")
        
        time.sleep(3)

except KeyboardInterrupt:
    print("\n👁️  Watcher detenido")

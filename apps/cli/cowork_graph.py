"""Cowork + OpenCode integrados."""
import sys, os, subprocess, json

COWORK_DIR = "/media/SSD1T/cowork-local"
QUERY = " ".join(sys.argv[1:])

print(f"> build · cowork+opencode\n")
print(f"$ opencode run \"{QUERY[:60]}...\"\n")

# Ejecutar OpenCode directamente desde Cowork
result = subprocess.run(
    ["opencode", "run", QUERY],
    capture_output=True, text=True, timeout=300,
    cwd=COWORK_DIR,
    env={**os.environ, "OPENCODE_MODE": "auto"}
)

print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

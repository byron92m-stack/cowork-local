"""Proxy Unificado: cowork: = grafo, el resto = chat DeepSeek"""
from flask import Flask, request, jsonify
import httpx, json, uuid, subprocess, os, os

app = Flask(__name__)
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "sk-122139651350414899e1617d190c94f3"
COWORK = "/media/SSD1T/cowork-local"

def run_graph(query):
    try:
        r = subprocess.run(
            [f"{COWORK}/apps/cli/loop.sh", query],
            capture_output=True, text=True, timeout=90,
            cwd=COWORK,
            env={**os.environ, "DEEPSEEK_API_KEY": API_KEY}
        )
        out = r.stdout.strip() or "OK"
        # Solo devolver el código, sin logs
        lines = out.split('\n')
        code_lines = []
        for line in lines:
            if line and not line.startswith('🚀') and not line.startswith('✅') and not line.startswith('🏁') and 'iteraciones' not in line:
                code_lines.append(line)
        return '\n'.join(code_lines).strip() or "Codigo generado OK"
    except Exception as e:
        return f"Error: {e}"

@app.route('/v1/messages', methods=['POST'])
def proxy():
    data = request.json
    messages = []
    # Cargar CLAUDE.md del proyecto
    claude_md = ""
    claude_md_path = os.path.join(COWORK, "CLAUDE.md")
    if os.path.exists(claude_md_path):
        with open(claude_md_path) as f:
            claude_md = f.read()
    
    system = data.get('system', '')
    if claude_md:
        messages.append({"role": "system", "content": claude_md})
    if system and system != claude_md:
        messages.append({"role": "system", "content": str(system)})
    
    user_input = ""
    for msg in data.get('messages', []):
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if isinstance(content, list):
            content = ' '.join([c.get('text', '') for c in content if isinstance(c, dict)])
        if role == 'user':
            user_input += " " + content
        messages.append({"role": role, "content": str(content)})
    
    user_input = user_input.strip()
    
    # Modo COWORK: si empieza con "cowork:" o "cowork "
    if user_input.lower().startswith("cowork:") or user_input.lower().startswith("cowork "):
        query = user_input.split(":", 1)[-1].strip() if ":" in user_input else user_input[7:].strip()
        result = run_graph(query)
        return jsonify({
            "id": f"msg_{uuid.uuid4().hex[:24]}", "type": "message", "role": "assistant",
            "content": [{"type": "text", "text": result}], "model": "cowork",
            "stop_reason": "end_turn",
        })
    
    # Modo CHAT normal
    payload = {"model": "deepseek-chat", "messages": messages, "max_tokens": 4096, "temperature": 0.7, "stream": False}
    try:
        r = httpx.post(DEEPSEEK_URL, json=payload, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=60)
        resp = r.json()
        content = resp['choices'][0]['message']['content']
        return jsonify({
            "id": f"msg_{uuid.uuid4().hex[:24]}", "type": "message", "role": "assistant",
            "content": [{"type": "text", "text": content}], "model": "deepseek-chat",
            "stop_reason": "end_turn", "usage": resp.get('usage', {}),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/v1/models')
def models():
    return jsonify({"data": [{"id": "deepseek-chat", "object": "model", "created": 1}]})

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    print("Proxy [cowork: + chat] en :8080")
    app.run(host='0.0.0.0', port=8080, debug=False)

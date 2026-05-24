import time, requests, os, sys, json, redis

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8734865184:AAE53p-n9Uc-xmmYzPiB7EROiG_Xw5ci98k")
REDIS = redis.Redis(host='localhost', port=6379, decode_responses=True)
STATE_FILE = "/media/SSD1T/cowork-local/data/telegram_state.txt"

# Cargar último update_id
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        last_update_id = int(f.read().strip())
else:
    r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates")
    updates = r.json().get("result", [])
    last_update_id = updates[-1]["update_id"] if updates else 0
    with open(STATE_FILE, "w") as f:
        f.write(str(last_update_id))

def save_state(uid):
    with open(STATE_FILE, "w") as f:
        f.write(str(uid))

def get_session(chat_id):
    """Obtener o crear sesión para un chat_id"""
    session_key = f"cowork:session:{chat_id}"
    current = REDIS.get(f"cowork:current:{chat_id}") or session_key
    return current

def set_session(chat_id, session_name):
    """Cambiar a una sesión específica"""
    REDIS.set(f"cowork:current:{chat_id}", session_name)
    return session_name

def list_sessions(chat_id):
    """Listar todas las sesiones disponibles"""
    all_sessions = REDIS.keys("cowork:session:*")
    current = get_session(chat_id)
    result = ["📋 *Sesiones activas:*\n"]
    for s in sorted(all_sessions):
        name = s.replace("cowork:session:", "")
        marker = " ← actual" if s == current else ""
        result.append(f"• `{name}`{marker}")
    return "\n".join(result) if len(all_sessions) > 1 else "Solo tenés una sesión activa."

def handle_command(chat_id, text):
    """Procesar comandos del bot"""
    parts = text.strip().split()
    cmd = parts[0].lower()
    
    if cmd == "/list" or cmd == "/sesiones" or cmd == "/listar":
        return list_sessions(chat_id)
    
    elif cmd == "/switch" or cmd == "/cambiar":
        if len(parts) < 2:
            return "Usá: `/switch nombre_de_sesion`\nEj: `/switch pc-terminal`"
        session_name = parts[1]
        session_key = f"cowork:session:{session_name}"
        if REDIS.exists(session_key):
            set_session(chat_id, session_key)
            return f"✅ Cambiado a sesión `{session_name}`"
        return f"❌ No existe la sesión `{session_name}`. Usá `/list` para ver las disponibles."
    
    elif cmd == "/nueva" or cmd == "/new":
        if len(parts) < 2:
            return "Usá: `/nueva nombre_de_sesion`"
        session_name = parts[1]
        session_key = f"cowork:session:{session_name}"
        REDIS.setex(session_key, 3600, json.dumps({"created": True, "name": session_name}))
        set_session(chat_id, session_key)
        return f"✅ Sesión `{session_name}` creada y activada. Duración: 1 hora."
    
    elif cmd == "/cerrar" or cmd == "/close":
        current = get_session(chat_id)
        REDIS.delete(current)
        # Volver a la sesión default del chat
        default = f"cowork:session:{chat_id}"
        set_session(chat_id, default)
        return f"✅ Sesión cerrada. Volviste a la sesión por defecto."
    
    elif cmd == "/estado" or cmd == "/status":
        current = get_session(chat_id)
        name = current.replace("cowork:session:", "")
        data = REDIS.get(current)
        info = "vacía" if not data else "con datos"
        return f"📊 Sesión actual: `{name}` ({info})"
    
    elif cmd == "/pc":
        # Sincronizar con sesión de PC
        pc_session = "cowork:session:pc-terminal"
        if REDIS.exists(pc_session):
            set_session(chat_id, pc_session)
            return "✅ Conectado a la sesión de la PC. Ambos comparten la misma conversación."
        else:
            # Crear sesión compartida
            REDIS.setex(pc_session, 3600, json.dumps({"shared": True}))
            set_session(chat_id, pc_session)
            return "✅ Sesión compartida PC-Telegram creada. En la PC usá `--session pc-terminal`."
    
    elif cmd == "/ayuda" or cmd == "/help":
        return """🤖 *Comandos disponibles:*
/list - Ver todas las sesiones
/switch NOMBRE - Cambiar de sesión
/nueva NOMBRE - Crear sesión nueva
/cerrar - Cerrar sesión actual
/estado - Ver estado de la sesión
/pc - Conectar con sesión de la PC
/ayuda - Este mensaje"""
    
    return None  # No es un comando, es un mensaje normal

print(f"🤖 Asistente Cowork iniciado. Último ID: {last_update_id}")
print("   Comandos: /list /switch /nueva /cerrar /estado /pc /ayuda")
print("   Escribile a @byron92m_bot...")

while True:
    try:
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", 
                        params={"offset": last_update_id + 1, "timeout": 10})
        updates = r.json().get("result", [])
        
        for upd in updates:
            last_update_id = upd["update_id"]
            save_state(last_update_id)
            
            msg = upd.get("message", {})
            text = msg.get("text", "")
            chat_id = msg.get("chat", {}).get("id")
            
            if not text or not chat_id:
                continue
            
            # SEGURIDAD NIVEL 1: Solo mi usuario
            if str(chat_id) != "8047752200":
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": "⛔ Bot privado. Solo responde a @ByronMartinez92."})
                print(f"🚫 Bloqueado: {chat_id}")
                continue
            
            print(f"📩 [{chat_id}] {text[:50]}...")
            
            # Verificar si es un comando
            command_response = handle_command(chat_id, text)
            if command_response:
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": command_response, "parse_mode": "Markdown"})
                print("✅ Comando procesado")
                continue
            
            # Mensaje normal → enviar a Cowork
            login = requests.post("http://127.0.0.1:8000/auth/login",
                json={"username": os.getenv("API_USER", "admin"), "password": os.getenv("API_PASS", "admin123")}).json()
            
            # Usar la sesión actual del chat
            current_session = get_session(chat_id)
            
            chat = requests.post("http://127.0.0.1:8000/chat/assistant",
                json={"content": text, "chat_id": current_session},
                headers={"Authorization": f"Bearer {login.get('access_token','')}"}).json()
            
            reply = chat.get("reply", "Error")
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": reply[:4000]})
            print("✅")
    except KeyboardInterrupt:
        print(f"\n👋 Chau. Último ID guardado: {last_update_id}")
        break
    except Exception as e:
        print(f"⚠️ {e}")
        time.sleep(5)


"""
🐄 Cowork-Local Pro UI - Claude Cowork Style Interface
With chat persistence, new chat, and file upload.
"""
import sys
import os
import json
import base64
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

st.set_page_config(
    page_title="🐄 Cowork-Local Pro",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────
st.markdown("""
<style>
.main { background-color: #0f1117; color: #e1e4e8; }
.stApp { background-color: #0f1117; }
[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}
.project-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
    cursor: pointer;
}
.project-card:hover { border-color: #58a6ff; }
.user-msg { 
    background: #1c2128; 
    border-left: 3px solid #58a6ff;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    margin: 8px 0;
}
.assistant-msg {
    background: #161b22;
    border-left: 3px solid #3fb950;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    margin: 8px 0;
}
.thinking-msg {
    background: #1a1f2e;
    border-left: 3px solid #d2991d;
    padding: 8px 12px;
    font-size: 0.85em;
    color: #8b949e;
    border-radius: 0 8px 8px 0;
    margin: 4px 0;
}
.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
}
.status-online { background: #3fb950; }
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background-color: #161b22;
    border-radius: 8px;
    padding: 4px;
}
.stTabs [aria-selected="true"] {
    background-color: #1c2128;
    color: #e1e4e8;
}
.saved-chat-item {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 4px 0;
    cursor: pointer;
    font-size: 0.85em;
}
.saved-chat-item:hover { border-color: #58a6ff; }
</style>
""", unsafe_allow_html=True)

# ─── Chat storage ────────────────────────────────────────────
CHATS_DIR = Path(PROJECT_ROOT) / "data" / "chats"
CHATS_DIR.mkdir(parents=True, exist_ok=True)

def save_chat(name, messages):
    filepath = CHATS_DIR / f"{name}.json"
    with open(filepath, "w") as f:
        json.dump({"name": name, "messages": messages, "saved_at": str(datetime.now())}, f, indent=2)

def load_chat(name):
    filepath = CHATS_DIR / f"{name}.json"
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return None

def list_saved_chats():
    return sorted([f.stem for f in CHATS_DIR.glob("*.json")], reverse=True)

def delete_chat(name):
    filepath = CHATS_DIR / f"{name}.json"
    if filepath.exists():
        filepath.unlink()

# ─── File handling ───────────────────────────────────────────
def process_uploaded_file(uploaded_file):
    """Process uploaded file and return content for the chat."""
    if uploaded_file is None:
        return None, None
    
    filename = uploaded_file.name
    ext = Path(filename).suffix.lower()
    
    try:
        # Text files
        if ext in [".py", ".txt", ".md", ".yaml", ".json", ".sql", ".sh", ".env", ".cfg", ".ini", ".log", ".csv"]:
            content = uploaded_file.read().decode("utf-8", errors="replace")
            return filename, f"File: {filename}\n```{ext[1:]}\n{content[:5000]}\n```"
        
        # Images
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"]:
            bytes_data = uploaded_file.read()
            b64 = base64.b64encode(bytes_data).decode()
            return filename, f"![{filename}](data:image/{ext[1:]};base64,{b64})"
        
        # PDF
        elif ext == ".pdf":
            content = f"[PDF File: {filename}] - {uploaded_file.size} bytes"
            return filename, content
        
        # Office docs
        elif ext in [".xlsx", ".xls"]:
            content = f"[Excel File: {filename}] - {uploaded_file.size} bytes"
            return filename, content
        elif ext in [".pptx", ".ppt"]:
            content = f"[PowerPoint File: {filename}] - {uploaded_file.size} bytes"
            return filename, content
        elif ext in [".docx", ".doc"]:
            content = f"[Word File: {filename}] - {uploaded_file.size} bytes"
            return filename, content
        
        # Archives
        elif ext in [".zip", ".tar", ".gz", ".tar.gz"]:
            content = f"[Archive: {filename}] - {uploaded_file.size} bytes"
            return filename, content
        
        else:
            content = f"[File: {filename}] - {uploaded_file.size} bytes - Type: {ext}"
            return filename, content
    
    except Exception as e:
        return filename, f"[Error reading file: {str(e)}]"

# ─── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.title("🐄 Cowork Pro")
    st.caption("Agentic Development Assistant")
    st.markdown("---")
    
    # Status
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<span class="status-dot status-online"></span> GPU', unsafe_allow_html=True)
    with col2:
        st.markdown('<span class="status-dot status-online"></span> DB', unsafe_allow_html=True)
    with col3:
        st.markdown('<span class="status-dot status-online"></span> API', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "",
        ["💬 Chat", "📁 Projects", "🧩 Skills", "📝 Editor", "🔧 Sandbox", "📊 Dashboard"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Saved chats (only on Chat page)
    if page == "💬 Chat":
        st.caption("💾 Saved Chats")
        saved = list_saved_chats()
        if saved:
            for chat_name in saved[:10]:
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    if st.button(f"📄 {chat_name[:30]}", key=f"load_{chat_name}", use_container_width=True):
                        data = load_chat(chat_name)
                        st.session_state.messages = data["messages"]
                        st.session_state.current_chat = chat_name
                        st.rerun()
                with col_b:
                    if st.button("🗑️", key=f"del_{chat_name}"):
                        delete_chat(chat_name)
                        st.rerun()
        else:
            st.caption("No saved chats")
    
    st.markdown("---")
    st.caption("Model: Qwen 3 14B + DeepSeek")
    st.caption("Cost: ~$0.50/month")


# ═══════════════════════════════════════════════════════════
# PAGE: CHAT
# ═══════════════════════════════════════════════════════════
if page == "💬 Chat":
    st.title("💬 Chat")
    
    # Top bar with actions
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col2:
        if st.button("➕ New Chat", use_container_width=True):
            # Save current chat first
            if "messages" in st.session_state and len(st.session_state.messages) > 1:
                chat_name = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                save_chat(chat_name, st.session_state.messages)
            st.session_state.messages = [
                {"role": "assistant", "content": "Welcome to Cowork-Local Pro! I am running Qwen 3 14B on your GPU. How can I help?"}
            ]
            st.session_state.current_chat = None
            st.rerun()
    with col3:
        if st.button("💾 Save", use_container_width=True):
            if "messages" in st.session_state and len(st.session_state.messages) > 1:
                chat_name = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                save_chat(chat_name, st.session_state.messages)
                st.success(f"Saved as {chat_name}")
                st.rerun()
    with col4:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": "Chat cleared. How can I help?"}
            ]
            st.rerun()
    
    st.markdown("---")
    
    # Initialize chat
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome to Cowork-Local Pro! I am running Qwen 3 14B on your GPU. How can I help?"}
        ]
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = None
    
    # Show current chat name
    if st.session_state.current_chat:
        st.caption(f"📄 Chat: {st.session_state.current_chat}")
    
    # Chat messages
    for msg in st.session_state.messages:
        css = "user-msg" if msg["role"] == "user" else "assistant-msg"
        st.markdown(f'<div class="{css}">{msg["content"]}</div>', unsafe_allow_html=True)
    
    # File upload
    with st.expander("📎 Attach files (images, PDF, code, etc.)"):
        uploaded_files = st.file_uploader(
            "Upload files",
            type=["py", "txt", "md", "yaml", "json", "png", "jpg", "jpeg", "gif", "pdf", "xlsx", "csv", "pptx", "docx", "zip"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
    
    # Input area
    query = st.chat_input("Ask me anything... or upload files above")
    
    if query or uploaded_files:
        # Process uploaded files
        file_contents = []
        if uploaded_files:
            for uf in uploaded_files:
                fname, fcontent = process_uploaded_file(uf)
                if fcontent:
                    file_contents.append(fcontent)
        
        # Build message
        full_query = query
        if file_contents:
            full_query += "\n\n---\n**Attached files:**\n" + "\n\n".join(file_contents)
        
        if full_query and full_query.strip():
            st.session_state.messages.append({"role": "user", "content": full_query})
            
            with st.spinner("🧠 Thinking with Qwen 3..."):
                try:
                    from models.qwen_ollama_client import QwenOllamaClient
                    client = QwenOllamaClient(model="qwen3:14b")
                    
                    # Show thinking indicator
                    thinking_placeholder = st.empty()
                    thinking_placeholder.markdown(
                        '<div class="thinking-msg">🤔 Analyzing your request with Qwen 3 14B...</div>',
                        unsafe_allow_html=True
                    )
                    
                    response = client.generate(full_query)
                    
                    thinking_placeholder.empty()
                    
                    # Escapar bloques de código para que Streamlit los muestre bien
                    safe_response = response.replace("```", "'''")
                    st.session_state.messages.append({"role": "assistant", "content": safe_response})
                    st.rerun()
                except Exception as e:
                    thinking_placeholder.empty()
                    st.error(f"Error: {e}")


# ═══════════════════════════════════════════════════════════
# PAGE: PROJECTS
# ═══════════════════════════════════════════════════════════
elif page == "📁 Projects":
    st.title("📁 Projects")
    st.markdown("### Your Projects")
    st.markdown(f"""
    <div class="project-card">
        <strong>cowork-local</strong><br>
        <small>75 files - Active</small><br>
        <code>{str(PROJECT_ROOT)}</code>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
elif page == "🧩 Skills":
    st.title("🧩 Skills Marketplace")
    skills = ["PDF Generator", "Excel Generator", "PowerPoint", "Charts", "Email", "Web Search", "GitHub", "Slack", "Browser", "Notion"]
    for s in skills:
        st.markdown(f'<div class="project-card"><strong>{s}</strong> - Installed</div>', unsafe_allow_html=True)

elif page == "📝 Editor":
    st.title("📝 Markdown Editor")
    col1, col2 = st.columns(2)
    with col1:
        content = st.text_area("Edit", value="# Title\n\nContent here...", height=400, label_visibility="collapsed")
    with col2:
        st.markdown(content)

elif page == "🔧 Sandbox":
    st.title("🔧 Docker Sandbox")
    code = st.text_area("Code", value="print('Hello from sandbox!')", height=200)
    if st.button("Run in Sandbox"):
        with st.spinner("Running..."):
            try:
                from tools.mcp_client import get_mcp_client
                client = get_mcp_client()
                result = client.call_sync("docker_sandbox", "execute_python", {"code": code, "timeout": 30})
                st.code(result, language="text")
            except Exception as e:
                st.error(str(e))

elif page == "📊 Dashboard":
    st.title("📊 System Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Model", "Qwen 3 14B")
    with col2: st.metric("Cost", "$0.50/mo")
    with col3: st.metric("MCP", "13")
    with col4: st.metric("Skills", "10+")

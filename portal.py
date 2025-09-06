# streamlit_app.py
import streamlit as st
import hashlib
import sqlite3
import os
from datetime import datetime, timedelta

# --- Configuração Inicial ---
st.set_page_config(page_title="Portal de Apps", layout="wide")
DATA_DIR = "data"
USER_DB_PATH = os.path.join(DATA_DIR, "users.db")

# --- Funções de Autenticação ---

def hash_password(password: str) -> str:
    """Cria hash seguro da senha"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user_db():
    """Cria o banco de dados e a tabela de usuários se não existirem."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with sqlite3.connect(USER_DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT
            );
        """)
        cur.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cur.fetchone():
            admin_pass = hash_password("adminenge1")
            cur.execute("""
                INSERT INTO users(username, password_hash, created_at)
                VALUES(?, ?, ?)
            """, ("admin", admin_pass, datetime.utcnow().isoformat()))
        con.commit()

def validate_user(username: str, password: str) -> bool:
    """Valida as credenciais do usuário no banco de dados."""
    if not username or not password:
        return False
    
    with sqlite3.connect(USER_DB_PATH) as con:
        cur = con.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        result = cur.fetchone()
        
        if not result:
            return False
        
        password_hash = result[0]
        return hash_password(password) == password_hash

# --- Estilo Visual (Inspirado no Claude UI) ---

CLAUDE_STYLE_CSS = """
<style>
/* Reset e Base */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}
html, body, .stApp {
    background: #0e0e0e !important;
    color: #e0e0e0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
/* Remover o espaçamento padrão do Streamlit no topo/baixo */
main .block-container { 
    padding-top: 0.25rem !important; 
    padding-bottom: 1rem !important; 
}
/* Corrige empurrão causado pelo cabeçalho */
header[data-testid="stHeader"] { background: transparent; }
/* Evita que o conteúdo "escorregue" para baixo em resoluções altas */
div[data-testid="stAppViewContainer"] { min-height: 100dvh; }

/* Scrollbar */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #1a1a1a; }
::-webkit-scrollbar-thumb { background: #3a3a3a; border-radius: 4px; }

/* Página de Login */
.login-container {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 100dvh;
}
/* Estiliza a coluna central do Streamlit para parecer um card */
.login-container div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(2) > div {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 40px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.8);
}
.login-header { text-align: center; margin-bottom: 32px; }
.login-title { font-size: 24px; font-weight: 600; margin-bottom: 8px; color: #fff; }
.login-subtitle { color: #888; font-size: 14px; }
.form-group { margin-bottom: 20px; }
.form-label { display: block; margin-bottom: 8px; font-size: 13px; color: #888; }

/* Estilo dos Inputs */
input[type="text"], input[type="password"] {
    background: #0e0e0e !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 6px !important;
    color: #e0e0e0 !important;
    padding: 12px !important;
}
input:focus {
    outline: none !important;
    border-color: #3a3a3a !important;
    box-shadow: 0 0 0 2px #3a3a3a !important;
}
/* Botões */
.stButton button {
    width: 100%;
    padding: 12px 20px;
    background: #667eea;
    color: white;
    border: 1px solid #667eea;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.2s;
}
.stButton button:hover {
    background: #5a67d8;
    border-color: #5a67d8;
}
.stButton button:focus {
    box-shadow: 0 0 0 2px #5a67d8 !important;
}

/* Header do Portal */
.header-bar {
    background: #141414;
    border-bottom: 1px solid #2a2a2a;
    padding: 12px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 999;
    margin: 0 -1rem 1rem -1rem; /* Ajuste para colar no topo */
}
.header-title { font-size: 16px; font-weight: 600; color: #fff; }
.header-actions .stButton button {
    background: transparent;
    border: 1px solid #3a3a3a;
    padding: 6px 14px;
    font-size: 13px;
    width: auto;
}
.header-actions .stButton button:hover {
    border-color: #e06c75;
    color: #e06c75;
}

/* Portal de Apps */
.portal-content { padding: 0 1rem; }
.portal-header h3 { color: #fff; }
.portal-header p { color: #888; margin-top: -10px; }
.app-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    height: 260px;
    display: flex;
    flex-direction: column;
    transition: all 0.2s;
}
.app-card:hover {
    transform: translateY(-3px);
    border-color: #3a3a3a;
}
.app-icon { font-size: 36px; margin-bottom: 12px; }
.app-card h3 { font-size: 1.2rem; color: #fff; margin-bottom: 8px; }
.app-card p { font-size: 0.9rem; color: #888; line-height: 1.5; flex-grow: 1; }
.app-card a {
    display: inline-block;
    padding: 10px 18px;
    background: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.2s;
}
.app-card a:hover {
    background: #3a3a3a;
    border-color: #4a4a4a;
    color: #fff;
}
</style>
"""

# --- Interface do Portal ---

def show_portal():
    """Exibe o portal de aplicativos com o novo design."""
    st.markdown(CLAUDE_STYLE_CSS, unsafe_allow_html=True)

    # ---------- HEADER ----------
    st.markdown('<div class="header-bar">', unsafe_allow_html=True)
    header_cols = st.columns([0.8, 0.2])
    with header_cols[0]:
        st.markdown('<div class="header-title">🚀 Portal de Análises</div>', unsafe_allow_html=True)
    with header_cols[1]:
        st.markdown('<div class="header-actions">', unsafe_allow_html=True)
        if st.button("Sair", key="logout_button"):
            st.session_state.authenticated = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------- CONTEÚDO DO PORTAL ----------
    st.markdown('<div class="portal-content">', unsafe_allow_html=True)
    
    st.markdown('<div class="portal-header"><h3>Seu portal de aplicativos</h3><p>Acesse as ferramentas de análise de forma rápida e organizada.</p></div>', unsafe_allow_html=True)

    q = st.text_input("Buscar", placeholder="Buscar por nome ou descrição...", label_visibility="collapsed").strip().lower()

    # ---------- DADOS DOS APPS ----------
    APPS = [
        {"name": "TG/ADT Events", "desc": "Análise de eventos térmicos em TG/ADT.", "emoji": "🔥", "url": "https://apptgadtgeventspy-hqeqt7yljzwra3r7nmdhju.streamlit.app/"},
        {"name": "Stack Graph", "desc": "Criação de gráficos empilhados.", "emoji": "📊", "url": "https://appstackgraphpy-ijew8pyut2jkc4x4pa7nbv.streamlit.app/"},
        {"name": "Rheology App", "desc": "Análise de dados de reologia.", "emoji": "🔄", "url": "https://apprheologyapppy-mbkr3wmbdb76t3ysvlfecr.streamlit.app/"},
        {"name": "Mechanical Properties", "desc": "Cálculo de propriedades mecânicas.", "emoji": "⚙️", "url": "https://appmechanicalpropertiespy-79l8dejt9kfmmafantscut.streamlit.app/"},
        {"name": "Baseline Smoothing", "desc": "Suavização de linha de base em gráficos.", "emoji": "📈", "url": "https://appbaselinesmoothinglineplotpy-mvx5cnwr5szg4ghwpbx379.streamlit.app/"},
        {"name": "Isotherms App", "desc": "Análise de isotermas de adsorção.", "emoji": "🌡️", "url": "https://isothermsappfixedpy-ropmkqgbbxujhvkd6pfxgi.streamlit.app/"},
        {"name": "Histograms", "desc": "Geração de histogramas customizados.", "emoji": "📶", "url": "https://apphistogramspy-b3kfy7atbdhgxx8udeduma.streamlit.app/"},
        {"name": "Column 3D Line", "desc": "Visualização de dados em 3D com linhas.", "emoji": "🌐", "url": "https://column3dpyline2inmoduleimportdash-kdqhfwwyyhdtb48x4z3kkn.streamlit.app/"},
        {"name": "Crystallinity DSC/XRD", "desc": "Cálculo de cristalinidade por DSC e XRD.", "emoji": "💎", "url": "https://appcrystallinitydscxrdpy-wqtymsdcco2nuem7fv3hve.streamlit.app/"},
        {"name": "Column 3D", "desc": "Visualização de dados em colunas 3D.", "emoji": "🏛️", "url": "https://column3dpy-cskafquxluvyv23hbnhxli.streamlit.app/"},
        {"name": "Kinetic Models", "desc": "Ajuste de modelos cinéticos.", "emoji": "⚗️", "url": "https://kineticmodelsapppy-fz8qyt64fahje5acofqpcm.streamlit.app/"},
        {"name": "Python Launcher", "desc": "Executor de scripts Python online.", "emoji": "🐍", "url": "https://pythonlauncherfixedpy-yschqh6qwzl526xurdeoca.streamlit.app/"},
    ]
    apps_filtrados = [a for a in APPS if q in a["name"].lower() or q in a["desc"].lower()] if q else APPS

    # ---------- RENDERIZAÇÃO DOS CARDS ----------
    if apps_filtrados:
        cols = st.columns(3)
        for i, app in enumerate(apps_filtrados):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="app-card">
                    <div class="app-icon">{app['emoji']}</div>
                    <h3>{app['name']}</h3>
                    <p>{app['desc']}</p>
                    <a href="{app['url']}" target="_blank" rel="noopener">Abrir →</a>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Nenhum aplicativo encontrado para o termo buscado.")
    
    st.markdown('</div>', unsafe_allow_html=True)


# --- Página de Login ---

def show_login_page():
    """Exibe a página de login com o novo design e posicionamento corrigido."""
    st.markdown(CLAUDE_STYLE_CSS, unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Colunas para centralizar o card de login na tela
    _, center_col, _ = st.columns([1, 1.5, 1])

    with center_col:
        # O CSS irá estilizar esta coluna para que pareça um card
        st.markdown('<div class="login-header"><h1 class="login-title">🚀 Acesso ao Portal</h1><p class="login-subtitle">Entre com suas credenciais para continuar</p></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-group"><span class="form-label">Usuário</span>', unsafe_allow_html=True)
        username = st.text_input("Usuário", key="login_username", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-group"><span class="form-label">Senha</span>', unsafe_allow_html=True)
        password = st.text_input("Senha", type="password", key="login_password", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("Entrar", use_container_width=True):
            if validate_user(username, password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
    
    st.markdown('</div>', unsafe_allow_html=True)


# --- Lógica Principal ---

def main():
    """Função principal que controla qual página exibir."""
    create_user_db()

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        show_portal()
    else:
        show_login_page()

if __name__ == "__main__":
    main()


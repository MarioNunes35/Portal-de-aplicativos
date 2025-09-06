# streamlit_app.py
import streamlit as st
import hashlib
import sqlite3
import os
from datetime import datetime, timedelta

# --- Configuração Inicial ---
st.set_page_config(page_title="Portal de Apps", layout="wide", initial_sidebar_state="collapsed")
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

# --- Estilo Visual (baseado no seu app que funciona) ---

PORTAL_STYLE_CSS = """
<style>
.stApp {
  background:
    radial-gradient(1200px 500px at 20% -10%, rgba(99,102,241,0.25), transparent 40%),
    radial-gradient(1000px 450px at 90% 10%, rgba(45,212,191,0.22), transparent 40%),
    linear-gradient(180deg, #121317 0%, #0f1116 100%) !important;
  color: #EAEAF1;
}

/* Header fixo */
.nav { 
  position: sticky; top: 0; z-index: 20; padding: 14px 22px; margin: -1.2rem -1rem 0 -1rem;
  backdrop-filter: blur(8px); background: rgba(255,255,255,0.06);
  border-bottom: 1px solid rgba(255,255,255,0.12); 
  display: flex; justify-content: space-between; align-items: center;
}
.brand { 
  font-weight: 700; font-size: 1.05rem; letter-spacing: .02em; 
  display: flex; align-items: center; gap: 12px;
}

/* Inputs */
.block-container input[type="text"]{
  background: rgba(255,255,255,0.08) !important; 
  border: 1px solid rgba(255,255,255,0.20) !important;
  border-radius: 999px !important; 
  color: #fff !important;
  padding: 16px 20px !important;
  font-size: 16px !important;
}
.block-container .stTextInput > div > div{ 
  border-radius: 999px !important; 
}

/* Cards dos apps */
.card{ 
  position: relative; overflow: hidden; padding: 28px 24px 22px 24px; border-radius: 20px;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.18);
  box-shadow: 0 10px 30px rgba(0,0,0,0.35);
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease; 
  margin-bottom: 28px;
  height: 320px;
  display: flex;
  flex-direction: column;
}
.card:hover{ 
  transform: translateY(-2px); 
  box-shadow: 0 16px 40px rgba(0,0,0,0.45); 
  border-color: rgba(255,255,255,0.28); 
}
.card .accent{ 
  position: absolute; left: 0; top: 0; bottom: 0; width: 4px; 
}
.icon{ 
  width: 72px; height: 72px; border-radius: 50%; display: flex; 
  align-items: center; justify-content: center;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.20); 
  font-size: 32px; margin-bottom: 16px; 
}
.card h3{ 
  margin: 6px 0 8px 0; font-size: 1.25rem; color: #fff; font-weight: 600;
}
.card p{ 
  margin: 0 0 16px 0; color: #CBD5E1; line-height: 1.4; 
  flex-grow: 1;
}
.actions{ 
  display: flex; gap: 12px; align-items: center; margin-top: auto; 
}
.btn{ 
  padding: 12px 20px; border-radius: 12px; background: rgba(255,255,255,0.10);
  border: 1px solid rgba(255,255,255,0.22); color: #fff; text-decoration: none; 
  font-weight: 600; font-size: 14px;
  transition: background .15s ease, border-color .15s ease, transform .15s ease;
  display: inline-block; text-align: center;
}
.btn:hover{ 
  background: rgba(255,255,255,0.16); 
  border-color: rgba(255,255,255,0.32); 
  transform: translateY(-1px); 
}

/* Títulos */
h1, h2, h3{ 
  color: #fff; 
} 
.subtitle{ 
  color: #CBD5E1; margin-top: -6px; 
}

/* Responsividade */
.stColumn > div {
  padding-left: 0.5rem !important;
  padding-right: 0.5rem !important;
}

/* Botão de logout */
.logout-btn {
  background: rgba(239, 68, 68, 0.1) !important;
  border: 1px solid rgba(239, 68, 68, 0.3) !important;
  color: #ef4444 !important;
  padding: 8px 16px !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  transition: all 0.2s !important;
}
.logout-btn:hover {
  background: rgba(239, 68, 68, 0.2) !important;
  border-color: rgba(239, 68, 68, 0.5) !important;
}

/* LOGIN FORM */
.login-container {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 20px;
}

[data-testid="stForm"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    border-radius: 20px !important;
    padding: 24px !important;
    box-shadow: 0 20px 60px rgba(0,0,0,0.4) !important;
    backdrop-filter: blur(10px) !important;
    width: min(400px, 90vw) !important;
    max-height: 70vh !important;
    position: fixed !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    z-index: 1000 !important;
}

.login-title {
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #fff !important;
    margin-bottom: 4px !important;
    text-align: center !important;
}

.login-subtitle {
    color: #CBD5E1 !important;
    font-size: 14px !important;
    text-align: center !important;
    margin-bottom: 20px !important;
}

/* Inputs do login */
.login-container input[type="text"],
.login-container input[type="password"] {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.20) !important;
    border-radius: 12px !important;
    color: #fff !important;
    padding: 16px 20px !important;
    font-size: 16px !important;
    height: 56px !important;
}

.login-container input[type="text"]:focus,
.login-container input[type="password"]:focus {
    border-color: rgba(99,102,241,0.5) !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.1) !important;
}

/* Botão de login */
.login-container .stButton > button {
    width: 100% !important;
    padding: 16px 24px !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    height: 56px !important;
    margin-top: 24px !important;
    transition: all 0.2s !important;
}

.login-container .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3) !important;
}
</style>
"""

# --- Página de Login ---

def show_login_page():
    """Exibe a página de login."""
    st.markdown(PORTAL_STYLE_CSS, unsafe_allow_html=True)
    
    with st.form("login_form", clear_on_submit=False):
        st.markdown('<h1 class="login-title">🚀 Portal de Análises</h1>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">Entre com suas credenciais para continuar</p>', unsafe_allow_html=True)

        username = st.text_input("Usuário", placeholder="Digite seu usuário", key="login_username")
        password = st.text_input("Senha", type="password", placeholder="Digite sua senha", key="login_password")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            remember = st.checkbox("Lembrar-me", value=True)
        with col2:
            show_pwd = st.checkbox("Mostrar senha")
            
        if show_pwd:
            password = st.text_input("Senha visível", value=password, placeholder="Digite sua senha", key="login_password_visible")
        
        submitted = st.form_submit_button("Entrar")

    if submitted:
        if not username or not password:
            st.error("❌ Preencha usuário e senha.")
        else:
            if validate_user(username, password):
                st.session_state.authenticated = True
                st.session_state["current_user"] = username
                if remember:
                    st.session_state["remember_me"] = True
                st.success("✅ Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")


def show_portal():
    """Exibe o portal de aplicativos."""
    st.markdown(PORTAL_STYLE_CSS, unsafe_allow_html=True)
    
    # Header com logout (seguindo o padrão do seu app)
    st.markdown('''
    <div class="nav">
        <span class="brand">
            <span>🚀</span>
            <span>Portal de Análises</span>
        </span>
    </div>
    ''', unsafe_allow_html=True)
    
    # Botão de logout posicionado no canto superior direito
    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button("Sair", key="logout", help="Fazer logout"):
            st.session_state.authenticated = False
            st.rerun()
    
    # Título e descrição
    st.markdown("### Seus aplicativos")
    st.markdown('<p class="subtitle">Acesse as ferramentas de análise de forma rápida e organizada</p>', unsafe_allow_html=True)
    
    # Busca
    search_query = st.text_input("Buscar", placeholder="🔍 Buscar aplicativos...", label_visibility="collapsed")
    
    # Lista de aplicativos
    APPS = [
        {
            "name": "TG/ADT Events",
            "desc": "Análise de eventos térmicos em TG/ADT com identificação automática de picos e eventos.",
            "emoji": "🔥",
            "url": "https://apptgadtgeventspy-hqeqt7yljzwra3r7nmdhju.streamlit.app/",
            "accent": "linear-gradient(180deg, #ef4444, #dc2626)",
        },
        {
            "name": "Stack Graph", 
            "desc": "Criação de gráficos empilhados para visualização de dados multidimensionais.",
            "emoji": "📊",
            "url": "https://appstackgraphpy-ijew8pyut2jkc4x4pa7nbv.streamlit.app/",
            "accent": "linear-gradient(180deg, #3b82f6, #1d4ed8)",
        },
        {
            "name": "Rheology App",
            "desc": "Análise completa de dados de reologia com ajuste de modelos viscoelásticos.",
            "emoji": "🔄",
            "url": "https://apprheologyapppy-mbkr3wmbdb76t3ysvlfecr.streamlit.app/",
            "accent": "linear-gradient(180deg, #8b5cf6, #7c3aed)",
        },
        {
            "name": "Mechanical Properties",
            "desc": "Cálculo de propriedades mecânicas e análise de tensão-deformação.",
            "emoji": "⚙️",
            "url": "https://appmechanicalpropertiespy-79l8dejt9kfmmafantscut.streamlit.app/",
            "accent": "linear-gradient(180deg, #6b7280, #4b5563)",
        },
        {
            "name": "Baseline Smoothing",
            "desc": "Suavização de linha de base em gráficos com algoritmos avançados.",
            "emoji": "📈",
            "url": "https://appbaselinesmoothinglineplotpy-mvx5cnwr5szg4ghwpbx379.streamlit.app/",
            "accent": "linear-gradient(180deg, #10b981, #059669)",
        },
        {
            "name": "Isotherms App",
            "desc": "Análise de isotermas de adsorção com modelos de Langmuir e Freundlich.",
            "emoji": "🌡️",
            "url": "https://isothermsappfixedpy-ropmkqgbbxujhvkd6pfxgi.streamlit.app/",
            "accent": "linear-gradient(180deg, #f59e0b, #d97706)",
        },
        {
            "name": "Histograms",
            "desc": "Geração de histogramas customizados com análise estatística completa.",
            "emoji": "📶",
            "url": "https://apphistogramspy-b3kfy7atbdhgxx8udeduma.streamlit.app/",
            "accent": "linear-gradient(180deg, #ec4899, #db2777)",
        },
        {
            "name": "Column 3D Line",
            "desc": "Visualização de dados em 3D com projeções e rotação interativa.",
            "emoji": "🌐",
            "url": "https://column3dpyline2inmoduleimportdash-kdqhfwwyyhdtb48x4z3kkn.streamlit.app/",
            "accent": "linear-gradient(180deg, #06b6d4, #0891b2)",
        },
        {
            "name": "Crystallinity DSC/XRD",
            "desc": "Cálculo de cristalinidade por DSC e XRD com análise comparativa.",
            "emoji": "💎",
            "url": "https://appcrystallinitydscxrdpy-wqtymsdcco2nuem7fv3hve.streamlit.app/",
            "accent": "linear-gradient(180deg, #a855f7, #9333ea)",
        },
        {
            "name": "Column 3D",
            "desc": "Visualização de dados em colunas 3D com mapeamento de cores.",
            "emoji": "🏛️",
            "url": "https://column3dpy-cskafquxluvyv23hbnhxli.streamlit.app/",
            "accent": "linear-gradient(180deg, #84cc16, #65a30d)",
        },
        {
            "name": "Kinetic Models",
            "desc": "Ajuste de modelos cinéticos com otimização de parâmetros.",
            "emoji": "⚗️",
            "url": "https://kineticmodelsapppy-fz8qyt64fahje5acofqpcm.streamlit.app/",
            "accent": "linear-gradient(180deg, #f97316, #ea580c)",
        },
        {
            "name": "Python Launcher",
            "desc": "Executor de scripts Python online com ambiente isolado.",
            "emoji": "🐍",
            "url": "https://pythonlauncherfixedpy-yschqh6qwzl526xurdeoca.streamlit.app/",
            "accent": "linear-gradient(180deg, #facc15, #eab308)",
        },
    ]
    
    # Filtrar apps
    query = search_query.lower().strip() if search_query else ""
    filtered_apps = [app for app in APPS if query in app["name"].lower() or query in app["desc"].lower()] if query else APPS
    
    # Renderizar cards
    if filtered_apps:
        cols = st.columns(3, gap="large")
        
        for i, app in enumerate(filtered_apps):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="card">
                    <div class="accent" style="background:{app['accent']};"></div>
                    <div class="icon">{app['emoji']}</div>
                    <h3>{app['name']}</h3>
                    <p>{app['desc']}</p>
                    <div class="actions">
                        <a class="btn" href="{app['url']}" target="_blank" rel="noopener">Abrir aplicativo →</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("🔍 Nenhum aplicativo encontrado para o termo buscado.")


# --- Lógica Principal ---

def main():
    """Função principal que controla qual página exibir."""
    # Criar banco de dados
    create_user_db()
    
    # Inicializar estado de autenticação
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Exibir página apropriada
    if st.session_state.authenticated:
        show_portal()
    else:
        show_login_page()

if __name__ == "__main__":
    main()












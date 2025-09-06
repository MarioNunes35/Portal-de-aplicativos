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

# --- Estilo Visual ---

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
    height: 100vh;
    overflow-x: hidden;
}

/* IMPORTANTE: Remover todos os paddings padrão do Streamlit */
.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
    height: 100vh !important;
}

.main {
    padding: 0 !important;
    margin: 0 !important;
}

/* Remover header e footer do Streamlit */
header[data-testid="stHeader"] {
    display: none !important;
}

footer {
    display: none !important;
}

/* Remover sidebar */
section[data-testid="stSidebar"] {
    display: none !important;
}

/* Container principal ocupando toda a tela */
div[data-testid="stAppViewContainer"] {
    padding-top: 0 !important;
}

.stApp > div:first-child {
    height: 100vh;
    overflow: hidden;
}

/* Scrollbar */
::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-track { background: #1a1a1a; }
::-webkit-scrollbar-thumb { background: #3a3a3a; border-radius: 4px; }

/* ================ PÁGINA DE LOGIN ================ */
.login-container {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100vw;
    height: 100vh;
    position: fixed;
    top: 0;
    left: 0;
    background: #0e0e0e;
}

.login-box {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 16px;
    padding: 60px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.8);
    width: 90%;
    max-width: 500px;
}

.login-title {
    text-align: center;
    margin-bottom: 50px;
}

.login-title h1 {
    font-size: 42px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
}

.login-title p {
    color: #888;
    font-size: 18px;
}

.login-form-label {
    display: block;
    margin-bottom: 10px;
    margin-top: 30px;
    font-size: 16px;
    color: #888;
    font-weight: 500;
}

/* Inputs de login maiores */
.login-container .stTextInput > div > div > input {
    background: #0e0e0e !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #e0e0e0 !important;
    padding: 18px 20px !important;
    font-size: 16px !important;
    height: 56px !important;
}

.login-container .stTextInput > div > div > input:focus {
    outline: none !important;
    border-color: #667eea !important;
    box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1) !important;
}

/* Botão de login maior */
.login-container .stButton > button {
    width: 100%;
    padding: 18px 30px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 18px;
    font-weight: 600;
    height: 56px;
    margin-top: 35px;
    transition: all 0.2s;
    cursor: pointer;
}

.login-container .stButton > button:hover {
    background: #5a67d8;
    transform: translateY(-1px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

/* ================ PÁGINA DO PORTAL ================ */
.portal-container {
    width: 100vw;
    height: 100vh;
    position: fixed;
    top: 0;
    left: 0;
    display: flex;
    flex-direction: column;
    background: #0e0e0e;
}

/* Header fixo no topo */
.portal-header {
    background: #141414;
    border-bottom: 1px solid #2a2a2a;
    padding: 20px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    height: 80px;
}

.portal-logo {
    font-size: 24px;
    font-weight: 700;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 12px;
}

.portal-header .stButton > button {
    background: transparent;
    border: 1px solid #3a3a3a;
    padding: 10px 20px;
    font-size: 15px;
    color: #888;
    border-radius: 6px;
    transition: all 0.2s;
    height: auto;
}

.portal-header .stButton > button:hover {
    border-color: #e06c75;
    color: #e06c75;
    background: rgba(224, 108, 117, 0.1);
}

/* Área de conteúdo com scroll */
.portal-main {
    margin-top: 80px;
    height: calc(100vh - 80px);
    overflow-y: auto;
    padding: 40px;
}

.content-header {
    margin-bottom: 40px;
}

.content-header h1 {
    font-size: 32px;
    color: #fff;
    margin-bottom: 10px;
    font-weight: 600;
}

.content-header p {
    font-size: 18px;
    color: #888;
}

/* Barra de busca maior */
.search-box .stTextInput > div > div > input {
    background: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
    color: #e0e0e0 !important;
    padding: 16px 20px !important;
    font-size: 16px !important;
    margin-bottom: 30px;
    height: 52px !important;
}

.search-box .stTextInput > div > div > input::placeholder {
    color: #666 !important;
}

/* Cards maiores */
.app-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 14px;
    padding: 32px;
    margin-bottom: 24px;
    height: 320px;
    display: flex;
    flex-direction: column;
    transition: all 0.2s;
    cursor: pointer;
}

.app-card:hover {
    transform: translateY(-4px);
    border-color: #3a3a3a;
    box-shadow: 0 12px 30px rgba(0,0,0,0.5);
}

.app-icon {
    font-size: 48px;
    margin-bottom: 20px;
}

.app-card h3 {
    font-size: 20px;
    color: #fff;
    margin-bottom: 12px;
    font-weight: 600;
}

.app-card p {
    font-size: 15px;
    color: #888;
    line-height: 1.6;
    flex-grow: 1;
}

.app-card a {
    display: inline-block;
    padding: 12px 24px;
    background: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    font-size: 15px;
    transition: all 0.2s;
    text-align: center;
}

.app-card a:hover {
    background: #667eea;
    border-color: #667eea;
    color: #fff;
    transform: translateX(2px);
}

/* Mensagens de erro */
.stAlert {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 8px;
    padding: 16px;
    margin-top: 20px;
    font-size: 15px;
}

/* Remover elementos desnecessários */
.stDeployButton,
div[data-testid="stDecoration"],
div[data-testid="stToolbar"] {
    display: none !important;
}

/* Ajuste para centralização vertical */
.element-container:has(.login-container) {
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Responsividade */
@media (max-width: 768px) {
    .login-box {
        padding: 40px 30px;
        width: 95%;
    }
    
    .login-title h1 {
        font-size: 32px;
    }
    
    .portal-header {
        padding: 15px 20px;
    }
    
    .portal-main {
        padding: 20px;
    }
    
    .app-card {
        height: auto;
        min-height: 280px;
    }
}
</style>
"""

# --- Página de Login ---

def show_login_page():
    """Exibe a página de login centralizada (form Streamlit no centro)."""
    # Mantém o CSS global do app
    st.markdown(CLAUDE_STYLE_CSS, unsafe_allow_html=True)

    # CSS específico para centralizar o st.form e dar aparência de "login-box"
    st.markdown(
        """
        <style>
        [data-testid="stForm"] {
            display:inline-block !important;
            height:auto !important;
            min-height: 0 !important;
            position: fixed !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            width: min(560px, 92vw);
            z-index: 999;
            margin: 0 !important;
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 16px;
            padding: 36px 34px 28px 34px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.8);
        }
        .login-title-h1 { font-size: 40px; line-height: 1.1; margin: 0 0 2px 0; }
        .login-sub { color:#9aa0a6; font-size: 18px; margin: 2px 0 22px 0; }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.form("login_form", clear_on_submit=False):
        st.markdown('<h1 class="login-title-h1">🚀 Acesso ao<br>Portal</h1>', unsafe_allow_html=True)
        st.markdown('<p class="login-sub">Entre com suas credenciais para continuar</p>', unsafe_allow_html=True)

        col1, col2 = st.columns([1,1])
        with col1:
            username = st.text_input("Usuário ou e-mail", placeholder="seunome@exemplo.com", key="login_username")
        with col2:
            show_pwd = st.toggle("Mostrar senha", value=False, key="login_showpwd")
        password = st.text_input("Senha", type=("text" if show_pwd else "password"),
                                 placeholder="••••••••", key="login_password")
        remember = st.checkbox("Lembrar-me", value=True, key="login_remember")
        submitted = st.form_submit_button("Entrar", use_container_width=True)

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
    
    # Correção de espaçamento: aproxima o conteúdo do topo
    st.markdown(
        """
        <style>
        .portal-container{ position: static !important; height: auto !important; min-height: 100vh !important; }
        .portal-main{ margin-top: 80px !important; height: auto !important; padding-top: 8px !important; }
        </style>
        """,
        unsafe_allow_html=True
    )
"""Exibe o portal de aplicativos."""
    # Aplicar CSS
    st.markdown(CLAUDE_STYLE_CSS, unsafe_allow_html=True)
    
    # Container do portal
    st.markdown('<div class="portal-container">', unsafe_allow_html=True)
    
    # Header fixo
    st.markdown("""
    <div class="portal-header">
        <div class="portal-logo">
            <span>🚀</span>
            <span>Portal de Análises</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão de logout no header
    with st.container():
        col1, col2 = st.columns([10, 1])
        with col2:
            if st.button("Sair", key="logout"):
                st.session_state.authenticated = False
                st.rerun()
    
    # Área principal com scroll
    st.markdown('<div class="portal-main">', unsafe_allow_html=True)
    
    # Cabeçalho do conteúdo
    st.markdown("""
    <div class="content-header">
        <h1>Seus aplicativos</h1>
        <p>Acesse as ferramentas de análise de forma rápida e organizada</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Barra de busca
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    search_query = st.text_input("search", placeholder="🔍 Buscar por nome ou descrição...", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Lista de aplicativos
    APPS = [
        {
            "name": "TG/ADT Events",
            "desc": "Análise de eventos térmicos em TG/ADT com identificação automática de picos e eventos.",
            "emoji": "🔥",
            "url": "https://apptgadtgeventspy-hqeqt7yljzwra3r7nmdhju.streamlit.app/"
        },
        {
            "name": "Stack Graph",
            "desc": "Criação de gráficos empilhados para visualização de dados multidimensionais.",
            "emoji": "📊",
            "url": "https://appstackgraphpy-ijew8pyut2jkc4x4pa7nbv.streamlit.app/"
        },
        {
            "name": "Rheology App",
            "desc": "Análise completa de dados de reologia com ajuste de modelos viscoelásticos.",
            "emoji": "🔄",
            "url": "https://apprheologyapppy-mbkr3wmbdb76t3ysvlfecr.streamlit.app/"
        },
        {
            "name": "Mechanical Properties",
            "desc": "Cálculo de propriedades mecânicas e análise de tensão-deformação.",
            "emoji": "⚙️",
            "url": "https://appmechanicalpropertiespy-79l8dejt9kfmmafantscut.streamlit.app/"
        },
        {
            "name": "Baseline Smoothing",
            "desc": "Suavização de linha de base em gráficos com algoritmos avançados.",
            "emoji": "📈",
            "url": "https://appbaselinesmoothinglineplotpy-mvx5cnwr5szg4ghwpbx379.streamlit.app/"
        },
        {
            "name": "Isotherms App",
            "desc": "Análise de isotermas de adsorção com modelos de Langmuir e Freundlich.",
            "emoji": "🌡️",
            "url": "https://isothermsappfixedpy-ropmkqgbbxujhvkd6pfxgi.streamlit.app/"
        },
        {
            "name": "Histograms",
            "desc": "Geração de histogramas customizados com análise estatística completa.",
            "emoji": "📶",
            "url": "https://apphistogramspy-b3kfy7atbdhgxx8udeduma.streamlit.app/"
        },
        {
            "name": "Column 3D Line",
            "desc": "Visualização de dados em 3D com projeções e rotação interativa.",
            "emoji": "🌐",
            "url": "https://column3dpyline2inmoduleimportdash-kdqhfwwyyhdtb48x4z3kkn.streamlit.app/"
        },
        {
            "name": "Crystallinity DSC/XRD",
            "desc": "Cálculo de cristalinidade por DSC e XRD com análise comparativa.",
            "emoji": "💎",
            "url": "https://appcrystallinitydscxrdpy-wqtymsdcco2nuem7fv3hve.streamlit.app/"
        },
        {
            "name": "Column 3D",
            "desc": "Visualização de dados em colunas 3D com mapeamento de cores.",
            "emoji": "🏛️",
            "url": "https://column3dpy-cskafquxluvyv23hbnhxli.streamlit.app/"
        },
        {
            "name": "Kinetic Models",
            "desc": "Ajuste de modelos cinéticos com otimização de parâmetros.",
            "emoji": "⚗️",
            "url": "https://kineticmodelsapppy-fz8qyt64fahje5acofqpcm.streamlit.app/"
        },
        {
            "name": "Python Launcher",
            "desc": "Executor de scripts Python online com ambiente isolado.",
            "emoji": "🐍",
            "url": "https://pythonlauncherfixedpy-yschqh6qwzl526xurdeoca.streamlit.app/"
        },
    ]
    
    # Filtrar apps
    query = search_query.lower().strip() if search_query else ""
    filtered_apps = [app for app in APPS if query in app["name"].lower() or query in app["desc"].lower()] if query else APPS
    
    # Renderizar cards
    if filtered_apps:
        # Grid de 3 colunas
        cols = st.columns(3, gap="large")
        
        for i, app in enumerate(filtered_apps):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="app-card">
                    <div class="app-icon">{app['emoji']}</div>
                    <h3>{app['name']}</h3>
                    <p>{app['desc']}</p>
                    <a href="{app['url']}" target="_blank" rel="noopener">Abrir aplicativo →</a>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("🔍 Nenhum aplicativo encontrado para o termo buscado.")
    
    st.markdown('</div>', unsafe_allow_html=True)  # Fecha portal-main
    st.markdown('</div>', unsafe_allow_html=True)  # Fecha portal-container

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







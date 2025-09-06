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

/* Remover espaçamentos do Streamlit */
.main .block-container {
    padding-top: 2rem !important;
    padding-bottom: 0 !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: none !important;
}

/* Remover header do Streamlit */
header[data-testid="stHeader"] {
    display: none !important;
}

/* Container principal */
div[data-testid="stAppViewContainer"] {
    min-height: 100vh;
}

/* Scrollbar */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #1a1a1a; }
::-webkit-scrollbar-thumb { background: #3a3a3a; border-radius: 4px; }

/* PÁGINA DE LOGIN */
.login-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 4rem);
    padding: 20px;
}

.login-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 40px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.8);
    width: 100%;
    max-width: 400px;
    margin: 0 auto;
}

.login-header { 
    text-align: center; 
    margin-bottom: 32px; 
}

.login-title { 
    font-size: 28px; 
    font-weight: 600; 
    margin-bottom: 8px; 
    color: #fff; 
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}

.login-subtitle { 
    color: #888; 
    font-size: 14px; 
}

.form-label { 
    display: block; 
    margin-bottom: 8px; 
    margin-top: 20px;
    font-size: 13px; 
    color: #888; 
    font-weight: 500;
}

/* Estilo dos Inputs do Streamlit */
.stTextInput > div > div > input {
    background: #0e0e0e !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 6px !important;
    color: #e0e0e0 !important;
    padding: 12px !important;
    font-size: 14px !important;
}

.stTextInput > div > div > input:focus {
    outline: none !important;
    border-color: #667eea !important;
    box-shadow: 0 0 0 1px #667eea !important;
}

/* Botões */
.login-card .stButton > button {
    width: 100%;
    padding: 12px 20px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.2s;
    margin-top: 24px;
}

.login-card .stButton > button:hover {
    background: #5a67d8;
}

/* Mensagens de erro */
.stAlert {
    margin-top: 20px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 6px;
}

/* PÁGINA DO PORTAL */
.portal-wrapper {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Header do Portal */
.header-bar {
    background: #141414;
    border-bottom: 1px solid #2a2a2a;
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: -2rem -1rem 0 -1rem;
    width: calc(100% + 2rem);
}

.header-title { 
    font-size: 18px; 
    font-weight: 600; 
    color: #fff; 
    display: flex;
    align-items: center;
    gap: 10px;
}

.header-bar .stButton > button {
    background: transparent;
    border: 1px solid #3a3a3a;
    padding: 6px 14px;
    font-size: 13px;
    color: #888;
    transition: all 0.2s;
}

.header-bar .stButton > button:hover {
    border-color: #e06c75;
    color: #e06c75;
    background: rgba(224, 108, 117, 0.1);
}

/* Conteúdo do Portal */
.portal-content { 
    padding: 30px 24px;
}

.portal-header {
    margin-bottom: 30px;
}

.portal-header h2 { 
    color: #fff; 
    font-size: 1.8rem;
    margin-bottom: 8px;
}

.portal-header p { 
    color: #888; 
    font-size: 0.95rem;
}

/* Barra de busca */
.search-container .stTextInput > div > div > input {
    background: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #e0e0e0 !important;
    padding: 12px 16px !important;
    font-size: 14px !important;
}

/* Cards dos Apps */
.app-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    height: 280px;
    display: flex;
    flex-direction: column;
    transition: all 0.2s;
    cursor: pointer;
}

.app-card:hover {
    transform: translateY(-3px);
    border-color: #3a3a3a;
    box-shadow: 0 8px 20px rgba(0,0,0,0.4);
}

.app-icon { 
    font-size: 40px; 
    margin-bottom: 16px; 
}

.app-card h3 { 
    font-size: 1.1rem; 
    color: #fff; 
    margin-bottom: 10px; 
    font-weight: 600;
}

.app-card p { 
    font-size: 0.9rem; 
    color: #888; 
    line-height: 1.5; 
    flex-grow: 1; 
}

.app-card a {
    display: inline-block;
    padding: 10px 18px;
    background: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 600;
    font-size: 13px;
    transition: all 0.2s;
    text-align: center;
}

.app-card a:hover {
    background: #667eea;
    border-color: #667eea;
    color: #fff;
}

/* Ocultar elementos desnecessários do Streamlit */
.stDeployButton, 
div[data-testid="stDecoration"],
footer {
    display: none !important;
}

/* Responsividade */
@media (max-width: 768px) {
    .header-bar {
        padding: 12px 16px;
    }
    
    .portal-content {
        padding: 20px 16px;
    }
    
    .app-card {
        height: auto;
        min-height: 250px;
    }
}
</style>
"""

# --- Página de Login ---

def show_login_page():
    """Exibe a página de login."""
    st.markdown(CLAUDE_STYLE_CSS, unsafe_allow_html=True)
    
    # Container centralizado
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    
    # Criar colunas para centralizar o card
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('''
        <div class="login-card">
            <div class="login-header">
                <div class="login-title">
                    <span>🚀</span>
                    <span>Acesso ao Portal</span>
                </div>
                <p class="login-subtitle">Entre com suas credenciais para continuar</p>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Adicionar espaço antes dos campos
        st.markdown('<div style="margin-top: -20px;"></div>', unsafe_allow_html=True)
        
        # Campo de usuário
        st.markdown('<p class="form-label">Usuário</p>', unsafe_allow_html=True)
        username = st.text_input("Usuario", key="login_username", label_visibility="collapsed", placeholder="Digite seu usuário")
        
        # Campo de senha
        st.markdown('<p class="form-label">Senha</p>', unsafe_allow_html=True)
        password = st.text_input("Senha", type="password", key="login_password", label_visibility="collapsed", placeholder="Digite sua senha")
        
        # Botão de login
        if st.button("Entrar", use_container_width=True, type="primary"):
            if validate_user(username, password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Interface do Portal ---

def show_portal():
    """Exibe o portal de aplicativos."""
    st.markdown(CLAUDE_STYLE_CSS, unsafe_allow_html=True)
    
    # Container wrapper
    st.markdown('<div class="portal-wrapper">', unsafe_allow_html=True)
    
    # Header
    st.markdown('''
    <div class="header-bar">
        <div class="header-title">
            <span>🚀</span>
            <span>Portal de Análises</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Botão de logout posicionado no canto
    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button("Sair", key="logout_button"):
            st.session_state.authenticated = False
            st.rerun()
    
    # Conteúdo do portal
    st.markdown('<div class="portal-content">', unsafe_allow_html=True)
    
    # Cabeçalho
    st.markdown('''
    <div class="portal-header">
        <h2>Seus aplicativos</h2>
        <p>Acesse as ferramentas de análise de forma rápida e organizada</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Barra de busca
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    search_query = st.text_input("Buscar", placeholder="🔍 Buscar por nome ou descrição...", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Lista de aplicativos
    APPS = [
        {"name": "TG/ADT Events", "desc": "Análise de eventos térmicos em TG/ADT com identificação automática de picos.", "emoji": "🔥", "url": "https://apptgadtgeventspy-hqeqt7yljzwra3r7nmdhju.streamlit.app/"},
        {"name": "Stack Graph", "desc": "Criação de gráficos empilhados para visualização de dados multidimensionais.", "emoji": "📊", "url": "https://appstackgraphpy-ijew8pyut2jkc4x4pa7nbv.streamlit.app/"},
        {"name": "Rheology App", "desc": "Análise completa de dados de reologia com ajuste de modelos.", "emoji": "🔄", "url": "https://apprheologyapppy-mbkr3wmbdb76t3ysvlfecr.streamlit.app/"},
        {"name": "Mechanical Properties", "desc": "Cálculo de propriedades mecânicas e análise de tensão-deformação.", "emoji": "⚙️", "url": "https://appmechanicalpropertiespy-79l8dejt9kfmmafantscut.streamlit.app/"},
        {"name": "Baseline Smoothing", "desc": "Suavização de linha de base em gráficos com algoritmos avançados.", "emoji": "📈", "url": "https://appbaselinesmoothinglineplotpy-mvx5cnwr5szg4ghwpbx379.streamlit.app/"},
        {"name": "Isotherms App", "desc": "Análise de isotermas de adsorção com modelos de Langmuir e Freundlich.", "emoji": "🌡️", "url": "https://isothermsappfixedpy-ropmkqgbbxujhvkd6pfxgi.streamlit.app/"},
        {"name": "Histograms", "desc": "Geração de histogramas customizados com análise estatística.", "emoji": "📶", "url": "https://apphistogramspy-b3kfy7atbdhgxx8udeduma.streamlit.app/"},
        {"name": "Column 3D Line", "desc": "Visualização de dados em 3D com projeções e rotação interativa.", "emoji": "🌐", "url": "https://column3dpyline2inmoduleimportdash-kdqhfwwyyhdtb48x4z3kkn.streamlit.app/"},
        {"name": "Crystallinity DSC/XRD", "desc": "Cálculo de cristalinidade por DSC e XRD com análise comparativa.", "emoji": "💎", "url": "https://appcrystallinitydscxrdpy-wqtymsdcco2nuem7fv3hve.streamlit.app/"},
        {"name": "Column 3D", "desc": "Visualização de dados em colunas 3D com mapeamento de cores.", "emoji": "🏛️", "url": "https://column3dpy-cskafquxluvyv23hbnhxli.streamlit.app/"},
        {"name": "Kinetic Models", "desc": "Ajuste de modelos cinéticos com otimização de parâmetros.", "emoji": "⚗️", "url": "https://kineticmodelsapppy-fz8qyt64fahje5acofqpcm.streamlit.app/"},
        {"name": "Python Launcher", "desc": "Executor de scripts Python online com ambiente isolado.", "emoji": "🐍", "url": "https://pythonlauncherfixedpy-yschqh6qwzl526xurdeoca.streamlit.app/"},
    ]
    
    # Filtrar apps baseado na busca
    query = search_query.lower().strip() if search_query else ""
    filtered_apps = [app for app in APPS if query in app["name"].lower() or query in app["desc"].lower()] if query else APPS
    
    # Renderizar cards
    if filtered_apps:
        # Criar grid de 3 colunas
        cols = st.columns(3, gap="medium")
        
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
    
    st.markdown('</div>', unsafe_allow_html=True)  # Fecha portal-content
    st.markdown('</div>', unsafe_allow_html=True)  # Fecha portal-wrapper

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


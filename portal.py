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

# --- Funções de Autenticação (do segundo arquivo) ---

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
        # Adiciona um usuário padrão 'admin' com senha 'admin' se não existir
        cur.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cur.fetchone():
            admin_pass = hash_password("admin")
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

# --- Interface do Portal (do primeiro arquivo, adaptado) ---

def show_portal():
    """Exibe o portal de aplicativos."""
    # ---------- ESTILO (glass + dark) ----------
    st.markdown("""
    <style>
    .stApp {
      background:
        radial-gradient(1200px 500px at 20% -10%, rgba(99,102,241,0.25), transparent 40%),
        radial-gradient(1000px 450px at 90% 10%, rgba(45,212,191,0.22), transparent 40%),
        linear-gradient(180deg, #121317 0%, #0f1116 100%) !important;
      color: #EAEAF1;
    }
    .nav { 
      position: sticky; top: 0; z-index: 20; padding: 14px 22px; margin: -1.2rem -1rem 0 -1rem;
      backdrop-filter: blur(8px); background: rgba(255,255,255,0.06);
      border-bottom: 1px solid rgba(255,255,255,0.12); 
      display: flex; justify-content: space-between; align-items: center;
    }
    .brand { 
      font-weight: 700; font-size: 1.05rem; letter-spacing: .02em; 
    }
    .block-container input[type="text"]{
      background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.20);
      border-radius: 999px !important; color: #fff !important;
    }
    .block-container .stTextInput > div > div{ 
      border-radius: 999px !important; 
    }
    .card{ 
      position: relative; overflow: hidden; padding: 22px 22px 18px 22px; border-radius: 20px;
      background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.18);
      box-shadow: 0 10px 30px rgba(0,0,0,0.35);
      transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease; 
      margin-bottom: 28px;
      height: 280px;
    }
    .card:hover{ 
      transform: translateY(-2px); 
      box-shadow: 0 16px 40px rgba(0,0,0,0.45); 
      border-color: rgba(255,255,255,0.28); 
    }
    .card .accent{ 
      position: absolute; left: 0; top: 0; bottom: 0; width: 10px; 
    }
    .icon{ 
      width:84px; height:84px; border-radius:50%; display:grid; place-items:center;
      background: rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.20); 
      font-size:36px; margin-bottom:10px; 
    }
    .card h3{ 
      margin:6px 0 4px 0; font-size:1.25rem; color:#fff; 
    }
    .card p{ 
      margin:0 0 14px 0; color:#CBD5E1; line-height:1.35; 
    }
    .actions{ 
      display:flex; gap:12px; align-items:center; margin-top:14px; 
    }
    .btn{ 
      padding:10px 18px; border-radius:12px; background:rgba(255,255,255,0.10);
      border:1px solid rgba(255,255,255,0.22); color:#fff; text-decoration:none; font-weight:600;
      transition: background .15s ease, border-color .15s ease, transform .15s ease; 
    }
    .btn:hover{ 
      background:rgba(255,255,255,0.16); 
      border-color:rgba(255,255,255,0.32); 
      transform: translateY(-1px); 
    }
    h1,h2{ 
      color:#fff; 
    } 
    .subtitle{ 
      color:#CBD5E1; margin-top:-6px; 
    }
    .stColumn > div {
      padding-left: 0.5rem !important;
      padding-right: 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------- DADOS (com os links fornecidos) ----------
    APPS = [
        {"name": "TG/ADT Events", "desc": "Análise de eventos térmicos em TG/ADT.", "emoji": "🔥", "url": "https://apptgadtgeventspy-hqeqt7yljzwra3r7nmdhju.streamlit.app/", "accent": "linear-gradient(180deg, #f97316, #ef4444)"},
        {"name": "Stack Graph", "desc": "Criação de gráficos empilhados.", "emoji": "📊", "url": "https://appstackgraphpy-ijew8pyut2jkc4x4pa7nbv.streamlit.app/", "accent": "linear-gradient(180deg, #a855f7, #d946ef)"},
        {"name": "Rheology App", "desc": "Análise de dados de reologia.", "emoji": "🔄", "url": "https://apprheologyapppy-mbkr3wmbdb76t3ysvlfecr.streamlit.app/", "accent": "linear-gradient(180deg, #ec4899, #f43f5e)"},
        {"name": "Mechanical Properties", "desc": "Cálculo de propriedades mecânicas.", "emoji": "⚙️", "url": "https://appmechanicalpropertiespy-79l8dejt9kfmmafantscut.streamlit.app/", "accent": "linear-gradient(180deg, #84cc16, #22c55e)"},
        {"name": "Baseline Smoothing", "desc": "Suavização de linha de base em gráficos.", "emoji": "📈", "url": "https://appbaselinesmoothinglineplotpy-mvx5cnwr5szg4ghwpbx379.streamlit.app/", "accent": "linear-gradient(180deg, #22d3ee, #0ea5e9)"},
        {"name": "Isotherms App", "desc": "Análise de isotermas de adsorção.", "emoji": "🌡️", "url": "https://isothermsappfixedpy-ropmkqgbbxujhvkd6pfxgi.streamlit.app/", "accent": "linear-gradient(180deg, #f59e0b, #fbbf24)"},
        {"name": "Histograms", "desc": "Geração de histogramas customizados.", "emoji": "📶", "url": "https://apphistogramspy-b3kfy7atbdhgxx8udeduma.streamlit.app/", "accent": "linear-gradient(180deg, #6366f1, #818cf8)"},
        {"name": "Column 3D Line", "desc": "Visualização de dados em 3D com linhas.", "emoji": "🌐", "url": "https://column3dpyline2inmoduleimportdash-kdqhfwwyyhdtb48x4z3kkn.streamlit.app/", "accent": "linear-gradient(180deg, #10b981, #14b8a6)"},
        {"name": "Crystallinity DSC/XRD", "desc": "Cálculo de cristalinidade por DSC e XRD.", "emoji": "💎", "url": "https://appcrystallinitydscxrdpy-wqtymsdcco2nuem7fv3hve.streamlit.app/", "accent": "linear-gradient(180deg, #06b6d4, #38bdf8)"},
        {"name": "Column 3D", "desc": "Visualização de dados em colunas 3D.", "emoji": "🏛️", "url": "https://column3dpy-cskafquxluvyv23hbnhxli.streamlit.app/", "accent": "linear-gradient(180deg, #8b5cf6, #a78bfa)"},
        {"name": "Kinetic Models", "desc": "Ajuste de modelos cinéticos.", "emoji": "⚗️", "url": "https://kineticmodelsapppy-fz8qyt64fahje5acofqpcm.streamlit.app/", "accent": "linear-gradient(180deg, #d946ef, #ec4899)"},
        {"name": "Python Launcher", "desc": "Executor de scripts Python online.", "emoji": "🐍", "url": "https://pythonlauncherfixedpy-yschqh6qwzl526xurdeoca.streamlit.app/", "accent": "linear-gradient(180deg, #facc15, #eab308)"},
    ]

    # ---------- TOPO + BUSCA + LOGOUT ----------
    st.markdown('<div class="nav"><span class="brand">Portal de Análises</span></div>', unsafe_allow_html=True)
    
    # Adiciona botão de logout à direita da barra de navegação
    with st.container():
        _, col2 = st.columns([0.9, 0.1])
        with col2:
             if st.button("Sair", key="logout_button"):
                st.session_state.authenticated = False
                st.rerun()

    st.markdown("### Seu portal de aplicativos de análise")
    st.markdown('<p class="subtitle">Rápido, organizado e bonito — clique para abrir em uma nova aba.</p>', unsafe_allow_html=True)
    
    q = st.text_input("Buscar", placeholder="Buscar aplicativos…", label_visibility="collapsed").strip().lower()
    apps = [a for a in APPS if q in a["name"].lower() or q in a["desc"].lower()] if q else APPS

    # ---------- RENDERIZAÇÃO COM COLUNAS ----------
    if apps:
        cols = st.columns(3) # Aumentado para 3 colunas para melhor visualização
        
        for i, app in enumerate(apps):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="card">
                  <div class="accent" style="background:{app['accent']};"></div>
                  <div class="icon">{app['emoji']}</div>
                  <h3>{app['name']}</h3>
                  <p>{app['desc']}</p>
                  <div class="actions">
                    <a class="btn" href="{app['url']}" target="_blank" rel="noopener">Abrir →</a>
                  </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("### Nenhum aplicativo encontrado")
        st.markdown("Tente buscar por outro termo.")


# --- Página de Login ---

def show_login_page():
    """Exibe a página de login."""
    st.markdown("""
    <style>
        .stApp {
            background: #111827;
        }
        .login-container {
            padding: 3rem 1rem;
            background-color: #1F2937;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.header("🔐 Acesso ao Portal")
            st.write("Por favor, insira suas credenciais.")
            
            username = st.text_input("👤 Usuário", key="login_username")
            password = st.text_input("🔑 Senha", type="password", key="login_password")
            
            if st.button("Entrar", use_container_width=True):
                if validate_user(username, password):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")
            st.info("Usuário padrão: `admin`, Senha padrão: `admin`")
            st.markdown('</div>', unsafe_allow_html=True)

# --- Lógica Principal ---

def main():
    """Função principal que controla qual página exibir."""
    create_user_db() # Garante que o DB exista

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        show_portal()
    else:
        show_login_page()

if __name__ == "__main__":
    main()

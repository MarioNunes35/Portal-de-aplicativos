import streamlit as st
from urllib.parse import urlparse
import hashlib
import hmac

st.set_page_config(page_title="Portal de Análises", page_icon="🚀", layout="wide")

# ===========================
# Session State Management
# ===========================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

# ===========================
# OIDC preflight (checks Secrets before calling st.login)
# ===========================
def check_oidc_available():
    """Verifica se OIDC está disponível e configurado"""
    try:
        # Verifica se st.login existe e está disponível
        if not hasattr(st, 'login'):
            return False, ["st.login não está disponível nesta versão do Streamlit"]
        
        # Verifica se há user info disponível
        if hasattr(st, 'user') and getattr(st.user, 'is_logged_in', False):
            return True, []
            
        # Verifica configuração OIDC
        problems = check_oidc_secrets()
        if problems:
            return False, problems
            
        return True, []
    except Exception as e:
        return False, [f"Erro ao verificar OIDC: {str(e)}"]

def check_oidc_secrets():
    cfg = st.secrets.get("oidc", {})
    required = ["client_id", "client_secret", "redirect_uri", "discovery_url", "cookie_secret"]
    missing = [k for k in required if not str(cfg.get(k, "")).strip()]
    problems = []

    if missing:
        problems.append(f"Faltando em [oidc]: {', '.join(missing)}")

    cid = cfg.get("client_id", "")
    if cid and not cid.endswith(".apps.googleusercontent.com"):
        problems.append("client_id parece inválido (não termina com .apps.googleusercontent.com)")

    disc = cfg.get("discovery_url", "")
    if disc and not disc.startswith("https://accounts.google.com/.well-known/openid-configuration"):
        problems.append("discovery_url deve ser https://accounts.google.com/.well-known/openid-configuration")

    csec = cfg.get("cookie_secret", "")
    if csec and len(csec) < 43:
        problems.append("cookie_secret curto (gere um novo com ~32 bytes, ~43+ chars urlsafe)")

    return problems

# ===========================
# Fallback Authentication
# ===========================
def simple_auth(username: str, password: str) -> tuple[bool, str]:
    """Autenticação simples como fallback"""
    # Busca credenciais nos secrets
    fallback_users = st.secrets.get("fallback_auth", {}).get("users", {})
    
    if not fallback_users:
        # Se não há usuários configurados, use uma lista padrão (apenas para demo)
        # Em produção, sempre configure os usuários nos secrets!
        fallback_users = {
            "admin": {
                "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
                "email": "admin@example.com"
            }
        }
    
    if username in fallback_users:
        user_data = fallback_users[username]
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash == user_data.get("password_hash"):
            return True, user_data.get("email", f"{username}@portal.local")
    
    return False, ""

# ===========================
# Allowlist / Roles
# ===========================
def get_allowlists():
    auth = st.secrets.get("auth", {})
    emails = { (e or "").strip().lower() for e in auth.get("allowed_emails", []) }
    domains = { (d or "").strip().lower() for d in auth.get("allowed_domains", []) }
    return emails, domains

def is_allowed(email: str, emails, domains) -> bool:
    if not email:
        return False
    # Se não há listas configuradas, permite todos (para facilitar desenvolvimento)
    if not emails and not domains:
        return True
    if email in emails:
        return True
    return any(email.endswith(f"@{d}") for d in domains)

def has_role(email: str, role: str | None):
    if role is None:
        return True
    roles = st.secrets.get("roles", {})
    permitted = { (e or "").strip().lower() for e in roles.get(role, []) }
    return email in permitted

# ===========================
# Styles
# ===========================
CSS = """
<style>
.login-wrap {
  max-width: 620px;
  margin: 5vh auto 3rem auto;
  padding: 2.2rem 2rem 1.6rem 2rem;
  border-radius: 20px;
  background: rgba(22, 22, 26, 0.85);
  border: 1px solid rgba(255,255,255,0.06);
  box-shadow: 0 12px 40px rgba(0,0,0,0.25);
}
.login-title { font-size: 2.0rem; font-weight: 800; margin-bottom: 0.25rem; }
.login-sub { opacity: .85; margin: 0 0 1.4rem 0; }
label, .stCheckbox label { font-weight: 600; }
.small-note { font-size: 0.85rem; opacity: .70; }
.google-btn > button { width: 100%; height: 44px; font-weight: 700; }
.google-btn > button:before {
  content: " "; display: inline-block; width: 18px; height: 18px; margin-right: 8px; vertical-align: -3px;
  background-image: url('https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg'); background-size: cover;
}
.app-card {
    border: 1px solid var(--secondary-background-color);
    border-radius: 0.75rem;
    padding: 0.9rem 0.9rem 0.6rem 0.9rem;
    height: 100%;
    background: var(--background-color);
    box-shadow: 0 0 0 1px rgba(0,0,0,0.02), 0 2px 8px rgba(0,0,0,0.06);
}
.app-url { font-size: 0.8rem; opacity: 0.7; margin-top: 0.25rem; word-break: break-all; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ===========================
# Login Functions
# ===========================
def render_login_card():
    """Renderiza o card de login com suporte a OIDC ou fallback"""
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🚀 Portal de Análises</div>', unsafe_allow_html=True)
    
    # Verifica disponibilidade de OIDC
    oidc_available, problems = check_oidc_available()
    
    if oidc_available and hasattr(st, 'login'):
        # Usa OIDC/Google
        st.markdown('<div class="login-sub">Entre com sua conta Google para continuar</div>', unsafe_allow_html=True)
        
        # Campos visuais (desabilitados)
        colu, colv = st.columns(2)
        with colu:
            st.text_input("Usuário", placeholder="Digite seu usuário", disabled=True, key="dummy_user")
        with colv:
            st.text_input("Senha", type="password", placeholder="Digite sua senha", disabled=True, key="dummy_pass")
        
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Lembrar-me", value=True, disabled=True, key="dummy_remember")
        with col2:
            st.checkbox("Mostrar senha", value=False, disabled=True, key="dummy_show")
        
        st.caption("Este portal usa autenticação Google. Os campos acima são apenas visuais.")
        
        # Botão Google
        with st.container():
            st.markdown('<div class="google-btn">', unsafe_allow_html=True)
            if st.button("Entrar com Google", type="primary", use_container_width=True):
                try:
                    st.login("oidc")
                except Exception as e:
                    st.error(f"Erro ao iniciar login Google: {str(e)}")
                    st.info("Recarregue a página ou use o login alternativo abaixo.")
            st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        # Fallback para autenticação simples
        st.markdown('<div class="login-sub">Entre com suas credenciais</div>', unsafe_allow_html=True)
        
        if problems:
            with st.expander("⚠️ Configuração OIDC", expanded=False):
                st.warning("Login Google não disponível. Usando autenticação alternativa.")
                for p in problems:
                    st.markdown(f"- {p}")
                
                # Se o problema é falta de Authlib, mostra instruções
                if any("Authlib" in p for p in problems):
                    st.info("""
                    **Para habilitar login com Google:**
                    1. Adicione ao arquivo `requirements.txt`:
                       ```
                       Authlib>=1.3.2
                       ```
                    2. Faça o redeploy do app
                    3. Configure os secrets OIDC conforme documentação
                    """)
        
        # Formulário de login simples
        with st.form("login_form"):
            username = st.text_input("Usuário", placeholder="Digite seu usuário")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            col1, col2 = st.columns(2)
            with col1:
                remember = st.checkbox("Lembrar-me", value=True)
            with col2:
                submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            
            if submitted:
                if username and password:
                    success, email = simple_auth(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_email = email
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos")
                else:
                    st.error("Por favor, preencha todos os campos")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ===========================
# App catalog
# ===========================
APPS = [
    {"name": "TG/ADT Events", "url": "https://apptgadtgeventspy-hqeqt7yljzwra3r7nmdhju.streamlit.app"},
    {"name": "Stack Graph", "url": "https://appstackgraphpy-ijew8pyut2jkc4x4pa7nbv.streamlit.app"},
    {"name": "Rheology App", "url": "https://apprheologyapppy-mbkr3wmbdb76t3ysvlfecr.streamlit.app"},
    {"name": "Mechanical Properties", "url": "https://appmechanicalpropertiespy-79l8dejt9kfmmafantscut.streamlit.app"},
    {"name": "Baseline Smoothing", "url": "https://appbaselinesmoothinglineplotpy-mvx5cnwr5szg4ghwpbx379.streamlit.app"},
    {"name": "Isotherms App", "url": "https://isothermsappfixedpy-ropmkqgbbxujhvkd6pfxgi.streamlit.app"},
    {"name": "Histograms", "url": "https://apphistogramspy-b3kfy7atbdhgxx8udeduma.streamlit.app"},
    {"name": "Column 3D Line", "url": "https://column3dpyline2inmoduleimportdash-kdqhfwwyyhdtb48x4z3kkn.streamlit.app"},
    {"name": "Crystallinity DSC/XRD", "url": "https://appcrystallinitydscxrdpy-wqtymsdcco2nuem7fv3hve.streamlit.app"},
    {"name": "Column 3D", "url": "https://column3dpy-cskafquxluvyv23hbnhxli.streamlit.app"},
    {"name": "Kinetic Models", "url": "https://kineticmodelsapppy-fz8qyt64fahje5acofqpcm.streamlit.app"},
    {"name": "Python Launcher", "url": "https://pythonlauncherfixedpy-yschqh6qwzl526xurdeoca.streamlit.app"},
]

# ===========================
# Main Flow
# ===========================
# Determina se o usuário está autenticado
is_logged_in = False
user_email = None

# Primeiro verifica OIDC (se disponível)
if hasattr(st, 'user') and getattr(st.user, 'is_logged_in', False):
    is_logged_in = True
    user_email = (getattr(st.user, 'email', '') or '').lower()
# Senão, verifica session state (fallback auth)
elif st.session_state.authenticated:
    is_logged_in = True
    user_email = st.session_state.user_email

# Se não está logado, mostra tela de login
if not is_logged_in:
    render_login_card()
    st.stop()

# Verifica permissões
emails, domains = get_allowlists()

if not is_allowed(user_email, emails, domains):
    st.error("Acesso não autorizado. Solicite liberação ao administrador.")
    if st.button("Fazer logout"):
        if hasattr(st, 'logout'):
            st.logout()
        else:
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()
    st.stop()

# Verifica roles (opcional)
required_role = None  # Mude para "admin" se necessário
if not has_role(user_email, required_role):
    st.error("Você não tem permissão para acessar esta seção.")
    st.stop()

# ===========================
# Interface Principal
# ===========================
# Sidebar com informações do usuário
with st.sidebar:
    st.caption(f"Logado como: {user_email}")
    if st.button("Sair"):
        if hasattr(st, 'logout'):
            st.logout()
        else:
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()

# Título e busca
st.title("📚 Apps disponíveis")
q = st.text_input("Buscar apps por nome:", placeholder="Ex.: histogram, 3D, rheology...").strip().lower()

def matches(app, q):
    if not q:
        return True
    return q in app["name"].lower() or q in app["url"].lower()

apps = [a for a in APPS if matches(a, q)]
st.caption(f"{len(apps)} app(s) encontrado(s).")

# Grid de apps
N_COLS = 3
cols = st.columns(N_COLS)

for i, app in enumerate(apps):
    with cols[i % N_COLS]:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.subheader(app["name"])
        st.markdown(f'<div class="app-url">{app["url"]}</div>', unsafe_allow_html=True)
        st.link_button("Abrir app", app["url"], type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Ajuda
st.divider()
with st.expander("ℹ️ Ajuda"):
    st.markdown("""
    - Caso um app peça login novamente, é normal: cada app também valida acesso.
    - Se aparecer **Acesso não autorizado**, peça liberação ao administrador.
    - Problemas com a conta Google? Tente sair e entrar novamente em `accounts.google.com`.
    """)











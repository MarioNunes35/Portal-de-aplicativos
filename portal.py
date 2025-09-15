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
    """Verifica se OIDC está disponível e configurado. 
    Retorna (available: bool, provider_arg: str|None, problems: list[str]).
    """
    problems = []
    try:
        # 1) st.login disponível?
        if not hasattr(st, "login"):
            return False, None, ["st.login não está disponível nesta versão do Streamlit"]
        
        # 2) Já logado?
        if hasattr(st, "user") and getattr(st.user, 'is_logged_in', False):
            return True, None, []
        
        # 3) Resolver provider a partir de secrets
        provider_arg, provider_problems = resolve_auth_provider()
        problems.extend(provider_problems)
        if problems:
            return False, provider_arg, problems
        
        return True, provider_arg, []
    except Exception as e:
        return False, None, [f"Erro ao verificar OIDC: {str(e)}"]

def resolve_auth_provider():
    """Inspeciona st.secrets e tenta descobrir onde estão as chaves de OIDC/OAuth.
    Suporta:
      - [auth] com (client_id, client_secret, server_metadata_url|discovery_url, redirect_uri, cookie_secret)
      - [auth.<nome>] com (client_id, client_secret, server_metadata_url|discovery_url) e, em [auth], (redirect_uri, cookie_secret)
      - [oidc] legado com (client_id, client_secret, redirect_uri, discovery_url|server_metadata_url, cookie_secret)
    Retorna (provider_arg, problems). Se provider_arg for None, chama-se st.login() sem nome.
    """
    problems = []
    auth_root = st.secrets.get("auth", {})
    # normalizar discovery_url -> server_metadata_url quando aparecer
    def norm_provider(cfg: dict) -> dict:
        cfg = dict(cfg or {})
        if "server_metadata_url" not in cfg and "discovery_url" in cfg:
            cfg["server_metadata_url"] = cfg.get("discovery_url")
        return cfg
    
    # 1) Caso A: tudo em [auth]
    root_cfg = norm_provider(auth_root)
    root_has_provider = all(str(root_cfg.get(k, "")).strip() for k in ("client_id","client_secret","server_metadata_url"))
    root_has_root = all(str(root_cfg.get(k, "")).strip() for k in ("redirect_uri","cookie_secret"))
    if root_has_provider and root_has_root:
        # provider sem nome
        return None, []
    
    # 2) Caso B: provider nomeado dentro de [auth.<nome>]
    named_candidate = None
    for name, cfg in auth_root.items():
        if isinstance(cfg, dict):
            cfg = norm_provider(cfg)
            if all(str(cfg.get(k, "")).strip() for k in ("client_id","client_secret","server_metadata_url")):
                named_candidate = name
                break
    if named_candidate:
        # precisa de redirect_uri e cookie_secret no [auth] raiz
        if not all(str(auth_root.get(k, "")).strip() for k in ("redirect_uri","cookie_secret")):
            miss = [k for k in ("redirect_uri","cookie_secret") if not str(auth_root.get(k, "")).strip()]
            problems.append("Faltando em [auth]: " + ", ".join(miss))
        return str(named_candidate), problems
    
    # 3) Caso C: bloco legado [oidc]
    legacy = norm_provider(st.secrets.get("oidc", {}))
    if legacy:
        req = ["client_id","client_secret","redirect_uri","server_metadata_url","cookie_secret"]
        miss = [k for k in req if not str(legacy.get(k, "")).strip()]
        if miss:
            problems.append("Faltando em [oidc]: " + ", ".join(miss))
        else:
            return "oidc", []
    
    # 4) Não encontrado
    if not problems:
        problems.append("Nenhuma configuração válida encontrada. Preencha [auth] e/ou [auth.<nome>] com as chaves necessárias.")
    return None, problems

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
                "email": "admin@portal.local",
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

def is_allowed(email: str, emails: set[str], domains: set[str]):
    email = (email or "").strip().lower()
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
    max-width: 680px; margin: 3rem auto 1.5rem auto;
    padding: 1.25rem 1.25rem 0.5rem 1.25rem;
    background: var(--background-color);
    border-radius: 16px;
    border: 1px solid rgba(49, 51, 63, 0.2);
}
.login-title {
    font-size: 1.25rem; font-weight: 700; margin-bottom: 0.25rem;
}
.login-sub { font-size: 0.95rem; opacity: 0.8; margin-bottom: 0.5rem; }
.google-btn { margin-top: 0.25rem; }

.app-grid {
    display: grid; gap: 12px; grid-template-columns: repeat(12, 1fr);
}
.app-card {
    grid-column: span 4;
    padding: 0.9rem 0.9rem 0.6rem 0.9rem;
    height: 100%;
    background: var(--background-color);
    box-shadow: 0 0 0 1px rgba(0,0,0,0.02), 0 2px 8px rgba(0,0,0,0.06);
}
.app-url { font-size: 0.8rem; opacity: 0.7; margin-top: 0.25rem; word-break: break-all; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ===== Compat helpers / Debug =====
import sys, platform
from datetime import datetime

def link_btn(label: str, url: str):
    """Compat: usa st.link_button se existir; senão, mostra um link padrão."""
    if hasattr(st, "link_button"):
        st.link_button(label, url, type="primary", use_container_width=True)
    else:
        st.markdown(f"[**{label}**]({url})")


def show_diag(note: str | None = None, error: Exception | None = None):
    """Painel compacto de diagnóstico para entender 500 internos."""
    with st.expander("🛠 Diagnóstico (local)", expanded=False):
        if note:
            st.info(note)
        if error:
            st.exception(error)
        try:
            provider_arg, provider_problems = resolve_auth_provider()
        except Exception as e:
            provider_arg, provider_problems = None, [f"resolve_auth_provider falhou: {e}"]
        info = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "streamlit_version": getattr(st, "__version__", "unknown"),
            "st_user_present": bool(getattr(st, "user", None)),
            "st_user_is_logged": bool(getattr(getattr(st, "user", object()), "is_logged_in", False)),
            "st_user_email": (getattr(getattr(st, "user", object()), "email", "") or ""),
            "provider_arg": provider_arg,
            "provider_problems": provider_problems,
            "secrets_keys": sorted(list(st.secrets.keys())),
            "has_[auth]": bool(st.secrets.get("auth")),
            "has_[oidc]": bool(st.secrets.get("oidc")),
        }
        st.json(info)

# ===========================
# Login Functions
# ===========================
def render_login_card():
    """Renderiza o card de login com suporte a OIDC ou fallback"""
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🚀 Portal de Análises</div>', unsafe_allow_html=True)
    
    # Verifica disponibilidade de OIDC
    oidc_available, provider_arg, problems = check_oidc_available()
    
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
            st.checkbox("Lembrar de mim", value=True, disabled=True)
        with col2:
            st.checkbox("Mostrar senha", value=False, disabled=True, key="dummy_show")
        
        st.caption("Este portal usa autenticação Google. Os campos acima são apenas visuais.")
        
        # Botão Google
        with st.container():
            st.markdown('<div class="google-btn">', unsafe_allow_html=True)
            if st.button("Entrar com Google", type="primary", use_container_width=True):
                try:
                    st.login(provider_arg) if provider_arg else st.login()
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
                
                # Dica rápida de dependência (Authlib)
                st.info(
                    """
                    **Para habilitar login com Google:**
                    1. Em `requirements.txt` adicione/garanta:
                       ```
                       streamlit>=1.42
                       authlib>=1.3.2
                       ```
                    2. Configure `Secrets` com **[auth]** e (opcional) **[auth.<nome>]**.
                    3. No Google Cloud, cadastre o `redirect_uri` que termina com **/oauth2callback**.
                    """
                )
        
        # Formulário de login simples
        with st.form("login_form"):
            username = st.text_input("Usuário", placeholder="Digite seu usuário")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            col1, col2 = st.columns(2)
            with col1:
                st.checkbox("Lembrar de mim", value=True)
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
# Conteúdo protegido (após login)
# ===========================
# Determina se está logado
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

st.title("📊 Portal de Análises")
st.write("Selecione um aplicativo abaixo para abrir em uma nova aba:")

# Lista de apps (exemplo)
apps = [
    {"name": "Barras Agrupadas", "url": "https://barras-agrupado.streamlit.app"},
    {"name": "TGA & DTG", "url": "https://tga-dtg.streamlit.app"},
    {"name": "Raman Deconvolution", "url": "https://raman-deconv.streamlit.app"},
    {"name": "Linha Base & Suavização", "url": "https://linha-base.streamlit.app"},
    {"name": "Histogramas", "url": "https://histogramas.streamlit.app"},
    {"name": "Colunas 3D", "url": "https://colunas-3d.streamlit.app"},
]

# Grid responsivo simples
try:
    N_COLS = 3
    cols = st.columns(N_COLS)
    for i, app in enumerate(apps):
        with cols[i % N_COLS]:
            st.markdown('<div class="app-card">', unsafe_allow_html=True)
            st.subheader(app["name"])
            st.markdown(f'<div class="app-url">{app["url"]}</div>', unsafe_allow_html=True)
            link_btn("Abrir app", app["url"])
            st.markdown("</div>", unsafe_allow_html=True)
except Exception as e:
    st.error("Falha ao renderizar a grade de aplicativos.")
    show_diag("Exceção ao montar o grid de apps", e)

# Ajuda
st.divider()
with st.expander("ℹ️ Ajuda"):
    st.markdown(
        """
        - Caso um app peça login novamente, é normal: cada app também valida acesso.
        - Se aparecer **Acesso não autorizado**, peça liberação ao administrador.
        - Problemas com a conta Google? Tente sair e entrar novamente em `accounts.google.com`.
        """
    )











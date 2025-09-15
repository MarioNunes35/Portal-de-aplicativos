import streamlit as st
from urllib.parse import urlparse
import hashlib
import hmac
from pathlib import Path
import json, csv

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
    """Inspeciona st.secrets e tenta descobrir onde estão as chaves de OIDC/OAuth."""
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
    fallback_users = st.secrets.get("fallback_auth", {}).get("users", {})
    
    if not fallback_users:
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
    """
    Carrega as listas de permissão dos secrets de forma segura.
    Garante que os valores sejam listas para evitar erros de iteração.
    """
    auth = st.secrets.get("auth", {})
    
    # MODIFICADO: Garante que os valores sejam listas para evitar erros
    allowed_emails_list = auth.get("allowed_emails", [])
    if not isinstance(allowed_emails_list, list):
        allowed_emails_list = [] # Usa lista vazia se o formato for inválido

    allowed_domains_list = auth.get("allowed_domains", [])
    if not isinstance(allowed_domains_list, list):
        allowed_domains_list = [] # Usa lista vazia se o formato for inválido

    emails = { (e or "").strip().lower() for e in allowed_emails_list }
    domains = { (d or "").strip().lower() for d in allowed_domains_list }
    return emails, domains

def is_allowed(email: str, emails: set[str], domains: set[str]):
    email = (email or "").strip().lower()
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
.login-sub { font-size: 0.95rem; opacity: 0.8; margin-bottom: 1rem; }
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

# ===========================
# Apps loader (dinâmico)
# ===========================
def _coerce_items(seq):
    out = []
    for it in seq:
        if not isinstance(it, dict):
            continue
        name = (it.get("name") or it.get("title") or "").strip()
        url = (it.get("url") or it.get("href") or "").strip()
        icon = (it.get("icon") or it.get("emoji") or "↗️").strip() or "↗️"
        if name and url:
            out.append({"name": name, "url": url, "icon": icon})
    seen = set()
    dedup = []
    for it in out:
        if it["name"] in seen:
            continue
        seen.add(it["name"])
        dedup.append(it)
    return dedup

def load_apps():
    apps_from_secrets = st.secrets.get("apps", None)
    if isinstance(apps_from_secrets, list):
        coerced = _coerce_items(apps_from_secrets)
        if coerced:
            return coerced, "secrets:[[apps]]"
    elif isinstance(apps_from_secrets, dict):
        items = apps_from_secrets.get("items")
        if isinstance(items, list):
            coerced = _coerce_items(items)
            if coerced:
                return coerced, "secrets:[apps].items"
    
    p_json = Path("apps.json")
    if p_json.exists():
        try:
            data = json.loads(p_json.read_text(encoding="utf-8"))
            if isinstance(data, list):
                coerced = _coerce_items(data)
                if coerced:
                    return coerced, "apps.json"
            elif isinstance(data, dict) and "items" in data:
                coerced = _coerce_items(data.get("items", []))
                if coerced:
                    return coerced, "apps.json:items"
        except Exception as e:
            st.warning(f"apps.json inválido: {e}")

    p_csv = Path("apps.csv")
    if p_csv.exists():
        try:
            rows = []
            with p_csv.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    rows.append(r)
            coerced = _coerce_items(rows)
            if coerced:
                return coerced, "apps.csv"
        except Exception as e:
            st.warning(f"apps.csv inválido: {e}")

    fallback = [
        {"name": "Barras Agrupadas", "url": "https://barras-agrupado.streamlit.app", "icon": "📊"},
        {"name": "TGA & DTG", "url": "https://tga-dtg.streamlit.app", "icon": "🔥"},
        {"name": "Raman Deconvolution", "url": "https://raman-deconv.streamlit.app", "icon": "📈"},
        {"name": "Linha Base & Suavização", "url": "https://linha-base.streamlit.app", "icon": "🧰"},
        {"name": "Histogramas", "url": "https://histogramas.streamlit.app", "icon": "📉"},
        {"name": "Colunas 3D", "url": "https://colunas-3d.streamlit.app", "icon": "🧱"},
    ]
    return fallback, "fallback"

# ===========================
# Login Functions
# ===========================
def render_login_card():
    """Renderiza o card de login com suporte a OIDC ou fallback"""
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🚀 Portal de Análises</div>', unsafe_allow_html=True)
    
    oidc_available, provider_arg, problems = check_oidc_available()
    
    if oidc_available and hasattr(st, 'login'):
        # MODIFICADO: Layout simplificado apenas com o botão do Google
        st.markdown('<div class="login-sub">Entre com sua conta Google para continuar</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="google-btn">', unsafe_allow_html=True)
            if st.button("Entrar com Google", type="primary", use_container_width=True):
                try:
                    st.login(provider_arg) if provider_arg else st.login()
                except Exception as e:
                    st.error(f"Erro ao iniciar login Google: {str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        # Fallback para autenticação simples
        st.markdown('<div class="login-sub">Entre com suas credenciais</div>', unsafe_allow_html=True)
        
        if problems:
            with st.expander("⚠️ Configuração OIDC", expanded=False):
                st.warning("Login Google não disponível. Usando autenticação alternativa.")
                for p in problems:
                    st.markdown(f"- {p}")
        
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
# Main Application Logic
# ===========================
# Determina se está logado
is_logged_in = False
user_email = None

if hasattr(st, 'user') and getattr(st.user, 'is_logged_in', False):
    is_logged_in = True
    user_email = (getattr(st.user, 'email', '') or '').lower()
elif st.session_state.authenticated:
    is_logged_in = True
    user_email = st.session_state.user_email

# Se não está logado, mostra a tela de login e para a execução
if not is_logged_in:
    render_login_card()
    st.stop()

# A partir daqui, o usuário está logado.
# Verifica permissões de acesso
emails, domains = get_allowlists()
if not is_allowed(user_email, emails, domains):
    st.error("Acesso não autorizado. Seu e-mail não está na lista de permissões.")
    if st.button("Sair"):
        if hasattr(st, 'logout'):
            st.logout()
        else:
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()
    st.stop()

# Verifica roles (opcional)
required_role = None
if not has_role(user_email, required_role):
    st.error("Você não tem a permissão necessária para acessar esta seção.")
    st.stop()

# ===========================
# Interface Principal (Conteúdo Protegido)
# ===========================
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

apps, source = load_apps()

q = st.text_input("🔎 Buscar app", "", placeholder="Filtrar por nome...").strip().casefold()
if q:
    apps = [a for a in apps if q in a["name"].casefold()]

st.caption(f"{len(apps)} app(s) encontrados | Origem: {source}")
st.write("Selecione um aplicativo abaixo para abrir em uma nova aba:")

# Grid de aplicativos
N_COLS = 3
cols = st.columns(N_COLS)
for i, app in enumerate(sorted(apps, key=lambda x: x['name'].casefold())):
    with cols[i % N_COLS]:
        with st.container(border=True):
            st.subheader(f"{app.get('icon','↗️')}  {app['name']}")
            st.caption(f"{app['url']}")
            if hasattr(st, "link_button"):
                st.link_button("Abrir App", app["url"], use_container_width=True)
            else:
                st.markdown(f"**[Abrir App]({app['url']})**")


# Seção de Ajuda
st.divider()
with st.expander("ℹ️ Ajuda e Configuração"):
    st.markdown(
        """
        **Como configurar a lista de apps**

        A lista de aplicativos pode ser configurada de três maneiras, nesta ordem de prioridade:
        1.  **Arquivo de Segredos (`.streamlit/secrets.toml`)**
        2.  **Arquivo `apps.json`** (na raiz do projeto)
        3.  **Arquivo `apps.csv`** (na raiz do projeto)

        **Exemplo para `secrets.toml`:**
        ```toml
        [[apps]]
        name = "Meu App 1"
        url  = "[https://meu-app-1.streamlit.app](https://meu-app-1.streamlit.app)"
        icon = "🧪"

        [[apps]]
        name = "Meu App 2"
        url  = "[https://meu-app-2.streamlit.app](https://meu-app-2.streamlit.app)"
        icon = "📈"
        ```
        ---
        - Se um aplicativo pedir login novamente, é um comportamento normal, pois cada um tem sua própria autenticação.
        - Se a mensagem **"Acesso não autorizado"** aparecer, seu e-mail precisa ser adicionado à lista de permissões pelo administrador.
        """
    )












import streamlit as st
from urllib.parse import urlparse

st.set_page_config(page_title="Portal de Análises", page_icon="🚀", layout="wide")

# ===========================
# OIDC preflight (checks Secrets before calling st.login)
# ===========================
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
# Keep old login "look" (but button triggers Google login)
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

def render_login_card():
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🚀 Portal de Análises</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-sub">Entre com sua conta Google para continuar</div>', unsafe_allow_html=True)

    colu, colv = st.columns(2)
    with colu:
        st.text_input("Usuário", placeholder="Digite seu usuário", disabled=True)
    with colv:
        st.text_input("Senha", type="password", placeholder="Digite sua senha", disabled=True)
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Lembrar-me", value=True, disabled=True)
    with col2:
        st.checkbox("Mostrar senha", value=False, disabled=True)

    st.caption("Este portal usa autenticação Google. Os campos acima são apenas visuais.")

    problems = check_oidc_secrets()
    if problems:
        st.error("Configuração OIDC incompleta/inepta. Ajuste os *Secrets* do app:")
        for p in problems:
            st.markdown(f"- {p}")
        st.stop()

    with st.container():
        st.markdown('<div class="google-btn">', unsafe_allow_html=True)
        if st.button("Entrar com Google", type="primary", use_container_width=True):
            st.login("oidc")
        st.markdown('</div>', unsafe_allow_html=True)

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
# Flow
# ===========================
if not getattr(st.user, "is_logged_in", False):
    # show old-looking card that triggers Google login
    render_login_card()
    st.stop()

# Logged in → enforce allowlist & roles
email = (getattr(st.user, "email", "") or "").lower()
emails, domains = get_allowlists()

# If you want to require allowlist strictly, keep as-is.
# If you want to allow everyone when lists are empty, uncomment the next line:
# if not emails and not domains: emails.add(email)

if not is_allowed(email, emails, domains):
    st.error("Acesso não autorizado. Solicite liberação ao administrador.")
    st.stop()

# (Optional) role gate
required_role = None  # e.g., "admin"
if not has_role(email, required_role):
    st.error("Você não tem permissão para acessar esta seção.")
    st.stop()

# Sidebar user box
with st.sidebar:
    st.caption(f"Logado como: {email}")
    st.button("Sair", on_click=st.logout)

# Main
st.title("📚 Apps disponíveis")
q = st.text_input("Buscar apps por nome:", placeholder="Ex.: histogram, 3D, rheology...").strip().lower()

def matches(app, q):
    if not q:
        return True
    return q in app["name"].lower() or q in app["url"].lower()

apps = [a for a in APPS if matches(a, q)]
st.caption(f"{len(apps)} app(s) encontrado(s).")

N_COLS = 3
cols = st.columns(N_COLS)

def short_host(url: str) -> str:
    try:
        return urlparse(url).netloc.replace(".streamlit.app", "")
    except Exception:
        return url

for i, app in enumerate(apps):
    with cols[i % N_COLS]:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.subheader(app["name"])
        st.markdown(f'<div class="app-url">{app["url"]}</div>', unsafe_allow_html=True)
        st.link_button("Abrir app", app["url"], type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()
with st.expander("ℹ️ Ajuda"):
    st.markdown("""
    - Caso um app peça login novamente, é normal: cada app também valida acesso.
    - Se aparecer **Acesso não autorizado**, peça liberação ao administrador.
    - Problemas com a conta Google? Tente sair e entrar novamente em `accounts.google.com`.
    """)












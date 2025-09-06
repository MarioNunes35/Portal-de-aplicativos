# portal-3_centered.py
# Login centralizado (overlay) mantendo o layout do portal.
# Credenciais: via .streamlit/secrets.toml (ver exemplo acima)
# ou variável de ambiente PORTAL_USERS_JSON='{"user":"pass"}'

import os
import json
import streamlit as st

st.set_page_config(page_title="Portal", page_icon="🚀", layout="wide")

# =============== Helpers ===============

def _get_auth_users():
    """Lê credenciais de st.secrets ou da variável de ambiente PORTAL_USERS_JSON."""
    if "auth" in st.secrets and "users" in st.secrets["auth"]:
        return dict(st.secrets["auth"]["users"])
    env_json = os.getenv("PORTAL_USERS_JSON")
    if env_json:
        try:
            return json.loads(env_json)
        except Exception:
            pass
    return None

def _center_login_css():
    """CSS para centralizar o formulário de login sem quebrar o resto da página."""
    st.markdown(
        """
        <style>
        /* Backdrop opcional (sutil) atrás do card de login */
        #login-backdrop {
            position: fixed; inset: 0; 
            background: rgba(0,0,0,0.28);
            z-index: 998;
        }
        /* Wrapper do card de login */
        #login-overlay {
            position: fixed; top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: min(820px, 92vw);
            z-index: 999;
        }
        /* Card visual no estilo do seu layout */
        .login-card {
            background: #1f1f1f;
            border-radius: 18px;
            padding: 48px 48px 36px 48px;
            box-shadow: 0 10px 40px rgba(0,0,0,.50);
            border: 1px solid rgba(255,255,255,0.06);
        }
        .login-title {
            font-size: 56px; line-height: 1.05; margin: 0 0 6px 0;
        }
        .login-sub {
            color:#9aa0a6; font-size: 20px; margin: 6px 0 28px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _show_login_overlay() -> None:
    """Renderiza o overlay de login centralizado. Controla autenticação via session_state."""
    _center_login_css()
    # Backdrop
    st.markdown('<div id="login-backdrop"></div>', unsafe_allow_html=True)

    # Conteúdo central
    st.markdown('<div id="login-overlay"><div class="login-card">', unsafe_allow_html=True)
    st.markdown('<h1 class="login-title">🚀 Acesso ao<br>Portal</h1>', unsafe_allow_html=True)
    st.markdown('<p class="login-sub">Entre com suas credenciais para continuar</p>', unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        c1, c2 = st.columns([1, 1])
        with c1:
            username = st.text_input(
                "Usuário ou e-mail",
                placeholder="seunome@exemplo.com",
                key="username",
            )
        with c2:
            show_pwd = st.toggle("Mostrar senha", value=False)
        password = st.text_input(
            "Senha",
            type=("text" if show_pwd else "password"),
            placeholder="••••••••",
            key="password",
        )
        remember = st.checkbox("Lembrar-me", value=True, help="Mantém você conectado neste navegador.")
        submitted = st.form_submit_button("Entrar", use_container_width=True)

    # Validação
    if submitted:
        if not username or not password:
            st.error("Preencha usuário e senha.")
        else:
            users = _get_auth_users()
            ok = isinstance(users, dict) and users.get(username) == password
            if ok:
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = username
                if remember:
                    st.session_state["remember_me"] = True
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                if users is None:
                    st.info(
                        "Nenhuma base de usuários configurada. "
                        "Crie `.streamlit/secrets.toml` (ver exemplo no topo) "
                        "ou defina PORTAL_USERS_JSON."
                    )
                st.error("Credenciais inválidas.")

    st.markdown("</div></div>", unsafe_allow_html=True)

def _clear_login_css_after_auth():
    """Remove impactos visuais do overlay após login."""
    st.markdown(
        "<style>#login-backdrop{display:none} #login-overlay{position:static;transform:none;width:auto;}"
        ".login-card{background:transparent;box-shadow:none;border:none;padding:0}</style>",
        unsafe_allow_html=True,
    )

# =============== Fluxo de Página ===============

if not st.session_state.get("authenticated"):
    # Mostra somente o overlay até autenticar; o resto do layout permanece intacto por baixo.
    _show_login_overlay()
    st.stop()

# A partir daqui: usuário autenticado
_clear_login_css_after_auth()

# ======= Seu layout do portal (exemplo – substitua pelo seu conteúdo) =======
st.markdown("### 🎛️ Seus Aplicativos")  # mantenha seus títulos/estilos
st.caption("Exemplo – substitua pelo seu grid real de apps.")

# Grade simples de botões (placeholder)
c1, c2, c3 = st.columns(3)
with c1:
    st.button("App 1", use_container_width=True)
with c2:
    st.button("App 2", use_container_width=True)
with c3:
    st.button("App 3", use_container_width=True)

st.divider()
st.write("Você está logado como **{}**.".format(st.session_state.get("current_user", "")))

# (Opcional) botão de sair
if st.button("Sair"):
    for k in ("authenticated", "current_user", "remember_me"):
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()



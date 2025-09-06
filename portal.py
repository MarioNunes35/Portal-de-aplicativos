import os
import json
import streamlit as st

st.set_page_config(page_title="Portal", page_icon="🚀", layout="wide")

# ---------- styles ----------
st.markdown(
    """
    <style>
    .main-block { display:flex; align-items:center; justify-content:center; min-height:88vh; }
    .card { background:#1f1f1f; border-radius:18px; padding:56px 56px 40px 56px;
            box-shadow:0 10px 40px rgba(0,0,0,.5); max-width:760px; width:92%;
            border:1px solid rgba(255,255,255,.06); }
    .card h1 { font-size:56px; margin:0 0 4px 0; line-height:1.05; }
    .card p.subtitle { color:#9aa0a6; font-size:22px; margin:10px 0 36px 0; }
    </style>
    """, unsafe_allow_html=True
)

# ---------- login card ----------
st.markdown('<div class="main-block"><div class="card">', unsafe_allow_html=True)
st.markdown("<h1>🚀 Acesso ao<br>Portal</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Entre com suas credenciais para continuar</p>', unsafe_allow_html=True)

with st.form("login_form", clear_on_submit=False):
    c1, c2 = st.columns([1,1])
    with c1:
        username = st.text_input("Usuário ou e-mail", placeholder="seunome@exemplo.com", key="username")
    with c2:
        show_pwd = st.toggle("Mostrar senha", value=False)
    password = st.text_input("Senha", type=("text" if show_pwd else "password"), placeholder="••••••••", key="password")
    remember = st.checkbox("Lembrar-me", value=True, help="Mantém você conectado neste navegador.")
    submitted = st.form_submit_button("Entrar", use_container_width=True)

# ---------- simple credential check ----------
ok = False
auth_users = None
if "auth" in st.secrets and "users" in st.secrets["auth"]:
    auth_users = dict(st.secrets["auth"]["users"])
elif os.getenv("PORTAL_USERS_JSON"):
    try:
        auth_users = json.loads(os.getenv("PORTAL_USERS_JSON"))
    except Exception:
        auth_users = None

if submitted:
    if not username or not password:
        st.error("Preencha usuário e senha.")
    else:
        if isinstance(auth_users, dict):
            ok = auth_users.get(username) == password
        else:
            ok = False
        if ok:
            st.success("Login realizado com sucesso!")
            st.session_state["authenticated"] = True
            st.session_state["current_user"] = username
            if remember:
                st.session_state["remember_me"] = True
        else:
            st.error("Credenciais inválidas.")

# ---------- after login ----------
if st.session_state.get("authenticated"):
    st.divider()
    st.write(f"Bem-vindo, **{st.session_state.get('current_user', '')}**!")
    st.caption("Substitua este bloco pelo conteúdo do portal (lista de aplicativos).")
    # Exemplo de grade de apps protegida:
    # col1, col2, col3 = st.columns(3)
    # with col1: st.button("App 1", use_container_width=True)
    # ...

st.markdown('</div></div>', unsafe_allow_html=True)



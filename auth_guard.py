# auth_guard.py
# Guard de autenticação/autorização para apps Streamlit com OIDC (Google)
# Uso (no topo do app):
#   from auth_guard import guard, userbox
#   user = guard(required_role=None)  # opcional: required_role="admin"
#   userbox(user)  # mostra email e botão de sair na sidebar
#
# Requer nos Secrets:
# [oidc]
# client_id = "..."
# client_secret = "..."
# redirect_uri = "https://SEU-APP.streamlit.app/oauth2callback"
# discovery_url = "https://accounts.google.com/.well-known/openid-configuration"
# cookie_secret = "string-aleatoria"
#
# [auth]
# allowed_emails = ["pessoa1@gmail.com", "cliente2@gmail.com"]
# # opcional:
# allowed_domains = ["empresa.com"]
#
# [roles]
# admin = ["voce@gmail.com"]
# viewer = ["cliente2@gmail.com"]

from __future__ import annotations
from typing import Optional, Set, Tuple
import streamlit as st

def _get_allowlists() -> Tuple[Set[str], Set[str]]:
    auth = st.secrets.get("auth", {})
    emails = { (e or "").strip().lower() for e in auth.get("allowed_emails", []) }
    domains = { (d or "").strip().lower() for d in auth.get("allowed_domains", []) }
    return emails, domains

def _allowed(email: str, emails: Set[str], domains: Set[str]) -> bool:
    if not email:
        return False
    if email in emails:
        return True
    # liberação por domínio (Workspace)
    return any(email.endswith(f"@{d}") for d in domains)

def _has_role(email: str, role: Optional[str]) -> bool:
    if role is None:
        return True
    roles = st.secrets.get("roles", {})
    permitted = { (e or "").strip().lower() for e in roles.get(role, []) }
    return email in permitted

def guard(required_role: Optional[str] = None):
    """
    Garante login OIDC (Google) e autorização por allowlist/role.
    Retorna o objeto st.user se autorizado. Caso contrário, encerra a execução do app.
    """
    # Autenticação: exige login antes de renderizar
    if not getattr(st.user, "is_logged_in", False):
        st.login("oidc")  # redireciona para o IdP
        st.stop()

    # (opcional) conferir se o e-mail do Google foi verificado
    if hasattr(st.user, "email_verified") and not getattr(st.user, "email_verified", True):
        st.error("Seu e-mail Google não está verificado. Tente outra conta ou verifique seu e-mail.")
        st.stop()

    email = (getattr(st.user, "email", "") or "").lower()

    emails, domains = _get_allowlists()
    if not _allowed(email, emails, domains):
        st.error("Acesso não autorizado. Solicite liberação ao administrador.")
        st.stop()

    # Controle por papéis (se desejar)
    if not _has_role(email, required_role):
        st.error("Você não tem permissão para acessar esta seção.")
        st.stop()

    return st.user

def userbox(user=None, show_logout: bool = True):
    """Exibe info do usuário na sidebar e botão de sair."""
    if user is None:
        user = getattr(st, "user", None)

    with st.sidebar:
        if user and getattr(user, "email", None):
            st.caption(f"Logado como: {user.email}")
        if show_logout:
            st.button("Sair", on_click=st.logout)

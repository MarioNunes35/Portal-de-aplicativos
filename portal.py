import streamlit as st
from typing import Dict, List, Optional

# Configuração da página
st.set_page_config(
    page_title="Portal Unificado",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Lista de aplicativos
APPS: List[Dict[str, str]] = [
    {
        "title": "TG/ADT Events",
        "desc": "Análise de eventos (TG/ADT) e extração de parâmetros.",
        "href": "https://apptgadtgeventspy-hqeqt7yljzwra3r7nmdhju.streamlit.app/"
    },
    {
        "title": "Stack Graph",
        "desc": "Gráficos empilhados para dados multidimensionais.",
        "href": "https://appstackgraphpy-ijew8pyut2jkc4x4pa7nbv.streamlit.app/"
    },
    {
        "title": "Rheology App",
        "desc": "Análise de reologia e ajuste de modelos.",
        "href": "https://apprheologyapppy-mbkr3wmbdb76t3ysvlfecr.streamlit.app/"
    },
    {
        "title": "Mechanical Properties",
        "desc": "Propriedades mecânicas e curvas tensão—deformação.",
        "href": "https://appmechanicalpropertiespy-79l8dejt9kfmmafantscut.streamlit.app/"
    },
    {
        "title": "Baseline Smoothing",
        "desc": "Suavização e correção de linha de base em sinais.",
        "href": "https://appbaselinesmoothinglineplotpy-mvx5cnwr5szg4ghwpbx379.streamlit.app/"
    },
    {
        "title": "Isotherms App",
        "desc": "Isotermas de adsorção (vários modelos).",
        "href": "https://isothermsappfixedpy-ropmkqgbbxujhvkd6pfxgi.streamlit.app/"
    },
    {
        "title": "Histograms",
        "desc": "Geração e análise de histogramas.",
        "href": "https://apphistogramspy-b3kfy7atbdhgxx8udeduma.streamlit.app/"
    },
    {
        "title": "Column 3D Line",
        "desc": "Coluna 3D com linha sobreposta.",
        "href": "https://column3dpyline2inmoduleimportdash-kdqhfwwyyhdtb48x4z3kkn.streamlit.app/"
    },
    {
        "title": "Crystallinity DSC/XRD",
        "desc": "Cristalinidade por DSC/XRD.",
        "href": "https://appcrystallinitydscxrdpy-wqtymsdcco2nuem7fv3hve.streamlit.app/"
    },
    {
        "title": "Column 3D",
        "desc": "Gráficos de barras em 3D (colunas).",
        "href": "https://column3dpy-cskafquxluvyv23hbnhxli.streamlit.app/"
    },
    {
        "title": "Kinetic Models",
        "desc": "Modelagem cinética com múltiplos modelos.",
        "href": "https://kineticmodelsapppy-fz8qyt64fahje5acofqpcm.streamlit.app/"
    },
    {
        "title": "Python Launcher",
        "desc": "Launcher utilitário para scripts Python.",
        "href": "https://pythonlauncherfixedpy-yschqh6qwzl526xurdeoca.streamlit.app/"
    }
]

# =============================================================================
# FUNÇÕES DE AUTENTICAÇÃO
# =============================================================================

def get_user_info():
    """Obtém informações do usuário logado"""
    try:
        # Tenta acessar o objeto user do Streamlit
        user = getattr(getattr(st, "context", None), "user", None)
        if not user:
            user = getattr(st, "user", None)
        return user
    except:
        return None

def get_user_email() -> str:
    """Extrai o email do usuário logado"""
    user = get_user_info()
    if not user:
        return ""
    
    # Tenta diferentes atributos onde o email pode estar
    for attr in ("email", "primaryEmail", "preferred_username"):
        email = getattr(user, attr, None)
        if email:
            return str(email)
    
    # Se não encontrou email nos atributos, tenta converter o objeto user diretamente
    try:
        user_str = str(user).strip()
        if "@" in user_str:
            return user_str
    except:
        pass
    
    return ""

def is_authenticated() -> bool:
    """Verifica se o usuário está autenticado"""
    return bool(get_user_email())

def check_google_secrets() -> bool:
    """Verifica se as credenciais do Google estão configuradas"""
    try:
        secrets = dict(st.secrets)
        
        # Verifica formato [auth.google]
        if "auth" in secrets and "google" in secrets["auth"]:
            google_config = secrets["auth"]["google"]
            required_keys = ["client_id", "client_secret"]
            return all(google_config.get(key) for key in required_keys)
        
        # Verifica formato [auth] com provider="google"
        if "auth" in secrets:
            auth_config = secrets["auth"]
            if auth_config.get("provider", "").lower() == "google":
                required_keys = ["client_id", "client_secret"]
                return all(auth_config.get(key) for key in required_keys)
        
        return False
    except:
        return False

def test_redirect_uri():
    """Função para testar diferentes redirect URIs"""
    st.warning("🧪 **Modo de Teste de Redirect URI**")
    
    # Detecta a URL base
    try:
        app_url = f"https://{st.context.headers.get('host', 'app-unificadopy-j9wgzbt2sqm5pgaeqzxyme.streamlit.app')}"
    except:
        app_url = "https://app-unificadopy-j9wgzbt2sqm5pgaeqzxyme.streamlit.app"
    
    st.write(f"**URL base detectada:** {app_url}")
    
    # Lista de URIs para testar
    test_uris = [
        "_stcore/oauth2callback",
        "_stcore/auth/callback", 
        "auth/callback",
        "oauth2callback",
        "_streamlit/auth/callback"
    ]
    
    st.write("**Selecione uma URI para testar:**")
    
    for i, uri_path in enumerate(test_uris):
        full_uri = f"{app_url}/{uri_path}"
        if st.button(f"Testar: {full_uri}", key=f"test_{i}"):
            # Temporariamente modifica os secrets para teste
            if "auth" in st.secrets and "google" in st.secrets["auth"]:
                st.session_state.test_redirect_uri = full_uri
                st.success(f"✅ URI de teste selecionada: {full_uri}")
                st.write("**Agora configure esta URI nos seus secrets:**")
                st.code(f'''
[auth]
cookie_secret = "sua_chave_secreta"

[auth.google]
client_id = "{st.secrets["auth"]["google"].get("client_id", "SEU_CLIENT_ID")}"
client_secret = "{st.secrets["auth"]["google"].get("client_secret", "SEU_CLIENT_SECRET")}"
redirect_uri = "{full_uri}"
''', language="toml")
                st.write("**E adicione esta mesma URI no Google Cloud Console!**")
    
    return st.session_state.get('test_redirect_uri')

def show_auth_config_help():
    """Mostra as instruções de configuração dos secrets"""
    st.error("🔐 Configuração de autenticação necessária")
    
    # Primeiro, oferece o modo de teste
    st.info("💡 **Vamos descobrir a URI correta para sua aplicação!**")
    
    if st.button("🧪 Ativar Modo de Teste de Redirect URI", type="primary"):
        st.session_state.show_test_mode = True
    
    if st.session_state.get('show_test_mode', False):
        test_redirect_uri()
        return
    
    # Detecta a URL atual da aplicação
    try:
        app_url = f"https://{st.context.headers.get('host', 'app-unificadopy-j9wgzbt2sqm5pgaeqzxyme.streamlit.app')}"
    except:
        app_url = "https://app-unificadopy-j9wgzbt2sqm5pgaeqzxyme.streamlit.app"
    
    # Múltiplas possibilidades de redirect URI
    possible_uris = [
        f"{app_url}/_stcore/oauth2callback",
        f"{app_url}/_stcore/auth/callback",
        f"{app_url}/auth/callback",
        f"{app_url}/oauth2callback"
    ]
    
    st.markdown("""
    Para usar este portal, você precisa configurar a autenticação Google nos **Secrets** do Streamlit Cloud.
    
    ### 📋 Configuração Manual:
    
    **1. Configure os Secrets no Streamlit Cloud:**
    """)
    
    st.code(f"""
[auth]
cookie_secret = "SUA_CHAVE_SECRETA_LONGA_E_ALEATORIA_AQUI"

[auth.google]
client_id = "SEU_GOOGLE_CLIENT_ID"
client_secret = "SEU_GOOGLE_CLIENT_SECRET"
redirect_uri = "{possible_uris[0]}"
""", language="toml")
    
    st.markdown("""
    **2. No Google Cloud Console - Adicione TODAS estas URLs aos "Authorized redirect URIs":**
    
    (Adicione todas para garantir compatibilidade)
    """)
    
    for uri in possible_uris:
        st.code(uri, language="text")
    
    st.markdown("""
    **3. Passos no Google Cloud Console:**
    - Acesse o [Google Cloud Console](https://console.cloud.google.com/)
    - Crie um projeto ou selecione um existente
    - Habilite a "Google Sign-In API" ou "Identity Platform"
    - Vá em "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
    - Configure como "Web application"
    - Cole TODAS as URLs acima em "Authorized redirect URIs"
    
    **4. Gere uma chave secreta para cookies:**
    """)
    
    st.code("""
import secrets
print(secrets.token_urlsafe(32))
""", language="python")
    
    st.warning("⚠️ **IMPORTANTE**: Adicione TODAS as URLs de redirect no Google Cloud Console para garantir que funcione!")
    
    with st.expander("🔍 Debug dos Secrets (apenas estrutura)"):
        try:
            secrets_keys = list(st.secrets.keys())
            debug_info = {"sections_found": secrets_keys}
            
            if "auth" in st.secrets:
                debug_info["auth_keys"] = list(st.secrets["auth"].keys())
                if "google" in st.secrets["auth"]:
                    debug_info["auth_google_keys"] = list(st.secrets["auth"]["google"].keys())
            
            st.json(debug_info)
        except Exception as e:
            st.write(f"Erro ao ler secrets: {str(e)}")
    
    with st.expander("🌐 URLs de Redirect Detectadas"):
        st.write("**URL da aplicação detectada:**", app_url)
        st.write("**Possíveis redirect URIs:**")
        for i, uri in enumerate(possible_uris):
            st.write(f"{i+1}. `{uri}`")

def handle_authentication():
    """Gerencia o processo de autenticação"""
    # Verifica se as credenciais estão configuradas
    if not check_google_secrets():
        show_auth_config_help()
        st.stop()
    
    # Se não está autenticado, inicia o processo de login
    if not is_authenticated():
        st.info("🔐 **Autenticação necessária**")
        st.markdown("Clique no botão abaixo para fazer login com sua conta Google.")
        
        try:
            st.login("google")
            st.stop()
        except Exception as e:
            st.error(f"Erro no processo de login: {str(e)}")
            st.markdown("**Possíveis soluções:**")
            st.markdown("- Verifique se as credenciais Google estão corretas nos Secrets")
            st.markdown("- Confirme se a URL de redirect está configurada no Google Cloud Console")
            st.stop()

def show_user_info():
    """Mostra informações do usuário logado"""
    email = get_user_email()
    if email:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"🔐 Conectado como: **{email}**")
        with col2:
            if st.button("🚪 Logout", type="secondary"):
                # Limpa a sessão (método pode variar dependendo da versão do Streamlit)
                st.rerun()

# =============================================================================
# INTERFACE DO USUÁRIO
# =============================================================================

def render_apps_grid(apps: List[Dict[str, str]]):
    """Renderiza a grade de aplicativos com busca"""
    
    # Campo de busca
    search_query = st.text_input(
        "🔎 Buscar aplicativo", 
        placeholder="Digite parte do nome ou descrição...",
        help="Busque por nome ou descrição do aplicativo"
    ).strip().lower()
    
    # Filtrar apps baseado na busca
    if search_query:
        filtered_apps = [
            app for app in apps 
            if search_query in app["title"].lower() or search_query in app["desc"].lower()
        ]
    else:
        filtered_apps = apps
    
    # Mostrar quantidade de resultados
    if search_query:
        st.write(f"📊 Encontrados **{len(filtered_apps)}** de **{len(apps)}** aplicativos")
    else:
        st.write(f"📊 Total de **{len(apps)}** aplicativos disponíveis")
    
    if not filtered_apps:
        st.warning("🔍 Nenhum aplicativo encontrado com esse termo de busca.")
        return
    
    # Grade de aplicativos (3 colunas)
    cols = st.columns(3)
    
    for i, app in enumerate(filtered_apps):
        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(f"🔧 {app['title']}")
                st.write(app["desc"])
                st.link_button(
                    "🚀 Abrir Aplicativo", 
                    app["href"], 
                    use_container_width=True,
                    type="primary"
                )

def main():
    # Gerencia autenticação
    handle_authentication()
    
    # Cabeçalho
    st.title("🚀 Portal Unificado de Aplicativos")
    st.markdown("**Central de acesso aos aplicativos de análise de dados**")
    
    # Mostra informações do usuário
    show_user_info()
    
    st.divider()
    
    # Grade de aplicativos
    render_apps_grid(APPS)
    
    # Rodapé com informações
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.expander("ℹ️ Sobre este Portal"):
            st.markdown("""
            Este portal centraliza o acesso a todos os aplicativos de análise de dados disponíveis.
            
            **Categorias disponíveis:**
            - 📊 **Análise de Dados**: TG/ADT Events, Stack Graph, Histograms
            - 🔬 **Propriedades de Materiais**: Rheology, Mechanical Properties, Crystallinity
            - 📈 **Modelagem**: Kinetic Models, Isotherms
            - 🎨 **Visualização**: Column 3D, Baseline Smoothing
            - 🛠️ **Utilitários**: Python Launcher
            """)
    
    with col2:
        with st.expander("🔧 Dicas de Uso"):
            st.markdown("""
            - Use o campo de **busca** para encontrar apps rapidamente
            - Todos os links abrem em **nova aba**
            - Apps são **independentes** entre si
            - **Login necessário** para acesso aos aplicativos
            """)

if __name__ == "__main__":
    main()











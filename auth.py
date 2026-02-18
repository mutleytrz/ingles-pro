from __future__ import annotations
# auth.py — Camada de autenticação (email + senha)

import streamlit as st
import streamlit_authenticator as stauth
import database
import config
import email_service
import random
from typing import Optional


def _build_authenticator():
    """Constrói o objeto Authenticate a partir dos usuários no banco."""
    creds = database.get_all_users()
    if not creds["usernames"]:
        return None

    # Ler SECRET_KEY em tempo real (st.secrets > config)
    try:
        cookie_secret = st.secrets.get("SECRET_KEY", None) or config.SECRET_KEY
    except Exception:
        cookie_secret = config.SECRET_KEY

    authenticator = stauth.Authenticate(
        credentials={"usernames": creds["usernames"]},
        cookie_name="ingles_pro_session_v2",
        cookie_key=cookie_secret,
        cookie_expiry_days=30,
        auto_hash=False,
    )
    # [DEBUG]
    # print(f"[AUTH] Authenticator built. Cookie: ingles_pro_cookie. Secret len: {len(str(cookie_secret))}")
    return authenticator


def _generate_code() -> str:
    """Gera codigo de 6 digitos."""
    return str(random.randint(100000, 999999))


def _get_smtp_config() -> dict:
    """Busca config SMTP em tempo real (st.secrets > config)."""
    smtp = {"host": "", "user": "", "password": "", "port": 587, "from_name": "English Pro AI"}
    # Tenta st.secrets primeiro (Streamlit Cloud)
    try:
        smtp["host"] = st.secrets.get("SMTP_HOST", "") or ""
        smtp["user"] = st.secrets.get("SMTP_USER", "") or ""
        smtp["password"] = st.secrets.get("SMTP_PASS", "") or ""
        smtp["port"] = int(st.secrets.get("SMTP_PORT", 587))
        smtp["from_name"] = st.secrets.get("SMTP_FROM_NAME", "English Pro AI") or "English Pro AI"
    except Exception:
        pass
    # Fallback para config.py se st.secrets nao tiver
    if not smtp["host"]:
        smtp["host"] = config.SMTP_HOST
    if not smtp["user"]:
        smtp["user"] = config.SMTP_USER
    if not smtp["password"]:
        smtp["password"] = config.SMTP_PASS
    return smtp


def _is_smtp_configured() -> bool:
    """Verifica se SMTP esta realmente configurado (nao placeholder)."""
    smtp = _get_smtp_config()
    if not smtp["host"] or not smtp["user"]:
        return False
    placeholders = ["seu_email@gmail.com", "your_email@gmail.com", "you@example.com", ""]
    if smtp["user"].strip().lower() in placeholders:
        return False
    if not smtp["password"] or smtp["password"].strip() in ["sua_senha_de_app", "your_app_password", ""]:
        return False
    return True


def render_email_verification(username: str):
    """Tela de verificacao de codigo."""
    
    # MODO DEV: Se nao tem SMTP, ajuda o usuario mostrando o codigo
    dev_message = ""
    if not config.SMTP_HOST or not config.SMTP_USER:
        # Pega o codigo do banco rapidinho
        try:
            conn = database._get_conn()
            row = conn.execute("SELECT verification_code FROM users WHERE username=?", (username,)).fetchone()
            if row:
                dev_message = f"<div style='background:#fef3c7; color:#d97706; padding:10px; border-radius:8px; margin-bottom:15px; text-align:center; font-weight:bold;'>🔧 MODO DEV (Sem Email): Seu código é {row['verification_code']}</div>"
            conn.close()
        except:
            pass

    st.markdown(f"""
    <div style='text-align:center; animation:fadeInUp 0.5s ease-out; background:rgba(139,92,246,0.05); padding:30px; border-radius:20px; border:1px solid rgba(139,92,246,0.2);'>
        <h2 style='color:#fff;'>📧 Verifique seu Email</h2>
        <p style='color:#a78bfa;'>Enviamos um código de 6 dígitos para o email cadastrado em <strong>{username}</strong>.</p>
        {dev_message}
    </div>
    """, unsafe_allow_html=True)

    with st.form("verify_form"):
        code_input = st.text_input("Código de Verificação", max_chars=6, placeholder="000000", key="ver_code").strip()
        submit = st.form_submit_button("✅ CONFIRMAR CÓDIGO", use_container_width=True)

    if submit:
        if database.verify_email_code(username, code_input):
            st.success("✅ Email verificado com sucesso! Você já pode entrar.")
            if "pending_verification_user" in st.session_state:
                del st.session_state["pending_verification_user"]
            # NUCLEAR OPTION: Clear authenticator cache to force reload of users from DB
            if "_authenticator_instance" in st.session_state:
                del st.session_state["_authenticator_instance"]
            st.balloons()
            st.rerun()
        else:
            st.error("❌ Código inválido ou expirado.")
    
    if st.button("⬅ Voltar ao Login"):
        if "pending_verification_user" in st.session_state:
             del st.session_state["pending_verification_user"]
        st.rerun()


def render_register():
    """Formulário de cadastro de novo usuário (Premium Look)."""
    st.markdown("""
<div style='text-align:center; margin-bottom:20px; animation:fadeInUp 0.5s ease-out;'>
<div style='background:rgba(139,92,246,0.08); display:inline-block; padding:14px 28px; border-radius:16px; border:1px solid rgba(139,92,246,0.15);'>
<h3 style='margin:0; font-size:18px; color:#c4b5fd !important;'>📝 Criar Nova Conta</h3>
</div>
<p style='color:#94a3b8; font-size:14px; margin-top:8px;'>Informe um email válido para ativar sua conta.</p>
</div>
""", unsafe_allow_html=True)

    with st.form("register_form"):
        st.markdown("<div style='display:flex; gap:20px;'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            new_user = st.text_input("👤 Usuário", key="reg_user", placeholder="ex: aluno123")
            new_email = st.text_input("📧 Email", key="reg_email", placeholder="seu@email.com")
        with c2:
            new_name = st.text_input("📛 Nome", key="reg_name", placeholder="Seu nome")
        st.markdown("</div>", unsafe_allow_html=True)
        
        c3, c4 = st.columns(2)
        with c3:
             new_pass = st.text_input("🔑 Senha", type="password", key="reg_pass", placeholder="••••")
        with c4:
             new_pass2 = st.text_input("🔑 Confirmar Senha", type="password", key="reg_pass2", placeholder="••••")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 CRIAR CONTA", use_container_width=True)

    if submitted:
        if not new_user or not new_name or not new_pass:
            st.error("⚠️ Preencha todos os campos obrigatórios (Usuário, Nome, Senha).")
            return
        # Sanitização de username: só alfanumérico e underscore
        import re
        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', new_user):
            st.error("⚠️ Usuário deve ter 3-30 caracteres (letras, números ou _).")
            return
        if len(new_name.strip()) < 2:
            st.error("⚠️ Nome deve ter pelo menos 2 caracteres.")
            return
        new_user = new_user.strip().lower()
        new_name = new_name.strip()
        if new_pass != new_pass2:
            st.error("⚠️ As senhas não coincidem.")
            return
        if len(new_pass) < 4:
            st.error("⚠️ A senha deve ter pelo menos 4 caracteres.")
            return

        hashed = stauth.Hasher().hash(new_pass)
        
        if _is_smtp_configured() and new_email:
            # MODO PRODUCAO: cadastro com verificacao de email
            verification_code = _generate_code()
            ok = database.create_user_with_email(new_user, new_name, hashed, new_email, verification_code)
            if ok:
                if "_authenticator_instance" in st.session_state:
                    del st.session_state["_authenticator_instance"]
                sent = email_service.send_verification_email(new_email, verification_code)
                if sent:
                    st.session_state["pending_verification_user"] = new_user
                    st.success(f"✅ Conta criada! Enviamos um código para {new_email}.")
                    st.rerun()
                else:
                    st.warning("⚠️ Conta criada, mas falha ao enviar email.")
            else:
                st.error(f"❌ Usuário '{new_user}' já existe.")
        else:
            # MODO SEM EMAIL: cadastro direto, sem verificacao
            ok = database.create_user(new_user, new_name, hashed)
            if ok:
                # NUCLEAR OPTION: Clear authenticator cache to force reload of users from DB
                if "_authenticator_instance" in st.session_state:
                    del st.session_state["_authenticator_instance"]
                
                st.success("✅ Conta criada com sucesso! A página será atualizada...")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ Usuário '{new_user}' já existe.")


import hmac
import hashlib
import json
import base64
import time

# ... (imports existing) ...

def _get_secret_key():
    """Retorna chave secreta para assinatura."""
    try:
        return st.secrets.get("SECRET_KEY", config.SECRET_KEY)
    except:
        return config.SECRET_KEY

def create_session_token(username: str) -> str:
    """Cria um token assinado para a URL."""
    payload = {
        "u": username,
        "exp": time.time() + (30 * 24 * 3600)  # 30 dias
    }
    payload_str = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = hmac.new(
        _get_secret_key().encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{payload_str}.{signature}"

def validate_session_token(token: str) -> Optional[str]:
    """Valida o token da URL e retorna o username se valido."""
    try:
        payload_str, signature = token.split(".")
        # Recalcula assinatura
        expected_sig = hmac.new(
            _get_secret_key().encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if hmac.compare_digest(expected_sig, signature):
            payload = json.loads(base64.urlsafe_b64decode(payload_str).decode())
            if payload["exp"] > time.time():
                return payload["u"]
    except Exception:
        pass
    return None

def render_login() -> Optional[str]:
    """
    Renderiza a tela de login + cadastro com fluxo de email.
    """
    # -----------------------------------------------------------
    # FIX: Preventing DuplicateElementKey (CookieManager conflict)
    # -----------------------------------------------------------
    # -----------------------------------------------------------
    # FIX: Preventing DuplicateElementKey (CookieManager conflict)
    # -----------------------------------------------------------
    # Force rebuild if not present OR if we suspect it's stale (e.g. just registered)
    if "_authenticator_instance" not in st.session_state:
        st.session_state["_authenticator_instance"] = _build_authenticator()
    
    authenticator = st.session_state["_authenticator_instance"]

    # ------------------------------------------------------------------
    # URL SESSION CHECK (NUCLEAR OPTION ☢️)
    # ------------------------------------------------------------------
    
    # [LOGOUT DETECTION] - REMOVED TO FIX BUG
    # Do not intercept logout here. Let it propagate to render_logout function.
    pass

    # Se nao esta logado, checa se tem token na URL
    if st.session_state.get("authentication_status") is not True:
        query_params = st.query_params
        if "session" in query_params:
            token = query_params["session"]
            valid_user = validate_session_token(token)
            if valid_user:
                # Login automatico via URL
                st.session_state["authentication_status"] = True
                st.session_state["username"] = valid_user
                st.session_state["name"] = valid_user 
                st.session_state["logout"] = False
                st.rerun()
    # ------------------------------------------------------------------

    # 1. Se estiver pendente de verificação, mostra tela de código
    pending_user = st.session_state.get("pending_verification_user")
    if pending_user:
        # Header simplificado
        st.markdown("<div style='text-align:center; margin:40px 0;'><h1>🚀 ENGLISH PRO</h1></div>", unsafe_allow_html=True)
        
        _sp1, c_main, _sp2 = st.columns([1, 2, 1])
        with c_main:
            render_email_verification(pending_user)
        return None

    # 2. Tela Normal de Login
    # ... (Keep existing UI code) ...
    st.markdown("""
<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding-top:60px; margin-bottom:50px; animation:fadeInUp 0.7s cubic-bezier(0.2, 0.8, 0.2, 1);">
<div class="sys-badge" style="border-color:rgba(6,182,212,0.5); background:rgba(6,182,212,0.1); color:#22d3ee; margin-bottom:20px; box-shadow:0 0 15px rgba(6,182,212,0.2);">
<span style="animation:pulse 2s infinite;">●</span> SISTEMA V2.0: ONLINE
</div>
<div style="font-size:72px; font-weight:900; letter-spacing:-2px; line-height:1.0; margin-bottom:15px; font-family:'Outfit',sans-serif; text-align:center; filter: drop-shadow(0 0 20px rgba(139,92,246,0.2));">
<span style="color:#fff;">ENGLISH</span>
<span style="background:linear-gradient(135deg, #8b5cf6 0%, #06b6d4 50%, #f472b6 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">PRO</span>
<span style="font-size:40px; vertical-align:top; margin-left:5px;">🚀</span>
</div>
<div style="background:linear-gradient(90deg, transparent, rgba(139,92,246,0.1), transparent); height:1px; width:200px; margin:10px 0 20px;"></div>
<div style="text-align:center; max-width:700px;">
<h2 style="font-size:26px; color:#e2e8f0; margin-bottom:10px; font-weight:700;">
A Revolução da sua Fluência.
</h2>
<p style="color:#94a3b8; font-size:18px; line-height:1.6; font-family:'Outfit',sans-serif; font-weight:400;">
Plataforma de ensino com <strong>Inteligência Artificial</strong>, reconhecimento de voz em tempo real e metodologia imersiva.
</p>
</div>
<div style="margin-top:25px; color:#64748b; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:1px; display:flex; align-items:center; gap:10px;">
<span style="width:20px; height:1px; background:#64748b;"></span>
ÁREA EXCLUSIVA DE MEMBROS
<span style="width:20px; height:1px; background:#64748b;"></span>
</div>
</div>
""", unsafe_allow_html=True)

    _sp1, c_main, _sp2 = st.columns([1.5, 2, 1.5])
    
    with c_main:
        if authenticator is not None:
            authenticator.login(
                location="main",
                fields={
                    "Form name": "🔐 Acessar Plataforma",
                    "Username": "Usuário",
                    "Password": "Senha",
                    "Login": "ENTRAR NO SISTEMA",
                },
            )

            # ------------------------------------------------------------------
            # CRITICAL FIX: FORCE SESSION CLEANUP IF NOT AUTHENTICATED
            # ------------------------------------------------------------------
            # Se não logou (está na tela de login), GARANTIR que não sobrou lixo de sessões anteriores
            if st.session_state.get("authentication_status") is not True:
                keys_to_nuke = ['xp', 'indice', 'porc_atual', 'tentativa', 'pagina', 'arquivo_atual', '_progresso_carregado']
                for k in keys_to_nuke:
                    if k in st.session_state:
                         del st.session_state[k]
            # ------------------------------------------------------------------

            if st.session_state.get("authentication_status") is True:
                # Checa se email verificado
                username_logged = st.session_state.get("username")
                
                if database.is_email_verified(username_logged):
                    st.session_state["_authenticator"] = authenticator
                    
                    # ------------------------------------------------------------------
                    # NUCLEAR URL PERSISTENCE ☢️
                    # ------------------------------------------------------------------
                    # Só atualiza o token se não existir ou se for inválido
                    # Isso evita o loop infinito de refresh da URL (que causa o bug do logout)
                    current_token = st.query_params.get("session")
                    if not current_token or not validate_session_token(current_token):
                         token = create_session_token(username_logged)
                         st.query_params["session"] = token
                    # ------------------------------------------------------------------

                    return username_logged
                else:
                    # Nao verificado -> gera novo codigo e reenvia email
                    if _is_smtp_configured():
                        new_code = _generate_code()
                        # Busca o email do usuario
                        try:
                            conn = database._get_conn()
                            row = conn.execute("SELECT email FROM users WHERE username=?", (username_logged,)).fetchone()
                            user_email = row["email"] if row else None
                            # Atualiza codigo no banco
                            conn.execute("UPDATE users SET verification_code=? WHERE username=?", (new_code, username_logged))
                            conn.commit()
                            conn.close()
                            if user_email:
                                email_service.send_verification_email(user_email, new_code)
                        except Exception as e:
                            print(f"[ERR] Falha ao reenviar codigo: {e}")
                        authenticator.logout("main")
                        st.session_state["pending_verification_user"] = username_logged
                        st.rerun()
                    else:
                        # Sem SMTP: auto-verificar o usuario
                        try:
                            conn = database._get_conn()
                            conn.execute("UPDATE users SET email_verified=1 WHERE username=?", (username_logged,))
                            conn.commit()
                            conn.close()
                        except Exception:
                            pass
                        st.session_state["_authenticator"] = authenticator
                        
                        # NUCLEAR URL PERSISTENCE (fallback path)
                        current_token = st.query_params.get("session")
                        if not current_token or not validate_session_token(current_token):
                             token = create_session_token(username_logged)
                             st.query_params["session"] = token
                        
                        return username_logged

            elif st.session_state.get("authentication_status") is False:
                st.error("❌ Usuário ou senha incorretos.")
                # NUCLEAR OPTION: Se falhou, limpa qualquer resquicio de sessao anterior
                # Isso ajuda se o cookie estiver em conflito com o estado interno
                keys_to_nuke = ['xp', 'indice', 'porc_atual', 'tentativa', 'pagina', 'arquivo_atual']
                for k in keys_to_nuke:
                     if k in st.session_state:
                          del st.session_state[k]
        else:
            st.info("👋 Bem-vindo! Crie o primeiro usuário admin abaixo.")

        st.markdown("<div class='divider-glow'></div>", unsafe_allow_html=True)
        render_register()
    
    return None


def render_logout(location="sidebar"):
    """Botão de logout oficial."""
    authenticator = st.session_state.get("_authenticator_instance")
    
    # Se estivermos na main, style it better
    if location == "main":
        st.markdown("<br><hr style='border-color:rgba(139,92,246,0.2);'><br>", unsafe_allow_html=True)
        # ... styles ...
        st.markdown("""
        <style>
        div[data-testid="stbutton"] > button { width: 100%; }
        div.stButton > button {
            border: 1px solid rgba(239, 68, 68, 0.3);
            background: rgba(239, 68, 68, 0.1);
            color: #fca5a5;
        }
        div.stButton > button:hover {
            border-color: rgba(239, 68, 68, 0.6);
            background: rgba(239, 68, 68, 0.2);
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

        # CUSTOM LOGOUT IMPLEMENTATION (MAIN AREA)
        if st.button("🚪 ENCERRAR SESSÃO", key="logout_btn_main", use_container_width=True):
            # 1. Clear Authenticator State
            st.session_state["authentication_status"] = None
            st.session_state["username"] = None
            st.session_state["name"] = None
            st.session_state["logout"] = True
            
            # 2. Aggressive Cookie Clearing
            try:
                if authenticator and hasattr(authenticator, 'cookie_manager'):
                    authenticator.cookie_manager.delete(authenticator.cookie_name)
            except:
                pass
                
            # 3. Clear App Session Data
            keys_to_clear = [
                'pagina', 'usuario', 'is_admin', 'is_premium',
                'xp', 'indice', 'porc_atual', 'tentativa', 'arquivo_atual', 
                'prova_modulo', 'prova_idx', 'god_mode', '_progresso_carregado'
            ]
            for k in keys_to_clear:
                if k in st.session_state:
                    del st.session_state[k]

            # 4. Nuke URL and Rerun
            st.query_params.clear()
            st.rerun()
    else:
        # CUSTOM LOGOUT IMPLEMENTATION
        # Bypass authenticator.logout bug by handling it manually
        if st.button("🚪 ENCERRAR SESSÃO", key=f"logout_btn_{location}", use_container_width=True):
            # 1. Clear Authenticator State
            st.session_state["authentication_status"] = None
            st.session_state["username"] = None
            st.session_state["name"] = None
            st.session_state["logout"] = True
            
            # 2. Aggressive Cookie Clearing (Try multiple paths)
            try:
                if authenticator and hasattr(authenticator, 'cookie_manager'):
                    authenticator.cookie_manager.delete(authenticator.cookie_name)
            except:
                pass
                
            # 3. Clear App Session Data
            keys_to_clear = [
                'pagina', 'usuario', 'is_admin', 'is_premium',
                'xp', 'indice', 'porc_atual', 'tentativa', 'arquivo_atual', 
                'prova_modulo', 'prova_idx', 'god_mode', '_progresso_carregado'
            ]
            for k in keys_to_clear:
                if k in st.session_state:
                    del st.session_state[k]

            # 4. Nuke URL and Rerun
            st.query_params.clear()
            st.rerun()


def get_current_user() -> Optional[str]:
    """Retorna o username do usuário logado ou None."""
    return st.session_state.get("username")

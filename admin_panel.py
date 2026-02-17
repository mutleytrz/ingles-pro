from __future__ import annotations
import streamlit as st
import database
import config
import streamlit_authenticator as stauth

def render_admin_panel(username: str):
    """Renderiza o painel ADM completo."""
    st.markdown("""
    <div style="background:rgba(220, 38, 38, 0.1); border:1px solid rgba(220, 38, 38, 0.3); padding:20px; border-radius:12px; margin-bottom:30px;">
        <h2 style="color:#f87171; margin:0; display:flex; align-items:center; gap:10px;">🛡️ PAINEL DE ADMINISTRADOR</h2>
        <p style="color:#fca5a5; margin:5px 0 0;">God Mode & User Management</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["👥 Gerenciar Usuários", "⚡ Ferramentas de Teste"])

    with tab1:
        _render_user_management(username)

    with tab2:
        _render_tester_tools()


def _render_user_management(current_admin_user: str):
    st.markdown("### Lista de Usuários")
    
    users = database.get_all_users_detailed()
    if not users:
        st.info("Nenhum usuário encontrado.")
        return

    # Table Header
    c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 1, 2])
    c1.markdown("**ID**")
    c2.markdown("**User**")
    c3.markdown("**Nome**")
    c4.markdown("**XP**")
    c5.markdown("**Ações**")
    st.divider()

    for u in users:
        c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 1, 2])
        is_self = (u['username'] == current_admin_user)
        
        c1.write(f"#{u['id']}")
        c2.write(f"**{u['username']}**")
        c3.write(u['name'])
        
        # XP Edit
        with c4:
             # Unique key per user
             current_xp = u['xp'] if u['xp'] is not None else 0
             new_xp = st.number_input("XP", value=current_xp, key=f"xp_{u['username']}", label_visibility="collapsed")
             if new_xp != current_xp:
                 if st.button("💾", key=f"save_xp_{u['username']}"):
                     database.update_user_xp(u['username'], int(new_xp))
                     st.toast(f"XP de {u['username']} atualizado!")
                     st.rerun()

        # Actions
        with c5:
            # is_admin toggle
            is_adm = bool(u['is_admin'])
            if st.checkbox("Admin", value=is_adm, key=f"is_adm_{u['username']}", disabled=is_self):
                if not is_adm:
                    database.update_user_role(u['username'], True)
                    st.toast(f"{u['username']} agora é Admin!")
                    st.rerun()
            else:
                if is_adm:
                    database.update_user_role(u['username'], False)
                    st.toast(f"{u['username']} removido de Admin.")
                    st.rerun()

            # Password Reset Modal Trigger
            if st.button("🔑 Senha", key=f"pwd_{u['username']}"):
                _reset_password_dialog(u['username'])

    st.divider()


@st.dialog("Resetar Senha")
def _reset_password_dialog(target_username: str):
    st.warning(f"Alterando senha de: **{target_username}**")
    new_pass = st.text_input("Nova Senha", type="password")
    confirm = st.text_input("Confirmar", type="password")
    
    if st.button("Confirmar Alteração"):
        if new_pass != confirm:
            st.error("Senhas não coincidem.")
            return
        if len(new_pass) < 4:
            st.error("Mínimo 4 caracteres.")
            return
        
        hashed = stauth.Hasher().hash(new_pass)
        database.update_user_password(target_username, hashed)
        st.success("Senha alterada com sucesso!")
        st.rerun()


def _render_tester_tools():
    st.markdown("### God Mode")
    
    god_mode_active = st.session_state.get('god_mode', False)
    toggle = st.toggle("🔓 Desbloquear Todos os Módulos (God Mode)", value=god_mode_active)
    
    if toggle != god_mode_active:
        st.session_state['god_mode'] = toggle
        st.toast(f"God Mode {'ATIVADO' if toggle else 'DESATIVADO'}")
        st.rerun()

    st.divider()
    
    st.markdown("### Salto de Lição (Jump)")
    modulos = config.MODULOS
    mod_opts = [m[1] for m in modulos] # filenames
    
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        sel_mod = st.selectbox("Módulo", mod_opts)
    with c2:
        idx = st.number_input("Índice (0-based)", min_value=0, value=0)
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Pular"):
            st.session_state['arquivo_atual'] = sel_mod
            st.session_state['indice'] = idx
            st.session_state['pagina'] = 'aula'
            st.session_state['porc_atual'] = 0
            st.session_state['tentativa'] = 0
            # Salva auto
            database.save_module_progress(st.session_state.get('username'), sel_mod, idx)
            st.rerun()

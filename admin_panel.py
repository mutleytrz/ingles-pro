from __future__ import annotations
import streamlit as st
import database
import config
import streamlit_authenticator as stauth

def render_admin_panel(username: str, test_oral_callback=None):
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
        _render_tester_tools(test_oral_callback)


def _render_user_management(current_admin_user: str):
    st.markdown("### Lista de Usuários")
    
    users = database.get_all_users_detailed()
    if not users:
        st.info("Nenhum usuário encontrado.")
        return

    # Table Header
    c1, c2, c3, c4, c5, c6 = st.columns([1, 2, 2, 2, 1, 2])
    c1.markdown("**ID**")
    c2.markdown("**User**")
    c3.markdown("**Nome**")
    c4.markdown("**Email**")
    c5.markdown("**XP**")
    c6.markdown("**Ações**")
    st.divider()

    for u in users:
        c1, c2, c3, c4, c5, c6 = st.columns([1, 2, 2, 2, 1, 2])
        is_self = (u['username'] == current_admin_user)
        
        c1.write(f"#{u['id']}")
        c2.write(f"**{u['username']}**")
        c3.write(u['name'])
        c4.write(u.get('email', '-') or '-')
        
        # XP Edit
        with c5:
             # Unique key per user
             current_xp = u['xp'] if u['xp'] is not None else 0
             new_xp = st.number_input("XP", value=current_xp, key=f"xp_{u['username']}", label_visibility="collapsed")
             if new_xp != current_xp:
                 if st.button("💾", key=f"save_xp_{u['username']}"):
                     database.update_user_xp(u['username'], int(new_xp))
                     # FIX: Se estiver editando a si mesmo, atualiza a sessao imediatamente
                     # caso contrario, o proximo salvar_progresso() vai sobrescrever o banco com o valor antigo
                     if is_self:
                        st.session_state['xp'] = int(new_xp)
                     
                     st.toast(f"XP de {u['username']} atualizado!")
                     st.rerun()

        # Actions
        with c6:
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
                    st.toast(f"{u['username']} removido de Admin.")
                    st.rerun()

            # is_premium toggle
            is_prem = bool(u.get('is_premium', 0))
            new_prem = st.checkbox("Premium", value=is_prem, key=f"is_prem_{u['username']}")
            if new_prem != is_prem:
                database.update_user_premium(u['username'], new_prem)
                st.toast(f"Status Premium de {u['username']}: {'ATIVADO' if new_prem else 'REMOVIDO'}")
                # Update session state if modifying self
                if is_self:
                    st.session_state['usuario']['is_premium'] = new_prem
                st.rerun()

            # Password Reset
            if st.button("🔑", key=f"pwd_{u['username']}", help="Resetar Senha"):
                _reset_password_dialog(u['username'])
            
            # Delete User
            if not is_self:
                if st.button("🗑️", key=f"del_{u['username']}", help="Excluir Usuário"):
                    _delete_user_dialog(u['username'])

    st.divider()


@st.dialog("Excluir Usuário")
def _delete_user_dialog(target_username: str):
    st.error(f"Tem certeza que deseja excluir **{target_username}**?")
    st.warning("Essa ação não pode ser desfeita. Todo o progresso será perdido.")
    
    if st.button("Sim, excluir permanentemente"):
        if database.delete_user(target_username):
            st.success(f"Usuário {target_username} excluído.")
            st.rerun()
        else:
            st.error("Erro ao excluir usuário.")


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


def _render_tester_tools(test_oral_callback=None):
    st.markdown("### God Mode")
    
    god_mode_active = st.session_state.get('god_mode', False)
    toggle = st.toggle("🔓 Desbloquear Todos os Módulos (God Mode)", value=god_mode_active)
    
    if toggle != god_mode_active:
        st.session_state['god_mode'] = toggle
        st.toast(f"God Mode {'ATIVADO' if toggle else 'DESATIVADO'}")
        st.rerun()


    st.divider()
    
    # Premium Preview Toggle - Admin Testing Tool
    st.markdown("### 👁️ Visualização de Paywall")
    st.caption("Simule como usuários não-premium veem a tela de upgrade")
    
    preview_mode = st.session_state.get('preview_as_free', False)
    toggle_preview = st.toggle("🔍 Simular Usuário Gratuito (Remove Premium Temporário)", value=preview_mode)
    
    if toggle_preview != preview_mode:
        st.session_state['preview_as_free'] = toggle_preview
        # IMPORTANTE: Atualiza também o objeto usuario para refletir na session
        if toggle_preview:
            # Backup do estado real
            st.session_state['_premium_backup'] = st.session_state.get('usuario', {}).get('is_premium', False)
            if 'usuario' in st.session_state:
                st.session_state['usuario']['is_premium'] = False
            st.toast("🔍 Modo Preview ATIVADO - Você verá a tela de paywall como usuário gratuito")
        else:
            # Restaura estado real
            if 'usuario' in st.session_state and '_premium_backup' in st.session_state:
                st.session_state['usuario']['is_premium'] = st.session_state['_premium_backup']
            st.toast("✅ Modo Preview DESATIVADO - Status premium restaurado")
        st.rerun()
    
    if toggle_preview:
        st.info("💡 **Dica:** Acesse qualquer módulo e vá para a 2ª lição para ver o paywall aparecer!")
    
    st.divider()

    
    st.markdown("### 🧪 Ferramentas de Teste Rápido")
    if test_oral_callback:
        st.markdown("Teste a prova oral adaptativa usando o módulo atual (carregado na memória).")
        if st.button("🎤 Iniciar Prova Oral Agora", type="primary", use_container_width=True):
            test_oral_callback()
            
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

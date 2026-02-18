from __future__ import annotations
import streamlit as st
import database
import config
import streamlit_authenticator as stauth

def render_admin_panel(username: str, test_oral_callback=None):
    """Renderiza o painel ADM completo."""

    # ===== BOTAO VOLTAR NO TOPO (SEMPRE VISIVEL) =====
    _back_col, _title_col = st.columns([1, 5])
    with _back_col:
        if st.button("⬅ Voltar ao App", key="admin_back_top", use_container_width=True):
            st.session_state['pagina'] = 'inicio'
            st.rerun()

    with _title_col:
        st.markdown("""
        <div style="background:rgba(220, 38, 38, 0.1); border:1px solid rgba(220, 38, 38, 0.3); padding:20px; border-radius:12px;">
            <h2 style="color:#f87171; margin:0; display:flex; align-items:center; gap:10px;">🛡️ PAINEL DE ADMINISTRADOR</h2>
            <p style="color:#fca5a5; margin:5px 0 0;">God Mode & User Management</p>
        </div>
        """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Gerenciar Usuários", 
        "📊 Evolução dos Alunos", 
        "⚡ Ferramentas de Teste", 
        "💰 Relatório de Vendas",
        "⚙️ Gerenciar Planos"
    ])

    with tab1:
        _render_user_management(username)

    with tab2:
        _render_student_analytics()

    with tab3:
        _render_tester_tools(test_oral_callback)
    
    with tab4:
        _render_sales_reports()
        
    with tab5:
        _render_plan_settings()


def _render_user_management(current_admin_user: str):
    st.markdown("### Lista de Usuários")
    
    # Botao para forcar refresh da lista
    if st.button("🔄 Atualizar Lista", key="refresh_users"):
        database.get_all_users_detailed.clear()
        st.rerun()
    
    users = database.get_all_users_detailed()
    if not users:
        st.info("Nenhum usuário encontrado.")
        return

    # Table Header
    c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 2, 2, 2, 1, 2, 2])
    c1.markdown("**ID**")
    c2.markdown("**User**")
    c3.markdown("**Nome**")
    c4.markdown("**Email**")
    c5.markdown("**XP**")
    c6.markdown("**Plano**")
    c7.markdown("**Ações**")
    st.divider()

    for u in users:
        c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 2, 2, 2, 1, 2, 2])
        is_self = (u['username'] == current_admin_user)
        
        c1.write(f"#{u['id']}")
        c2.write(f"**{u['username']}**")
        c3.write(u['name'])
        c4.write(u.get('email', '-') or '-')
        
        # XP Edit
        with c5:
             current_xp = u['xp'] if u['xp'] is not None else 0
             new_xp = st.number_input("XP", value=current_xp, key=f"xp_{u['username']}", label_visibility="collapsed")
             if new_xp != current_xp:
                 if st.button("💾", key=f"save_xp_{u['username']}"):
                     database.update_user_xp(u['username'], int(new_xp))
                     if is_self:
                        st.session_state['xp'] = int(new_xp)
                     database.get_all_users_detailed.clear()
                     st.rerun()

        # Plan Info
        with c6:
            p_type = u.get('plan_type', 'free').upper()
            until = u.get('premium_until')
            color = "#22c55e" if u['is_premium'] else "#94a3b8"
            st.markdown(f"<span style='color:{color}; font-weight:bold;'>{p_type}</span>", unsafe_allow_html=True)
            if until:
                st.caption(f"Expira: {until[:10]}")

        # Actions
        with c7:
            _uname = u['username']

            # is_admin toggle
            is_adm = bool(u.get('is_admin', 0))
            new_adm = st.checkbox("Adm", value=is_adm, key=f"is_adm_{_uname}", disabled=is_self)
            if new_adm != is_adm:
                database.update_user_role(_uname, new_adm)
                database.get_all_users_detailed.clear()
                st.rerun()

            # is_premium toggle
            is_prem = bool(u.get('is_premium', 0))
            new_prem = st.checkbox("Prem", value=is_prem, key=f"is_prem_{_uname}")
            if new_prem != is_prem:
                database.update_user_premium(_uname, new_prem, plan_type="manual" if new_prem else "free")
                st.rerun()

            # reset/delete/expiry
            col_a, col_b, col_c = st.columns(3)
            if col_a.button("🔑", key=f"pwd_{_uname}", help="Resetar Senha"):
                _reset_password_dialog(_uname)
            if col_b.button("📅", key=f"exp_{_uname}", help="Data de Expiração"):
                _edit_expiry_dialog(_uname, u.get('premium_until'))
            if not is_self and col_c.button("🗑️", key=f"del_{_uname}", help="Excluir Usuário"):
                _delete_user_dialog(_uname)

    st.divider()


@st.dialog("Excluir Usuário")
def _delete_user_dialog(target_username: str):
    st.error(f"Tem certeza que deseja excluir **{target_username}**?")
    st.warning("Essa ação não pode ser desfeita. Todo o progresso será perdido.")
    
    if st.button("Sim, excluir permanentemente"):
        if database.delete_user(target_username):
            st.success(f"Usuário {target_username} excluído.")
            st.rerun()


@st.dialog("Gerenciar Expiração")
def _edit_expiry_dialog(target_username: str, current_expiry: str | None):
    st.markdown(f"Ajustando expiração para: **{target_username}**")
    
    # Prepara data atual para o date_input
    from datetime import date, datetime
    init_val = date.today()
    if current_expiry:
        try:
            init_val = datetime.fromisoformat(current_expiry).date()
        except: pass
    
    new_date = st.date_input("Nova Data de Expiração", value=init_val)
    st.info("Deixe em branco ou mude o plano para Free para remover o acesso.")
    
    col1, col2 = st.columns(2)
    if col1.button("Salvar Data"):
        if database.update_user_expiry(target_username, new_date.isoformat()):
            st.success("Data atualizada!")
            st.rerun()
    
    if col2.button("Remover Data"):
        if database.update_user_expiry(target_username, None):
            st.success("Expiração removida!")
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


# ========================================================================
# TAB: EVOLUÇÃO DOS ALUNOS
# ========================================================================
def _render_student_analytics():
    st.markdown("### 📊 Acompanhamento Individual de Alunos")

    users = database.get_all_users_detailed()
    if not users:
        st.info("Nenhum usuário encontrado.")
        return

    # Dropdown para selecionar aluno
    user_options = {f"{u['username']} — {u['name']}": u['username'] for u in users}
    selected_label = st.selectbox("Selecione o aluno:", list(user_options.keys()), key="analytics_user_select")
    selected_user = user_options[selected_label]

    # Busca analytics completo
    data = database.get_student_analytics(selected_user)

    # --- Header: XP e Tier ---
    xp = data.get('xp', 0)
    # Importar a funcao de tier do app_core via indireta (evita import circular)
    tiers = [
        (0, "Novato", "#64748b", "🌱"),
        (100, "Aprendiz", "#22c55e", "📗"),
        (500, "Intermediário", "#3b82f6", "📘"),
        (1500, "Avançado", "#8b5cf6", "📙"),
        (3000, "Expert", "#f59e0b", "🏆"),
        (5000, "Mestre", "#ef4444", "👑"),
    ]
    tier_name, tier_color, tier_emoji = "Novato", "#64748b", "🌱"
    for threshold, name, color, emoji in tiers:
        if xp >= threshold:
            tier_name, tier_color, tier_emoji = name, color, emoji

    st.markdown(f"""
    <div style="background:linear-gradient(135deg, rgba(139,92,246,0.1), rgba(6,182,212,0.05));
                border:1px solid rgba(139,92,246,0.2); border-radius:16px; padding:24px; margin:16px 0;">
        <div style="display:flex; align-items:center; gap:20px; flex-wrap:wrap;">
            <div style="font-size:42px; font-weight:900; color:#f1f5f9;">⭐ {xp} XP</div>
            <div style="background:rgba(139,92,246,0.15); padding:8px 16px; border-radius:99px;
                        color:{tier_color}; font-weight:700; border:1px solid {tier_color}33;">
                {tier_emoji} {tier_name}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Progresso por Módulo ---
    st.markdown("#### 📂 Progresso por Módulo")

    mod_progress = data.get('module_progress', {})
    lesson_scores = data.get('lesson_scores', {})
    modulos = config.MODULOS

    if not mod_progress:
        st.caption("Este aluno ainda não iniciou nenhum módulo.")
    else:
        for titulo, arquivo, _url in modulos:
            # Carregar dados do CSV para saber o total de lições
            try:
                import pandas as pd
                import os
                csv_path = os.path.join(config.CSV_DIR, arquivo)
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path, on_bad_lines='skip', encoding='utf-8')
                    total_licoes = len(df)
                else:
                    total_licoes = 0
            except Exception:
                total_licoes = 0

            indice = mod_progress.get(arquivo, 0)
            if indice == 0 and arquivo not in mod_progress:
                continue  # Pula módulos não iniciados

            pct = min(int((indice / total_licoes) * 100), 100) if total_licoes > 0 else 0
            emoji = config.MODULOS_EMOJI.get(titulo, '📚')
            status = '✅ COMPLETO' if pct >= 100 else '🔄 EM CURSO'

            # Barra de progresso
            bar_color = "linear-gradient(90deg, #22c55e, #10b981)" if pct >= 100 else "linear-gradient(90deg, #8b5cf6, #06b6d4)"
            st.markdown(f"""
            <div style="background:rgba(15,10,40,0.4); border:1px solid rgba(139,92,246,0.15);
                        border-radius:12px; padding:16px; margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-weight:700; font-size:15px; color:#e2e8f0;">{emoji} {titulo}</span>
                    <span style="color:#06b6d4; font-weight:700; font-size:14px;">{pct}% — {status}</span>
                </div>
                <div style="background:rgba(255,255,255,0.06); border-radius:6px; height:8px; overflow:hidden;">
                    <div style="height:100%; width:{pct}%; background:{bar_color}; border-radius:6px;
                                transition:width 0.5s ease;"></div>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:6px; font-size:12px; color:#94a3b8;">
                    <span>Lição {indice}/{total_licoes}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Scores de lições deste módulo (se houver)
            mod_scores = lesson_scores.get(arquivo, {})
            if mod_scores:
                _scores_html_parts = []
                for idx in sorted(mod_scores.keys()):
                    score = mod_scores[idx]
                    bg = "#22c55e" if score >= 80 else ("#f59e0b" if score >= 50 else "#ef4444")
                    _scores_html_parts.append(
                        f'<span style="display:inline-block; padding:3px 8px; margin:2px; '
                        f'border-radius:6px; font-size:11px; font-weight:600; '
                        f'background:{bg}22; color:{bg}; border:1px solid {bg}44;">'
                        f'L{idx+1}: {score}%</span>'
                    )
                st.markdown(
                    '<div style="margin:-6px 0 10px 16px;">' + ''.join(_scores_html_parts) + '</div>',
                    unsafe_allow_html=True,
                )

    # --- Palavras com Dificuldade ---
    st.markdown("#### 🔴 Palavras com Dificuldade")

    weak_words = data.get('weak_words', [])
    if not weak_words:
        st.caption("Nenhuma dificuldade registrada ainda.")
    else:
        # Tabela de palavras com erros
        st.markdown("""
        <div style="background:rgba(15,10,40,0.4); border:1px solid rgba(239,68,68,0.2);
                    border-radius:12px; padding:16px; margin-bottom:10px;">
            <div style="display:flex; gap:10px; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.06);
                        font-size:12px; color:#94a3b8; font-weight:600;">
                <div style="flex:2;">PALAVRA</div>
                <div style="flex:1; text-align:center;">ERROS</div>
                <div style="flex:1; text-align:center;">VEZES VISTA</div>
                <div style="flex:1; text-align:center;">TAXA DE ERRO</div>
            </div>
        """, unsafe_allow_html=True)

        for w in weak_words[:20]:  # Limita a 20
            word = w.get('word', '?')
            errors = w.get('error_count', 0)
            total = w.get('total_seen', 1)
            rate = int((errors / total) * 100) if total > 0 else 0
            rate_color = "#ef4444" if rate >= 60 else ("#f59e0b" if rate >= 30 else "#22c55e")

            st.markdown(f"""
            <div style="display:flex; gap:10px; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.03);
                        font-size:14px; color:#e2e8f0;">
                <div style="flex:2; font-weight:600;">{word}</div>
                <div style="flex:1; text-align:center; color:#ef4444; font-weight:700;">{errors}</div>
                <div style="flex:1; text-align:center; color:#94a3b8;">{total}</div>
                <div style="flex:1; text-align:center; color:{rate_color}; font-weight:700;">{rate}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


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

def _render_sales_reports():
    st.markdown("### 💰 Relatório de Vendas Mercado Pago")
    
    if st.button("🔄 Atualizar Vendas", key="refresh_sales"):
        st.rerun()
    
    payments = database.get_all_payments()
    if not payments:
        st.info("Nenhum pagamento registrado ainda.")
        return

    # Sumário rápido
    total_sales = len(payments)
    total_revenue = sum(p['amount'] for p in payments if p['status'] == 'approved' or p['status'] == 'success')
    
    c1, c2 = st.columns(2)
    c1.metric("Total de Transações", total_sales)
    c2.metric("Receita Total (Aproximada)", f"R$ {total_revenue:.2f}")

    st.divider()
    
    # Table Header
    cols = st.columns([2, 2, 2, 1, 1, 2])
    cols[0].markdown("**Data**")
    cols[1].markdown("**Usuário**")
    cols[2].markdown("**ID Mercado Pago**")
    cols[3].markdown("**Valor**")
    cols[4].markdown("**Status**")
    cols[5].markdown("**Referência**")
    st.divider()

    for p in payments:
        cols = st.columns([2, 2, 2, 1, 1, 2])
        # Formatar data simplificada
        dt_str = p['created_at'].split('.')[0] if '.' in p['created_at'] else p['created_at']
        
        cols[0].write(dt_str)
        cols[1].write(f"{p['user_fullname']} (@{p['username']})")
        cols[2].code(p['payment_id'])
        cols[3].write(f"R$ {p['amount']:.2f}")
        
        status = p['status']
        if status in ['approved', 'success']:
            cols[4].success("Aprovado")
        elif status == 'pending':
            cols[4].warning("Pendente")
        else:
            cols[4].error(status)
            
        cols[5].write(p['external_reference'] or "-")

def _render_plan_settings():
    st.markdown("### ⚙️ Configuração de Planos e Preços")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💰 Preços dos Planos")
        
        p_mensal = st.text_input("Plano Mensal (Ex: 14.99)", value=database.get_setting("price_mensal", "14.99"))
        p_anual = st.text_input("Plano Anual (Ex: 159.00)", value=database.get_setting("price_anual", "159.00"))
        p_vitalicio = st.text_input("Plano Vitalício (Ex: 499.00)", value=database.get_setting("price_vitalicio", "499.00"))
        
        if st.button("💾 Salvar Preços", type="primary"):
            database.update_setting("price_mensal", p_mensal)
            database.update_setting("price_anual", p_anual)
            database.update_setting("price_vitalicio", p_vitalicio)
            st.success("Preços atualizados!")
            st.rerun()

    with col2:
        st.markdown("#### 👁️ Visibilidade e Links")
        
        show_v = database.get_setting("show_vitalicio", "0") == "1"
        new_show_v = st.toggle("Exibir Plano Vitalício na Assinatura", value=show_v)
        if new_show_v != show_v:
            database.update_setting("show_vitalicio", "1" if new_show_v else "0")
            st.rerun()
            
        st.divider()
        st.markdown("#### 📥 Links de Download (Vitalício)")
        dl_pc = st.text_input("Link Windows (.exe)", value=database.get_setting("download_pc_url", ""))
        dl_mob = st.text_input("Link Android (.apk)", value=database.get_setting("download_mobile_url", ""))
        
        if st.button("💾 Salvar Links"):
            database.update_setting("download_pc_url", dl_pc)
            database.update_setting("download_mobile_url", dl_mob)
            st.success("Links salvos!")
            st.rerun()

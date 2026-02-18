import streamlit as st
import time
import os
import pandas as pd
from gtts import gTTS
import config
from io import BytesIO
import base64

# ==============================================================================
# KONFIGURACAO & ASSETS
# ==============================================================================
SOUNDS_DIR = os.path.join(config.BASE_DIR, "sons_relax")
VIDEOS_DIR = os.path.join(config.BASE_DIR, "videos_relax")

AMBIENT_SOUNDS = {
    "Chuva Suave 🌧️": "Chuva_suave.mp3",
    "Chuva na Janela 🪟": "chuva na janela.mp3",
    "Tempestade ⛈️": "tempestade.mp3",
    "Trovões Distantes ⚡": "Trovoes distantes_trimmed.mp3",
    "Floresta Chuvosa 🍃": "floresta chuvosa.mp3",
    "Riacho na Mata 🌊": "riacho na mata_trimmed.mp3",
    "Ruído Branco (Foco) 📻": "ruido branco.mp3",
}

# Frequencias Binaurais (Geradas via JS)
BINAURAL_PRESETS = {
    "Theta (6Hz)": {"desc": "Relaxamento Profundo e Criatividade", "freq": 6},
    "Alpha (10Hz)": {"desc": "Foco Calmo e Aprendizado Leve", "freq": 10},
    "Delta (2Hz)": {"desc": "Sono Profundo e Regeneração", "freq": 2},
    "Beta (14Hz)": {"desc": "Concentração e Alerta", "freq": 14},
}


# ==============================================================================
# AUDIO GENERATOR (JS) - BINAURAL ENGINE
# ==============================================================================
AUDIO_JS_TEMPLATE = """
<div class="audio-engine-card">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
        <h3 style="margin:0; color:#a5b4c8; font-size:16px; font-weight:600;">🧠 BINAURAL ENGINE</h3>
        <div id="status_indicator" style="width:10px; height:10px; background:#475569; border-radius:50%; box-shadow:0 0 10px rgba(0,0,0,0.5);"></div>
    </div>

    <div style="display:flex; gap:10px; margin-bottom:20px;">
        <button onclick="toggleAudio()" id="btn_audio" class="engine-btn">▶ INICIAR ONDAS</button>
    </div>

    <!-- Controls -->
    <div class="control-group">
        <label>Frequência: <span id="freq_val">{freq}Hz</span></label>
        <input type="range" min="1" max="20" step="1" value="{freq}" oninput="setBinauralFreq(this.value)">
    </div>

    <div class="control-group">
        <label>Volume Binaural</label>
        <input type="range" min="0" max="0.3" step="0.01" value="0.1" oninput="setVolBinaural(this.value)">
    </div>

    <div style="margin-top:15px; font-size:12px; color:#64748b; line-height:1.4;">
        ℹ️ <b>Dica:</b> Use fones de ouvido para melhor experiência binaural.
    </div>
</div>

<style>
    .audio-engine-card {{
        background: linear-gradient(145deg, #1e1b4b, #0f172a);
        border: 1px solid rgba(79, 70, 229, 0.3);
        border-radius: 16px;
        padding: 20px;
        font-family: 'Outfit', sans-serif;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
    }}
    .engine-btn {{
        background: linear-gradient(90deg, #4f46e5, #6366f1);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 700;
        letter-spacing: 1px;
        flex: 1;
        transition: all 0.2s;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
    }}
    .engine-btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px rgba(79, 70, 229, 0.6); }}
    .control-group {{ margin-top: 15px; }}
    .control-group label {{ display:block; color:#94a3b8; font-size:13px; margin-bottom:5px; font-weight:500; }}
    input[type=range] {{ width: 100%; accent-color: #8b5cf6; cursor: pointer; }}
</style>

<script>
    var ctx = null;
    var gainBinaural = null, compressor = null;
    var osc1 = null, osc2 = null;
    var isPlaying = false;
    var currentFreq = {freq};

    function initAudio() {{
        if (!ctx) {{
            ctx = new (window.AudioContext || window.webkitAudioContext)();
            
            compressor = ctx.createDynamicsCompressor();
            compressor.threshold.value = -10;
            compressor.connect(ctx.destination);

            // BINAURAL SETUP
            var baseFreq = 200;
            
            osc1 = ctx.createOscillator();
            osc1.type = 'sine';
            osc1.frequency.value = baseFreq;
            var pan1 = ctx.createStereoPanner();
            pan1.pan.value = -1; // Left
            
            osc2 = ctx.createOscillator();
            osc2.type = 'sine';
            osc2.frequency.value = baseFreq + currentFreq; // Difference = Binaural Beat
            var pan2 = ctx.createStereoPanner();
            pan2.pan.value = 1; // Right

            gainBinaural = ctx.createGain();
            gainBinaural.gain.value = 0.1;

            osc1.connect(pan1); pan1.connect(gainBinaural);
            osc2.connect(pan2); pan2.connect(gainBinaural);
            
            gainBinaural.connect(compressor);
            
            osc1.start(0);
            osc2.start(0);
        }}
    }}

    function toggleAudio() {{
        var btn = document.getElementById("btn_audio");
        var led = document.getElementById("status_indicator");
        
        if (!ctx) initAudio();
        if (ctx.state === 'suspended') ctx.resume();

        if (isPlaying) {{
            if(ctx.suspend) ctx.suspend();
            btn.innerText = "▶ INICIAR ONDAS";
            btn.style.background = "linear-gradient(90deg, #4f46e5, #6366f1)";
            led.style.background = "#475569";
            led.style.boxShadow = "none";
            isPlaying = false;
        }} else {{
            if(ctx.resume) ctx.resume();
            btn.innerText = "⏸ PAUSAR ONDAS";
            btn.style.background = "linear-gradient(90deg, #ef4444, #f87171)";
            led.style.background = "#00ff88";
            led.style.boxShadow = "0 0 15px #00ff88";
            isPlaying = true;
        }}
    }}

    function setVolBinaural(val) {{
        if(gainBinaural) gainBinaural.gain.value = val;
    }}
    
    function setBinauralFreq(val) {{
        currentFreq = parseFloat(val);
        document.getElementById("freq_val").innerText = val + "Hz";
        if(osc1 && osc2) {{
            var base = osc1.frequency.value;
            osc2.frequency.value = base + currentFreq;
        }}
    }}
</script>
"""


# ==============================================================================
# UI HELPERS
# ==============================================================================
# ==============================================================================
# CACHED FILE LOADING
# ==============================================================================
@st.cache_data(show_spinner=False)
def load_media_base64(file_path):
    """Loads a media file and returns its base64 string."""
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def render_hero(video_path=None):
    # VIDEO BACKGROUND (High Performance Mode - st.video)
    if video_path and os.path.exists(video_path):
        # Renderiza video usando player nativo (streaming)
        # Hack CSS para jogar ele para o fundo
        st.video(video_path, format="video/mp4", autoplay=True, loop=True, start_time=0)
        
        # CSS para transformar o player nativo em background
        # O seletor busca o elemento de video do Streamlit
        st.markdown("""
        <style>
            [data-testid="stVideo"] {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                z-index: -1;
                overflow: hidden;
            }
            [data-testid="stVideo"] video {
                object-fit: cover;
                width: 100%;
                height: 100%;
                opacity: 0.5;
            }
            /* Esconde controles se possivel (Chrome/Webkit) */
            [data-testid="stVideo"] video::-webkit-media-controls {
                display: none !important;
            }
            /* Overlay Gradient para garantir leitura — reforçado */
            .stApp::before {
                content: "";
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(180deg, rgba(10, 5, 30, 0.8) 0%, rgba(20, 15, 50, 0.92) 100%);
                z-index: 0;
                pointer-events: none;
            }

            /* Neural Section Cards — glassmorphism para legibilidade */
            .neural-section-card {
                background: rgba(10, 5, 30, 0.85);
                backdrop-filter: blur(20px) saturate(1.5);
                border: 1px solid rgba(139, 92, 246, 0.2);
                border-radius: 16px;
                padding: 20px 24px;
                margin-bottom: 16px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.4);
            }
            .neural-section-card h3 {
                color: #f1f5f9 !important;
                font-family: 'Outfit', sans-serif;
                font-weight: 700;
                text-shadow: 0 2px 8px rgba(0,0,0,0.5);
                margin: 0;
            }
            .neural-section-card p, .neural-section-card span, .neural-section-card label {
                color: #c8d6e5 !important;
                text-shadow: 0 1px 4px rgba(0,0,0,0.4);
            }

            /* Metrics inside Neural Sleep — reforça fundo */
            [data-testid="stMetric"] {
                background: rgba(10, 5, 30, 0.75) !important;
                backdrop-filter: blur(12px);
                border: 1px solid rgba(139, 92, 246, 0.15);
                border-radius: 12px;
                padding: 12px 16px;
            }
            [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
                text-shadow: 0 1px 6px rgba(0,0,0,0.5);
            }

            /* Expander inside Neural Sleep */
            [data-testid="stExpander"] {
                background: rgba(10, 5, 30, 0.8) !important;
                backdrop-filter: blur(12px);
                border: 1px solid rgba(139, 92, 246, 0.15) !important;
                border-radius: 14px !important;
            }
            [data-testid="stExpander"] summary,
            [data-testid="stExpander"] p,
            [data-testid="stExpander"] li {
                text-shadow: 0 1px 4px rgba(0,0,0,0.3);
            }

            /* ============================================
               AUTO-HIDE MENUS (Zen Mode)
               ============================================ */
            .top-nav {
                transition: opacity 0.5s ease, transform 0.5s ease !important;
            }
            body.zen-hidden .top-nav {
                opacity: 0 !important;
                transform: translateY(-100%) !important;
                pointer-events: none !important;
            }
            [data-testid="stSidebar"] {
                transition: transform 0.5s ease, opacity 0.5s ease !important;
            }
            body.zen-hidden [data-testid="stSidebar"] {
                transform: translateX(-100%) !important;
                opacity: 0 !important;
                pointer-events: none !important;
            }
            /* Botão da sidebar (hamburguer) também esconde */
            button[data-testid="stSidebarCollapsedControl"] {
                transition: opacity 0.5s ease !important;
            }
            body.zen-hidden button[data-testid="stSidebarCollapsedControl"] {
                opacity: 0 !important;
                pointer-events: none !important;
            }
        </style>
        """, unsafe_allow_html=True)

    # Hero Content (Titulo)
    # Se tem video, fundo transparente. Se nao, gradient escuro.
    hero_bg = "transparent" if (video_path and os.path.exists(video_path)) else "linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%)"
    hero_extra = "" if (video_path and os.path.exists(video_path)) else "border: 1px solid rgba(139, 92, 246, 0.2); box-shadow: 0 20px 50px -10px rgba(0,0,0,0.5); overflow: hidden;"
    
    st.markdown(f"""
<div class="neural-hero">
    <div class="hero-content">
        <h1>MOONLIGHT MODE 🌙</h1>
        <p>Relaxe e aprenda enquanto a IA repousa em sua mente.</p>
    </div>
</div>
<style>
    .neural-hero {{
        position: relative;
        background: {hero_bg};
        border-radius: 24px;
        padding: 60px 20px;
        text-align: center;
        margin-bottom: 30px;
        z-index: 1;
        {hero_extra}
    }}
    .hero-content {{ position: relative; z-index: 2; }}
    .hero-content h1 {{
        font-family: 'Outfit', sans-serif;
        font-size: 42px;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 10px;
        letter-spacing: 2px;
        text-shadow: 0 0 30px rgba(139, 92, 246, 0.5);
    }}
    .hero-content p {{
        font-family: 'Outfit', sans-serif;
        color: #94a3b8;
        font-size: 18px;
    }}
</style>
""", unsafe_allow_html=True)

def render_warnings():
    with st.expander("⚠️ AVISOS DE SAÚDE & SEGURANÇA (LEIA ANTES)", expanded=False):
        st.markdown("""
        <div style="background:rgba(239, 68, 68, 0.1); padding:15px; border-radius:10px; border:1px solid rgba(239, 68, 68, 0.3);">
            <h4 style="color:#fca5a5; margin-top:0;">🚫 Contraindicações</h4>
            <ul style="color:#e2e8f0; font-size:14px;">
                <li><b>Epilepsia:</b> Pessoas propensas a convulsões ou epilepsia fotossensível NÃO devem usar áudios binaurais sem orientação médica.</li>
                <li><b>Problemas Cardíacos:</b> Portadores de marca-passo devem consultar um médico.</li>
                <li><b>Ao Dirigir:</b> NUNCA use este modo enquanto dirige ou opera máquinas pesadas. O relaxamento excessivo pode causar sonolência.</li>
                <li><b>Crianças:</b> Não recomendado para menores de 18 anos sem supervisão.</li>
            </ul>
            <p style="font-size:12px; color:#cbd5e1; margin-top:10px;">
                * Este aplicativo é uma ferramenta de auxílio ao aprendizado e relaxamento, não um tratamento médico.
            </p>
        </div>
        """, unsafe_allow_html=True)

def render_education():
    with st.expander("🎓 Como funciona o Aprendizado Neural?"):
        st.markdown("""
        ### O Poder das Ondas Binaurais
        Ondas binaurais são uma ilusão auditiva percebida quando dois tons de frequências ligeiramente diferentes são apresentados a cada ouvido. O cérebro processa a diferença (ex: 200Hz esquerdo - 206Hz direito = **6Hz**) e tende a sincronizar suas ondas cerebrais a essa frequência ("Frequency Following Response").
        
        ### Guia de Frequências
        - **Theta (4-8Hz):** O estado do "sonho lúcido". Ideal para hipnose, super-aprendizado e criatividade.
        - **Alpha (8-14Hz):** Relaxamento desperto. Bom para leitura e foco suave.
        - **Delta (0.5-4Hz):** Sono profundo sem sonhos. Use para dormir.
        - **Beta (14-30Hz):** Estado de alerta normal. Use para concentração ativa.
        
        ### Dicas de Uso
        1. **Fones de Ouvido:** Obrigatório. Sem fones estéreo, o efeito binaural não funciona.
        2. **Volume:** Mantenha baixo e confortável. O som não deve competir com sua atenção.
        3. **Consistência:** Sessões de 15-30 minutos trazem melhores resultados.
        """)

# ==============================================================================
# FUNCOES DE LÓGICA
# ==============================================================================
def generate_full_lesson_audio(df: pd.DataFrame, slow_en=True) -> BytesIO:
    """Concatena TTS (PT + Silêncio + EN + Silêncio) em um único MP3."""
    full_audio = BytesIO()
    
    # Placeholder de silencio (1 seg) - gerado "na marra" ou apenas ignorado em gTTS
    # gTTS nao gera silencio nativamente. Vamos apenas concatenar falas.
    
    for idx, row in df.iterrows():
        try:
            txt_pt = str(row['pt'])
            txt_en = str(row['en'])
            
            # Gera PT
            tts_pt = gTTS(text=txt_pt, lang='pt')
            fp_pt = BytesIO()
            tts_pt.write_to_fp(fp_pt)
            full_audio.write(fp_pt.getvalue())
            
            # Gera EN
            tts_en = gTTS(text=txt_en, lang='en', slow=slow_en)
            fp_en = BytesIO()
            tts_en.write_to_fp(fp_en)
            full_audio.write(fp_en.getvalue())
        except Exception as e:
            print(f"Erro TTS linha {idx}: {e}")
            continue
        
    full_audio.seek(0)
    return full_audio


def render_neural_mode(username: str):
    # -- HEADER --
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("⬅ VOLTAR", use_container_width=True):
            st.session_state['pagina'] = 'inicio'
            st.rerun()
            
    # 1. Recupera som atual (do session_state ou padrao) para definir o video de fundo
    default_sound = list(AMBIENT_SOUNDS.keys())[0]
    current_sound = st.session_state.get('selected_sound_name', default_sound)
    
    sound_file = AMBIENT_SOUNDS[current_sound]
    
    # Busca video correspondente
    video_path = None
    if os.path.exists(VIDEOS_DIR):
        base_name = os.path.splitext(sound_file)[0]
        base_name_clean = base_name.replace("_trimmed", "")
        
        for f in os.listdir(VIDEOS_DIR):
            if f.lower().startswith(base_name.lower()) or f.lower().startswith(base_name_clean.lower()):
                if f.endswith(('.mp4', '.webm', '.mov')):
                    video_path = os.path.join(VIDEOS_DIR, f)
                    break
    
    render_hero(video_path)
    
    # -- LAYOUT PRINCIPAL (2 Colunas) --
    c_config, c_player = st.columns([1.2, 2])

    with c_config:
        st.markdown("### 🎛️ Configuração Sonora", unsafe_allow_html=True)
        
        # 1. Seletor de Som Ambiente
        # Importante: key='selected_sound_name' conecta isso ao loop de renderizacao acima
        selected_sound_name = st.selectbox(
            "📍 Ambiente (Offline)", 
            list(AMBIENT_SOUNDS.keys()),
            index=list(AMBIENT_SOUNDS.keys()).index(current_sound),
            key="selected_sound_name"
        )
        
        # Atualiza sound_path baseado na selecao REAL deste ciclo
        sound_file = AMBIENT_SOUNDS[selected_sound_name]
        sound_path = os.path.join(SOUNDS_DIR, sound_file)

        st.divider()

        # Player Customizado com LOOP (HTML5)
        if os.path.exists(sound_path):
            try:
                # Le arquivo binario e converte para base64 - CACHED
                audio_b64 = load_media_base64(sound_path)
                mime_type = "audio/mp3"
                
                # HTML Player com LOOP e controle de volume integrado
                # Usando st.components.v1.html (Iframe) para garantir isolamento e reload
                player_html = f"""
                <html>
                <body style="margin:0; padding:0; background:transparent;">
                    <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:10px; border:1px solid rgba(255,255,255,0.1); font-family:sans-serif;">
                        <label style="font-size:12px; color:#94a3b8; display:block; margin-bottom:5px;">🔊 Player de Ambiente (Loop)</label>
                        <audio controls loop autoplay name="media" style="width:100%; height:30px;">
                            <source src="data:{mime_type};base64,{audio_b64}" type="{mime_type}">
                        </audio>
                    </div>
                </body>
                </html>
                """
                st.components.v1.html(player_html, height=80)
                
            except Exception as e:
                st.error(f"Erro ao carregar áudio: {e}")
        else:
            st.error(f"Arquivo não encontrado: {sound_file}")
            st.caption("Execute 'download_sounds.py'")

        # 2. Seletor Binaural
        st.markdown("### 🧠 Ondas Cerebrais")
        preset_name = st.selectbox(
            "Frequência Alvo",
            list(BINAURAL_PRESETS.keys())
        )
        preset = BINAURAL_PRESETS[preset_name]
        
        st.info(f"**{preset_name}:** {preset['desc']}")
        
        # Injeta JS Engine com a frequencia escolhida
        st.components.v1.html(AUDIO_JS_TEMPLATE.format(freq=preset['freq']), height=320)

    
    with c_player:
        # -- EDUCATIONAL TABS --
        st.markdown("""
<div class="neural-section-card">
    <h3>📚 Central de Conhecimento</h3>
    <p style="font-size:14px; margin-top:8px; margin-bottom:0;">Informações sobre ondas binaurais e segurança</p>
</div>
""", unsafe_allow_html=True)
        render_warnings()
        render_education()
        
        st.divider()

        # -- REPRODUTOR DE AULAS --
        st.markdown("""
<div class="neural-section-card">
    <h3>🎧 Sessão de Hipnose (Aula)</h3>
    <p style="font-size:14px; margin-top:8px; margin-bottom:0;">Selecione um módulo e gere sua sessão de aprendizado neural</p>
</div>
""", unsafe_allow_html=True)
        
        modulos = config.MODULOS
        opcoes = [m[0] for m in modulos]
        escolha = st.selectbox("Selecione o Conteúdo da Aula", opcoes)
        arquivo_csv = next(m[1] for m in modulos if m[0] == escolha)
        
        # Cards de status
        c1, c2 = st.columns(2)
        c1.metric("Módulo", escolha)
        c2.metric("Sessão", "30 Frases")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔮 GERAR SESSÃO DE HIPNOSE (TTS)", type="primary", use_container_width=True):
            with st.spinner("Sintetizando vozes neurais... (Aguarde ~10s)"):
                # Carrega CSV
                full_path = os.path.join(config.CSV_DIR, arquivo_csv)
                try:
                    df = pd.read_csv(full_path)
                    
                    # --- FREEMIUM LOGIC ---
                    _user_data = st.session_state.get('usuario', {})
                    is_premium = _user_data.get('is_premium', False)
                    if _user_data.get('is_admin', False) or st.session_state.get('god_mode', False):
                        is_premium = True
                        
                    if not is_premium:
                        df_slice = df.head(1)
                        # Premium Upsell Component for Sleep Mode
                        st.markdown("""
                        <div style="
                            background: linear-gradient(90deg, rgba(30, 20, 60, 0.6) 0%, rgba(139, 92, 246, 0.15) 100%);
                            border: 1px solid rgba(139, 92, 246, 0.3);
                            border-radius: 16px;
                            padding: 20px;
                            margin: 20px 0;
                            display: flex;
                            align-items: center;
                            gap: 20px;
                            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                        ">
                            <div style="font-size: 32px; filter: drop-shadow(0 0 10px rgba(139,92,246,0.5));">💎</div>
                            <div style="flex: 1;">
                                <h4 style="margin: 0; color: #f8fafc; font-family: 'Outfit', sans-serif; font-size: 18px;">Modo Demonstração</h4>
                                <p style="margin: 5px 0 0; color: #cbd5e1; font-size: 14px; line-height: 1.5;">
                                    Você está ouvindo uma sessão demo de 1 frase. 
                                    <br><strong style="color: #a78bfa;">Assine o Premium</strong> para desbloquear sessões profundas de 30 frases.
                                </p>
                            </div>
                            <a href="#" style="
                                background: linear-gradient(90deg, #8b5cf6, #d946ef);
                                color: white;
                                text-decoration: none;
                                padding: 10px 20px;
                                border-radius: 8px;
                                font-weight: 700;
                                font-size: 14px;
                                white-space: nowrap;
                                box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
                                text-transform: uppercase;
                                letter-spacing: 0.5px;
                            ">Virar Premium</a>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Pega apenas 30 frases para nao travar o servidor (Premium)
                        df_slice = df.head(30)
                    
                    audio_bytes = generate_full_lesson_audio(df_slice)
                    
                    st.success("✅ Sessão pronta! Coloque seus fones.")
                    st.audio(audio_bytes, format="audio/mp3", autoplay=False)
                    
                except Exception as e:
                    st.error(f"Falha ao gerar aula: {e}")

    # TODO: Auto-hide menus — precisa de pacote externo (streamlit-javascript)
    # Streamlit sanitiza <script>, onload, onerror em st.markdown e
    # st.components.v1.html roda em iframe sandbox sem acesso ao parent.

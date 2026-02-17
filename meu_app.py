import streamlit as st
from gtts import gTTS
import os
import requests
import base64
from streamlit_mic_recorder import mic_recorder
import string
import json
import io
import wave
import pandas as pd
from vosk import Model, KaldiRecognizer
import time

# --- SAVE / LOAD PROGRESSO ---
SAVE_FILE = "progresso.json"

def salvar_progresso():
    dados = {
        "pagina": st.session_state.pagina,
        "arquivo_atual": st.session_state.arquivo_atual,
        "indice": st.session_state.indice,
        "xp": st.session_state.xp,
        "porc_atual": st.session_state.porc_atual,
        "tentativa": st.session_state.tentativa
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f)

def carregar_progresso():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            for k, v in dados.items():
                st.session_state[k] = v

# --- CONFIG ---
st.set_page_config(page_title="Inglês Local Pro", layout="wide")

PASTAS = ["imagens", "audios_local", "assets", "model"]
for p in PASTAS:
    if not os.path.exists(p):
        os.makedirs(p)

def get_img_64(pasta, nome_arquivo):
    caminho = os.path.join(pasta, nome_arquivo)
    if os.path.exists(caminho):
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def aplicar_estilo():
    fundo_64 = get_img_64("assets", "fundo.png")
    st.markdown(f"""
    <style>
    #MainMenu, footer, header {{visibility: hidden;}}
    .stApp {{
        background: url("data:image/png;base64,{fundo_64}");
        background-size: cover;
        background-position: center;
    }}

    h1, h2, h3, p, b {{
        color: white !important;
        text-shadow: 2px 2px 8px #000;
        font-weight: bold;
    }}

    .feedback-word {{ display:inline-block; padding:5px 10px; margin:2px; border-radius:5px; font-weight:bold; font-size:20px; }}
    .word-correct {{ background:#28a745; color:white !important; }}
    .word-wrong {{ background:#dc3545; color:white !important; }}

    .ouvi-box {{ background:rgba(0,0,0,.85); padding:20px; border-radius:12px; border-left:12px solid #00BFFF; margin-bottom:20px; }}
    .precisao-box {{ background:rgba(15,15,15,.95); padding:30px; border-radius:15px; border:4px solid #FFD700; text-align:center; }}

    .xp-top-box {{ background:#FFD700; color:black !important; padding:15px; border-radius:10px; text-align:center; font-size:24px; font-weight:900; margin-bottom:20px; }}

    .module-card {{ background:rgba(0,0,0,.6); border:3px solid white; border-radius:15px 15px 0 0; overflow:hidden; line-height:0; margin-top:10px; }}
    .card-img {{ width:100%!important; height:160px!important; object-fit:cover!important; display:block; }}

    div.stButton>button {{
        width:100%!important;
        border:3px solid white!important;
        border-top:none!important;
        border-radius:0 0 15px 15px!important;
        background:#00BFFF!important;
        color:white!important;
        font-size:16px!important;
        font-weight:900!important;
        padding:10px!important;
        margin-bottom:25px!important;
        text-transform:uppercase;
    }}

    .aula-img-box {{ width:100%; height:420px; overflow:hidden; border-radius:15px; border:3px solid white; background:black; }}
    .aula-img-box img {{ width:100%; height:100%; object-fit:cover; }}

    /* === NOVO: ESTÉTICA APENAS DAS LIÇÕES === */
    .lang-box {{
        background: rgba(0,0,0,0.65);
        border: 2px solid rgba(255,255,255,0.7);
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 20px;
    }}

    .lang-line {{
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 10px;
    }}

    .lang-line img {{
        width: 40px;
        border-radius: 4px;
    }}

    .lang-pt {{ font-size: 22px; }}
    .lang-en {{ font-size: 30px; font-weight: 900; }}
    </style>
    """, unsafe_allow_html=True)

def carregar_banco_especifico(nome_arquivo):
    if os.path.exists(nome_arquivo):
        df = pd.read_csv(nome_arquivo, on_bad_lines='skip', encoding='utf-8')
        return df.fillna("").to_dict('records')
    return []

def limpar(t):
    return str(t).lower().strip().translate(str.maketrans('', '', string.punctuation))

# --- ESTADO ---
if 'pagina' not in st.session_state: st.session_state.pagina = 'inicio'
if 'arquivo_atual' not in st.session_state: st.session_state.arquivo_atual = 'palavras.csv'
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'porc_atual' not in st.session_state: st.session_state.porc_atual = 0
if 'tentativa' not in st.session_state: st.session_state.tentativa = 0

aplicar_estilo()
carregar_progresso()

@st.cache_resource
def carregar_vosk():
    return Model("model") if os.path.exists("model") else None

model_vosk = carregar_vosk()

# --- TELAS ---
if st.session_state.pagina == 'inicio':
    st.markdown("<br><br><h1 style='text-align:center;font-size:70px;'>INGLÊS LOCAL PRO</h1>", unsafe_allow_html=True)
    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        if st.button("🚀 INICIAR"):
            st.session_state.pagina = 'selecao_modulos'
            salvar_progresso()
            st.rerun()

elif st.session_state.pagina == 'selecao_modulos':
    st.markdown(f"<div style='text-align:right'><span style='background:#FFD700;color:black;padding:10px;border-radius:15px;font-weight:bold;'>⭐ XP TOTAL: {st.session_state.xp}</span></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;'>Selecione o Módulo</h1>", unsafe_allow_html=True)

    modulos = [
        ("🏫 ESCOLA","escola.csv","https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=400"),
        ("✈️ AEROPORTO","aeroporto.csv","https://upload.wikimedia.org/wikipedia/commons/a/a1/Sagu%C3%A3o_Aeroporto_da_Pampulha_3.jpg"),
        ("🏨 HOTEL","hotel.csv","https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400"),
        ("📂 PALAVRAS","palavras.csv","https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=400"),
        ("💼 TRABALHO","trabalho.csv","https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=400"),
        ("🛒 COMPRAS","compras.csv","https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400"),
        ("🍎 SAÚDE","saude.csv","https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?w=400"),
        ("☕ CASUAL","casual.csv","https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=400"),
        ("🚌 TRANSPORTE","transporte.csv","https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=400"),
        ("📱 TECNOLOGIA","tecnologia.csv","https://images.unsplash.com/photo-1518770660439-4636190af475?w=400"),
        ("🏠 COTIDIANO","cotidiano.csv","https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=400"),
        ("🎮 LAZER","lazer.csv","https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?w=400"),
        ("❤️ RELACIONAMENTO","relacionamento.csv","https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=400"),
    ]

    cols = st.columns(4)
    for i,(titulo,arquivo,img) in enumerate(modulos):
        with cols[i % 4]:
            st.markdown(f'<div class="module-card"><img src="{img}" class="card-img"></div>', unsafe_allow_html=True)
            if st.button(titulo, key=f"btn_{arquivo}"):
                st.session_state.arquivo_atual = arquivo
                st.session_state.indice = 0
                st.session_state.porc_atual = 0
                st.session_state.tentativa = 0
                st.session_state.pagina = 'aula'
                salvar_progresso()
                st.rerun()

elif st.session_state.pagina == 'aula':
    banco = carregar_banco_especifico(st.session_state.arquivo_atual)
    atual = banco[st.session_state.indice % len(banco)]

    st.markdown(f"<div class='xp-top-box'>⭐ MEU XP: {st.session_state.xp}</div>", unsafe_allow_html=True)

    col1,col2 = st.columns([1,1.2])

    with col1:
        img64 = get_img_64("imagens", f"{atual['id']}.jpg")
        if img64:
            st.markdown(f"<div class='aula-img-box'><img src='data:image/jpeg;base64,{img64}'></div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="lang-box">
            <div class="lang-line">
                <img src="https://flagcdn.com/w40/br.png">
                <div class="lang-pt">{atual['pt']}</div>
            </div>
            <div class="lang-line">
                <img src="https://flagcdn.com/w40/us.png">
                <div class="lang-en">{atual['en']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        modulo = os.path.splitext(st.session_state.arquivo_atual)[0]
        path_ref = os.path.join("audios_local", f"{modulo}_{atual['id']}.mp3")

        if not os.path.exists(path_ref):
            gTTS(text=str(atual['en']), lang='en').save(path_ref)

        st.audio(path_ref)

        gravacao = mic_recorder(
            start_prompt="🔴 CLIQUE PARA FALAR",
            stop_prompt="⏹️ PARAR",
            format="wav",
            key=f"mic_{st.session_state.indice}_{st.session_state.tentativa}"
        )

        if gravacao:
            audio_data = io.BytesIO(gravacao['bytes'])
            with wave.open(audio_data,'rb') as wf:
                rec = KaldiRecognizer(model_vosk, wf.getframerate())
                rec.AcceptWaveform(wf.readframes(wf.getnframes()))
                ouvida = json.loads(rec.FinalResult()).get("text","").lower()

            alvo = limpar(atual['en']).split()
            dito = limpar(ouvida).split()

            html = '<div class="ouvi-box">'
            acertos = 0
            for i,p in enumerate(alvo):
                if i < len(dito) and dito[i]==p:
                    html += f'<span class="feedback-word word-correct">{p.upper()}</span>'
                    acertos+=1
                else:
                    html += f'<span class="feedback-word word-wrong">{p.upper()}</span>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

            st.session_state.porc_atual = int((acertos/len(alvo))*100) if alvo else 0
            st.markdown(f"<div class='precisao-box'><h1>{st.session_state.porc_atual}%</h1></div>", unsafe_allow_html=True)

            salvar_progresso()

    st.write("---")
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("⬅ VOLTAR"):
            st.session_state.pagina='selecao_modulos'
            salvar_progresso()
            st.rerun()
    with c2:
        if st.button("🔄 REFAZER"):
            st.session_state.tentativa += 1
            st.session_state.porc_atual = 0
            salvar_progresso()
            st.rerun()
    with c3:
        if st.session_state.porc_atual >= 80:
            if st.button("➡️ PRÓXIMA"):
                st.session_state.indice+=1
                st.session_state.porc_atual=0
                st.session_state.tentativa=0
                salvar_progresso()
                st.rerun()
        else:
            st.button("🔒 BLOQUEADO", disabled=True)

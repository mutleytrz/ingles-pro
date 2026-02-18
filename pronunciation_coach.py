from __future__ import annotations
# pronunciation_coach.py — Professor de Pronúncia AI
# ====================================================================
# Módulo de treino de pronúncia com feedback detalhado em PT-BR,
# guia fonético "aportuguesado" e correção estilo professor real.
# ====================================================================

import streamlit as st
import os
import io
import json
import wave
import string
import random
from gtts import gTTS
from vosk import Model, KaldiRecognizer
from streamlit_mic_recorder import mic_recorder

import config
import database

# ---------------------------------------------------------------------------
# DICIONÁRIO FONÉTICO BR — Pronúncia "aportuguesada" das palavras mais comuns
# ---------------------------------------------------------------------------
PHONETIC_BR: dict[str, str] = {
    # --- Pronomes e artigos ---
    "i": "ai", "you": "iú", "he": "rí", "she": "xí", "it": "ít",
    "we": "uí", "they": "dêi", "me": "mí", "him": "rím", "her": "rêr",
    "us": "âs", "them": "dém", "my": "mái", "your": "iór", "his": "ríz",
    "our": "áur", "their": "dér", "its": "íts",
    "the": "dê", "a": "â", "an": "én",
    "this": "dís", "that": "dét", "these": "díiz", "those": "dôuz",

    # --- Verbos essenciais ---
    "is": "íz", "are": "ár", "am": "ém", "was": "uóz", "were": "uêr",
    "be": "bí", "been": "bín", "being": "bíin",
    "have": "rév", "has": "réz", "had": "réd", "having": "révin",
    "do": "dú", "does": "dâz", "did": "díd", "done": "dân",
    "will": "uíl", "would": "uúd", "could": "cúd", "should": "shúd",
    "can": "kén", "may": "mêi", "might": "máit", "must": "mâst",
    "go": "gôu", "goes": "gôuz", "going": "gôuin", "went": "uênt", "gone": "gón",
    "come": "câm", "came": "kêim", "coming": "câmin",
    "get": "guét", "got": "gót", "getting": "guétin",
    "make": "mêik", "made": "mêid", "making": "mêikin",
    "know": "nôu", "knew": "niú", "known": "nôun",
    "think": "thínk", "thought": "thót", "thinking": "thínkin",
    "take": "têik", "took": "túk", "taken": "têiken",
    "see": "sí", "saw": "só", "seen": "sín",
    "want": "uónt", "need": "níid", "like": "láik", "love": "lâv",
    "give": "guív", "gave": "guêiv", "given": "guíven",
    "tell": "tél", "told": "tôuld", "say": "sêi", "said": "séd",
    "put": "pút", "let": "lét", "keep": "kíip", "kept": "képt",
    "work": "uôrk", "working": "uôrkin", "worked": "uôrkd",
    "call": "kól", "try": "trái", "ask": "ésk",
    "use": "iúz", "find": "fáind", "found": "fáund",
    "live": "lív", "feel": "fíil", "become": "bikâm",
    "leave": "líiv", "left": "léft",
    "play": "plêi", "run": "rân", "move": "múuv",
    "buy": "bái", "bought": "bót", "pay": "pêi", "paid": "pêid",
    "eat": "íit", "ate": "êit", "eating": "íítin",
    "drink": "drínk", "drank": "drénk",
    "read": "ríid", "write": "ráit", "wrote": "rôut",
    "speak": "spík", "spoke": "spôuk", "spoken": "spôuken",
    "learn": "lêrn", "teach": "títch", "study": "stâdi",
    "sit": "sít", "stand": "sténd", "walk": "uók", "sleep": "slíip",
    "open": "ôupen", "close": "clôuz", "start": "stárt", "stop": "stóp",
    "help": "rélp", "show": "shôu", "turn": "têrn",
    "listen": "líssen", "watch": "uótch", "look": "lúk",
    "wait": "uêit", "meet": "míit", "met": "mét",
    "bring": "bríng", "brought": "brót",
    "send": "sênd", "sent": "sênt",
    "check": "tchék",

    # --- Perguntas ---
    "what": "uót", "where": "uér", "when": "uén", "why": "uái",
    "how": "ráu", "who": "rú", "which": "uítch", "whose": "rúuz",

    # --- Preposições e conectivos ---
    "in": "ín", "on": "ón", "at": "ét", "to": "tú", "for": "fór",
    "with": "uídh", "from": "frâm", "by": "bái", "about": "abáut",
    "into": "íntu", "through": "thrú", "after": "éfter", "before": "bifór",
    "between": "bituín", "under": "ânder", "over": "ôuver",
    "up": "âp", "down": "dáun", "out": "áut", "off": "óf",
    "and": "énd", "but": "bât", "or": "ór", "so": "sôu",
    "because": "bicóz", "if": "íf", "then": "dén", "than": "dén",
    "not": "nót", "no": "nôu", "yes": "iés",

    # --- Substantivos comuns ---
    "time": "táim", "day": "dêi", "night": "náit",
    "year": "iír", "week": "uíik", "month": "mânth",
    "today": "tudêi", "tomorrow": "tumórou", "yesterday": "iésterdei",
    "morning": "mórnin", "afternoon": "éfternuun", "evening": "ívnin",
    "man": "mén", "woman": "uúman", "child": "tcháild", "children": "tchíldren",
    "people": "pípol", "person": "pêrson", "family": "fémili",
    "friend": "frénd", "mother": "mâdher", "father": "fâdher",
    "brother": "brâdher", "sister": "síster",
    "house": "ráuz", "home": "rôum", "room": "rúum",
    "door": "dór", "window": "uíndou",
    "school": "skúul", "class": "kléss", "teacher": "títcher",
    "student": "stiúdent", "book": "búk", "pen": "pén", "desk": "désk",
    "meeting": "míiting", "office": "ófiss", "project": "pródject",
    "report": "ripórt", "email": "ímêil", "boss": "bós",
    "presentation": "prezentêixon", "check-in": "tchékin",
    "water": "uórer", "food": "fúud", "money": "mâni",
    "car": "kár", "bus": "bâs", "train": "trêin",
    "city": "síti", "country": "câuntri", "world": "uôrld",
    "way": "uêi", "place": "plêis", "thing": "thíng",
    "name": "nêim", "number": "nâmber", "part": "párt",
    "problem": "próblem", "question": "kuéstchon",
    "hand": "rénd", "head": "réd", "eye": "ái", "eyes": "áiz",
    "life": "láif", "heart": "rárt",
    "word": "uôrd", "story": "stóri",
    "table": "têibol", "chair": "tchér",
    "phone": "fôun", "computer": "compiúter",
    "hotel": "rotél", "restaurant": "réstorânt",
    "airport": "érpórt", "hospital": "róspitol",
    "market": "márket", "store": "stór",
    "street": "stríit", "road": "rôud",
    "weather": "uédher", "rain": "rêin", "sun": "sân",
    "breakfast": "brékfest", "lunch": "lântch", "dinner": "díner",
    "ticket": "tíket", "passport": "péssport",
    "bathroom": "béthruun", "kitchen": "kítchen",
    "doctor": "dóctor", "medicine": "médissin",
    "price": "práiss", "change": "tchêindj",

    # --- Adjetivos frequentes ---
    "good": "gúd", "bad": "béd", "great": "grêit",
    "big": "bíg", "small": "smól", "old": "ôuld", "new": "niú",
    "long": "lóng", "short": "shórt", "tall": "tól",
    "first": "fêrst", "last": "lést", "next": "nékst",
    "right": "ráit", "wrong": "rông",
    "same": "sêim", "different": "díferent",
    "important": "impórtant", "beautiful": "biúrifol",
    "happy": "répi", "sorry": "sóri", "sure": "shúr",
    "ready": "rédi", "late": "lêit", "early": "êrli",
    "free": "fríi", "busy": "bízi",
    "easy": "íizi", "hard": "rárrd", "difficult": "díficolt",
    "hot": "rót", "cold": "côuld", "warm": "uórm",
    "nice": "náiss", "fine": "fáin",
    "much": "mâtch", "many": "méni", "some": "sâm",
    "every": "évri", "all": "ól", "each": "íitch",
    "other": "âdher", "another": "anâdher",

    # --- Advérbios e expressões ---
    "very": "véri", "really": "ríili", "just": "djâst",
    "too": "tú", "also": "ólsou", "still": "stíl",
    "already": "olrédi", "always": "ólueiz",
    "never": "néver", "sometimes": "sâmtáimz",
    "here": "ríir", "there": "dér",
    "now": "náu", "again": "aguéin",
    "please": "plíiz", "thank": "thénk", "thanks": "thénks",
    "sorry": "sóri", "excuse": "ekskiúz",
    "hello": "relôu", "goodbye": "gudbái",
    "okay": "okêi", "ok": "okêi",
    "well": "uél",

    # --- Números ---
    "one": "uan", "two": "tú", "three": "thrí", "four": "fór",
    "five": "fáiv", "six": "síks", "seven": "séven",
    "eight": "êit", "nine": "náin", "ten": "tén",
    "hundred": "râdred", "thousand": "tháuzend",
    "million": "mílion",

    # --- Tempo/Dinheiro ---
    "hour": "áur", "minute": "mínit", "second": "sékond",
    "clock": "clók", "half": "réf",
    "dollar": "dólar", "cent": "sênt",

    # --- Viagem ---
    "travel": "trével", "trip": "tríp", "flight": "fláit",
    "luggage": "lâguidj", "bag": "bég",
    "reservation": "rezervêixon", "room": "rúum",
    "key": "kí", "floor": "flór",
    "taxi": "táksi", "subway": "sâbuei",
    "map": "mép", "sign": "sáin",

    # --- Comida ---
    "coffee": "kófi", "tea": "tí", "milk": "mílk",
    "bread": "bréd", "rice": "ráiss", "meat": "míit",
    "chicken": "tchíken", "fish": "físh",
    "egg": "ég", "cheese": "tchíiz",
    "sugar": "shúgar", "salt": "sólt",
    "fruit": "frúut", "apple": "épol",

    # --- Expressões úteis (multi-word handled separately) ---
    "don't": "dôunt", "doesn't": "dâzent", "didn't": "dídent",
    "won't": "uôunt", "can't": "kênt", "couldn't": "cúdent",
    "shouldn't": "shúdent", "wouldn't": "uúdent",
    "isn't": "ízent", "aren't": "árent", "wasn't": "uózent",
    "weren't": "uêrent",
    "i'm": "áim", "you're": "iór", "he's": "ríz", "she's": "shíz",
    "we're": "uír", "they're": "dér",
    "i've": "áiv", "you've": "iúv", "we've": "uív",
    "i'll": "áil", "you'll": "iúl", "he'll": "ríl", "she'll": "shíl",
    "we'll": "uíl", "they'll": "dêil",
    "let's": "léts", "there's": "dérz",
}

# ---------------------------------------------------------------------------
# DICAS DE ENTONAÇÃO — Sons difíceis para brasileiros
# ---------------------------------------------------------------------------
PRONUNCIATION_TIPS: dict[str, str] = {
    "th": "💡 O som 'TH': coloque a ponta da língua entre os dentes e sopre suavemente. Pratique com 'the', 'think', 'this'.",
    "r": "💡 O 'R' inglês: NÃO vibre a língua como no português. A língua vai para trás, sem tocar o céu da boca.",
    "w": "💡 O 'W': arredonde os lábios como se fosse dizer 'U' e depois abra para a vogal seguinte. Ex: 'water' = 'uórer'.",
    "h": "💡 O 'H' aspirado: sopre o ar como se estivesse embaçando um vidro. Ex: 'have' = 'rév' (aspirado!).",
    "ed": "💡 Terminação '-ED': pode soar como 'D' (played=plêid), 'T' (worked=uôrkT) ou 'ID' (wanted=uón-tid).",
    "ing": "💡 Terminação '-ING': pronuncie 'in' com um leve 'g' nasal no final. NÃO diga 'ingue'.",
    "l": "💡 O 'L' final: a língua toca atrás dos dentes superiores. 'School' = skúul, 'people' = pípol.",
    "v": "💡 O 'V' inglês: morda levemente o lábio inferior e vibre. Diferente do 'V' brasileiro!",
}


# ---------------------------------------------------------------------------
# FUNCS — Análise de Pronúncia
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    """Remove pontuação e normaliza."""
    return text.lower().strip().translate(str.maketrans('', '', string.punctuation))


def get_pronunciation_guide(phrase: str) -> str:
    """Gera a pronúncia 'aportuguesada' de uma frase inteira."""
    words = _clean(phrase).split()
    phonetics = []
    for w in words:
        if w in PHONETIC_BR:
            phonetics.append(PHONETIC_BR[w])
        else:
            # Fallback: mostra a palavra original em itálico
            phonetics.append(f"<i>{w}</i>")
    return " ".join(phonetics)


def get_word_phonetic(word: str) -> str:
    """Retorna a pronúncia BR de uma palavra, ou a própria palavra."""
    w = _clean(word)
    return PHONETIC_BR.get(w, w)


def _detect_difficult_sounds(word: str) -> list[str]:
    """Detecta sons difíceis para brasileiros em uma palavra."""
    tips = []
    w = word.lower()
    if "th" in w:
        tips.append("th")
    if w.startswith("r") or w.startswith("wr"):
        tips.append("r")
    if w.startswith("w") and not w.startswith("wr"):
        tips.append("w")
    if w.startswith("h"):
        tips.append("h")
    if w.endswith("ed"):
        tips.append("ed")
    if w.endswith("ing"):
        tips.append("ing")
    return tips


def analyze_pronunciation(target_phrase: str, spoken_text: str) -> dict:
    """
    Analisa pronúncia comparando frase alvo com o que foi falado.
    Retorna dict com feedback detalhado.
    """
    target_words = _clean(target_phrase).split()
    spoken_words = _clean(spoken_text).split()

    results = []
    correct_count = 0
    tips_shown = set()
    tip_messages = []

    for i, target_w in enumerate(target_words):
        spoken_w = spoken_words[i] if i < len(spoken_words) else ""
        is_correct = (spoken_w == target_w)

        phonetic_target = get_word_phonetic(target_w)
        phonetic_spoken = get_word_phonetic(spoken_w) if spoken_w else "(silêncio)"

        result = {
            "target": target_w,
            "spoken": spoken_w,
            "correct": is_correct,
            "phonetic_target": phonetic_target,
            "phonetic_spoken": phonetic_spoken,
        }

        if is_correct:
            correct_count += 1
        else:
            # Gera mensagem do professor
            if spoken_w:
                result["feedback"] = f"Você disse '{phonetic_spoken}', o correto é '{phonetic_target}'"
            else:
                result["feedback"] = f"Palavra não detectada. A pronúncia é '{phonetic_target}'"

            # Detecta sons difíceis e gera dicas
            for sound in _detect_difficult_sounds(target_w):
                if sound not in tips_shown:
                    tips_shown.add(sound)
                    tip_messages.append(PRONUNCIATION_TIPS[sound])

        results.append(result)

    total = len(target_words)
    score = int((correct_count / total) * 100) if total > 0 else 0

    return {
        "results": results,
        "score": score,
        "correct_count": correct_count,
        "total": total,
        "tips": tip_messages,
    }


# ---------------------------------------------------------------------------
# RENDER — Interface Streamlit
# ---------------------------------------------------------------------------

def render_pronunciation_coach(username: str):
    """Renderiza o módulo Professor de Pronúncia AI."""

    # Load Vosk model (cached)
    @st.cache_resource
    def _load_vosk():
        if os.path.exists(config.MODEL_DIR):
            return Model(config.MODEL_DIR)
        return None

    model_vosk = _load_vosk()
    if not model_vosk:
        st.error("⚠️ Modelo de reconhecimento de voz não encontrado. Verifique a pasta 'model'.")
        return

    # Estado do modo professor
    if "coach_module" not in st.session_state:
        st.session_state["coach_module"] = None
    if "coach_idx" not in st.session_state:
        st.session_state["coach_idx"] = 0
    if "coach_attempt" not in st.session_state:
        st.session_state["coach_attempt"] = 0
    if "coach_history" not in st.session_state:
        st.session_state["coach_history"] = []

    # ===== HEADER =====
    st.markdown("""
<div style="text-align:center; padding:20px 0 10px;">
<div style="display:inline-block; background:rgba(6,182,212,0.1); border:1px solid rgba(6,182,212,0.25); padding:6px 20px; border-radius:99px; font-size:12px; font-weight:700; letter-spacing:2px; color:#22d3ee; text-transform:uppercase; margin-bottom:12px;">🎓 MODO PROFESSOR</div>
<h2 style="font-size:32px; font-weight:900; color:#fff; margin:10px 0 6px;">Professor de Pronúncia AI</h2>
<p style="color:#94a3b8; font-size:15px;">Ouça, repita e receba correções detalhadas como um professor real.</p>
</div>
""", unsafe_allow_html=True)

    # ===== SELEÇÃO DE MÓDULO =====
    if st.session_state["coach_module"] is None:
        st.markdown("""
<div style="text-align:center; margin:20px 0;">
<h3 style="color:#e2e8f0; font-size:20px;">Escolha o módulo para treinar:</h3>
</div>
""", unsafe_allow_html=True)

        # Grid de módulos (3 colunas)
        modulos = config.MODULOS
        for i in range(0, len(modulos), 3):
            cols = st.columns(3)
            batch = modulos[i:i+3]
            for idx, (titulo, arquivo, _url) in enumerate(batch):
                with cols[idx]:
                    emoji = config.MODULOS_EMOJI.get(titulo, "📚")
                    if st.button(f"{emoji} {titulo}", key=f"coach_mod_{arquivo}", use_container_width=True):
                        st.session_state["coach_module"] = arquivo
                        st.session_state["coach_idx"] = 0
                        st.session_state["coach_attempt"] = 0
                        st.session_state["coach_history"] = []
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅ VOLTAR AO MENU", key="coach_back_menu"):
            st.session_state['pagina'] = 'inicio'
            st.rerun()
        return

    # ===== TREINO ATIVO =====
    arquivo = st.session_state["coach_module"]
    modulo_nome = arquivo.replace(".csv", "").upper()

    # Carrega banco (cached)
    @st.cache_data(ttl=3600, show_spinner=False)
    def _load_csv(f):
        import pandas as pd
        caminho = os.path.join(config.CSV_DIR, f)
        if os.path.exists(caminho):
            df = pd.read_csv(caminho, on_bad_lines='skip', encoding='utf-8')
            return df.fillna("").to_dict('records')
        return []

    banco = _load_csv(arquivo)
    if not banco:
        st.error("Módulo não encontrado.")
        st.session_state["coach_module"] = None
        st.rerun()
        return

    idx = int(st.session_state["coach_idx"])
    total = len(banco)

    if idx >= total:
        # Sessão completa
        _render_session_complete(st.session_state["coach_history"], total)
        return

    atual = banco[idx]
    frase_en = str(atual.get("en", ""))
    frase_pt = str(atual.get("pt", ""))

    # Toolbar
    c_nav1, c_info, c_nav2, c_exit = st.columns([1, 3, 1, 1])
    with c_nav1:
        if idx > 0:
            if st.button("⬅ Anterior", key="coach_prev"):
                st.session_state["coach_idx"] = idx - 1
                st.session_state["coach_attempt"] = 0
                st.rerun()
    with c_info:
        st.markdown(f"""
<div style="text-align:center; padding:4px 0;">
<span style="font-size:14px; color:#a78bfa; font-weight:600;">{modulo_nome}</span>
<span style="color:#64748b; margin:0 8px;">|</span>
<span style="font-size:14px; color:#94a3b8;">Frase {idx+1} de {total}</span>
</div>""", unsafe_allow_html=True)
    with c_nav2:
        if st.button("Próxima ➡", key="coach_next"):
            st.session_state["coach_idx"] = idx + 1
            st.session_state["coach_attempt"] = 0
            st.rerun()
    with c_exit:
        if st.button("❌ Sair", key="coach_exit"):
            st.session_state["coach_module"] = None
            st.rerun()

    # Barra de progresso
    pct = int((idx / total) * 100) if total > 0 else 0
    st.markdown(f"""
<div style="height:8px; background:rgba(30,20,60,0.5); border-radius:4px; overflow:hidden; margin:10px 0 24px;">
<div style="height:100%; width:{pct}%; background:linear-gradient(90deg,#06b6d4,#8b5cf6); border-radius:4px; transition:width 0.5s;"></div>
</div>""", unsafe_allow_html=True)

    # --- CARD DA FRASE ---
    pronunciation_guide = get_pronunciation_guide(frase_en)

    st.markdown(f"""
<div style="background:rgba(15,10,40,0.55); backdrop-filter:blur(16px); border:1px solid rgba(6,182,212,0.2); border-radius:24px; padding:36px; text-align:center; position:relative; overflow:hidden; margin-bottom:24px;">
<div style="position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,#06b6d4,#8b5cf6,#ec4899);"></div>

<div style="font-size:13px; color:#94a3b8; margin-bottom:8px; font-weight:500;">
<img src="https://flagcdn.com/w40/br.png" style="width:24px; height:24px; border-radius:50%; object-fit:cover; vertical-align:middle; margin-right:8px; border:2px solid rgba(255,255,255,0.1);">
{frase_pt}
</div>

<div style="font-size:36px; font-weight:800; color:#fff; margin:16px 0; line-height:1.3; text-shadow:0 2px 10px rgba(0,0,0,0.3); letter-spacing:-0.5px;">
<img src="https://flagcdn.com/w40/us.png" style="width:28px; height:28px; border-radius:50%; object-fit:cover; vertical-align:middle; margin-right:10px; border:2px solid rgba(255,255,255,0.1);">
{frase_en}
</div>

<div style="background:rgba(6,182,212,0.08); border:1px solid rgba(6,182,212,0.2); border-radius:16px; padding:14px 24px; margin-top:16px; display:inline-block;">
<div style="font-size:11px; color:#06b6d4; font-weight:700; letter-spacing:2px; text-transform:uppercase; margin-bottom:6px;">🔤 PRONÚNCIA</div>
<div style="font-size:22px; color:#22d3ee; font-weight:600; font-style:italic; letter-spacing:1px;">{pronunciation_guide}</div>
</div>
</div>
""", unsafe_allow_html=True)

    # --- AUDIO DO PROFESSOR ---
    modulo_slug = os.path.splitext(arquivo)[0]
    audio_id = atual.get("id", f"{modulo_slug}_{idx}")
    path_ref = os.path.join(config.AUDIOS_DIR, f"{modulo_slug}_{audio_id}.mp3")
    if not os.path.exists(path_ref):
        try:
            gTTS(text=frase_en, lang='en').save(path_ref)
        except Exception:
            pass

    st.markdown("""
<div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
<span style="font-size:13px; color:#a78bfa; font-weight:700; letter-spacing:1px;">🔊 OUÇA O PROFESSOR</span>
</div>""", unsafe_allow_html=True)

    if os.path.exists(path_ref):
        st.audio(path_ref)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # --- GRAVAÇÃO DO ALUNO ---
    st.markdown("""
<div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
<span style="font-size:13px; color:#22d3ee; font-weight:700; letter-spacing:1px;">🎤 SUA VEZ — REPITA A FRASE</span>
</div>""", unsafe_allow_html=True)

    c_mic, c_retry = st.columns([3, 1], gap="small")
    with c_mic:
        gravacao = mic_recorder(
            start_prompt="🔴 GRAVAR",
            stop_prompt="⏹️ PARAR",
            format="wav",
            key=f"coach_mic_{idx}_{st.session_state['coach_attempt']}"
        )
    with c_retry:
        if st.button("🔄 REPETIR", key="coach_retry", use_container_width=True):
            st.session_state["coach_attempt"] += 1
            st.rerun()

    # --- ANÁLISE & FEEDBACK ---
    if gravacao:
        audio_data = io.BytesIO(gravacao['bytes'])
        with wave.open(audio_data, 'rb') as wf:
            rec = KaldiRecognizer(model_vosk, wf.getframerate())
            rec.AcceptWaveform(wf.readframes(wf.getnframes()))
            ouvida = json.loads(rec.FinalResult()).get("text", "").lower()

        if not ouvida.strip():
            st.warning("🤔 Não consegui ouvir nada. Tente falar mais alto e perto do microfone.")
            return

        # Analisa pronúncia
        analysis = analyze_pronunciation(frase_en, ouvida)

        # O que o sistema ouviu
        st.markdown(f"""
<div style="background:rgba(15,10,40,0.7); backdrop-filter:blur(12px); border:1.5px solid rgba(6,182,212,0.3); border-left:5px solid #06b6d4; border-radius:16px; padding:18px 22px; margin:16px 0;">
<div style="font-size:11px; font-weight:700; letter-spacing:2px; color:#06b6d4; text-transform:uppercase; margin-bottom:8px;">🎤 VOCÊ DISSE:</div>
<div style="font-size:20px; font-weight:600; color:#f8fafc;">{ouvida.upper()}</div>
</div>""", unsafe_allow_html=True)

        # Score grande
        _pct_class = "background:linear-gradient(135deg,#34d399,#06b6d4,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;" if analysis["score"] >= 80 else "color:#f43f5e;"
        st.markdown(f"""
<div style="text-align:center; margin:20px 0;">
<div style="font-size:64px; font-weight:900; {_pct_class}">{analysis['score']}%</div>
<div style="font-size:13px; color:#94a3b8; font-weight:600; letter-spacing:1px;">PRECISÃO DA PRONÚNCIA</div>
</div>""", unsafe_allow_html=True)

        # Feedback palavra por palavra
        st.markdown("""
<div style="font-size:13px; color:#a78bfa; font-weight:700; letter-spacing:1px; margin-bottom:12px;">📝 ANÁLISE DETALHADA</div>""", unsafe_allow_html=True)

        for r in analysis["results"]:
            if r["correct"]:
                st.markdown(f"""
<div style="display:flex; align-items:center; gap:12px; padding:10px 16px; margin:6px 0; background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.2); border-radius:12px;">
<span style="font-size:18px;">✅</span>
<div>
<span style="font-weight:700; font-size:16px; color:#34d399;">{r['target'].upper()}</span>
<span style="color:#64748b; font-size:13px; margin-left:8px;">({r['phonetic_target']})</span>
<span style="color:#34d399; font-size:13px; margin-left:8px;">— Perfeito!</span>
</div>
</div>""", unsafe_allow_html=True)
            else:
                feedback_msg = r.get("feedback", "")
                st.markdown(f"""
<div style="padding:14px 18px; margin:8px 0; background:rgba(244,63,94,0.06); border:1px solid rgba(244,63,94,0.2); border-left:4px solid #f43f5e; border-radius:12px;">
<div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
<span style="font-size:18px;">❌</span>
<span style="font-weight:700; font-size:16px; color:#f43f5e;">{r['target'].upper()}</span>
<span style="color:#64748b; font-size:13px;">→ correto: <strong style="color:#22d3ee;">{r['phonetic_target']}</strong></span>
</div>
<div style="font-size:14px; color:#fca5a5; padding-left:32px;">🤖 {feedback_msg}</div>
</div>""", unsafe_allow_html=True)

        # Dicas de entonação
        if analysis["tips"]:
            st.markdown("""
<div style="margin-top:20px; font-size:13px; color:#f59e0b; font-weight:700; letter-spacing:1px; margin-bottom:10px;">🎯 DICAS DO PROFESSOR</div>""", unsafe_allow_html=True)
            for tip in analysis["tips"]:
                st.markdown(f"""
<div style="padding:12px 18px; margin:6px 0; background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.2); border-radius:12px; font-size:14px; color:#fbbf24;">
{tip}
</div>""", unsafe_allow_html=True)

        # Salva no histórico
        st.session_state["coach_history"].append({
            "phrase": frase_en,
            "score": analysis["score"],
            "errors": [r["target"] for r in analysis["results"] if not r["correct"]],
        })

        # Registra erros no banco (aprendizado adaptativo)
        target_words = _clean(frase_en).split()
        wrong_words = [r["target"] for r in analysis["results"] if not r["correct"]]
        database.record_word_errors(username, wrong_words, target_words)

        # XP
        if analysis["correct_count"] > 0:
            xp_gain = analysis["correct_count"] * 2  # 2 XP por acerto no modo professor
            current_xp = int(st.session_state.get("xp", 0))
            st.session_state["xp"] = current_xp + xp_gain
            st.toast(f"+{xp_gain} XP (Modo Professor)", icon="🎓")

        # Botões de ação
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 TENTAR DE NOVO", key="coach_retry_after", use_container_width=True):
                st.session_state["coach_attempt"] += 1
                st.rerun()
        with c2:
            if analysis["score"] >= 50:
                if st.button("➡️ PRÓXIMA FRASE", key="coach_next_after", use_container_width=True):
                    st.session_state["coach_idx"] = idx + 1
                    st.session_state["coach_attempt"] = 0
                    st.rerun()
            else:
                st.button("➡️ PRÓXIMA FRASE", key="coach_next_after_disabled",
                          use_container_width=True, disabled=True,
                          help="Alcance pelo menos 50% para avançar")

        # Audio da palavra errada (repete isoladamente)
        errors = [r for r in analysis["results"] if not r["correct"]]
        if errors:
            st.markdown("""
<div style="margin-top:24px; font-size:13px; color:#a78bfa; font-weight:700; letter-spacing:1px; margin-bottom:10px;">🔊 OUÇA AS PALAVRAS ERRADAS</div>""", unsafe_allow_html=True)
            for err in errors[:5]:  # Max 5
                word = err["target"]
                phonetic = err["phonetic_target"]
                word_audio_path = os.path.join(config.AUDIOS_DIR, f"_word_{word}.mp3")
                if not os.path.exists(word_audio_path):
                    try:
                        gTTS(text=word, lang='en', slow=True).save(word_audio_path)
                    except Exception:
                        continue
                col_w, col_a = st.columns([1, 2])
                with col_w:
                    st.markdown(f"""
<div style="padding:8px 14px; background:rgba(139,92,246,0.08); border-radius:10px; text-align:center;">
<span style="font-weight:700; font-size:16px; color:#e2e8f0;">{word.upper()}</span><br>
<span style="font-size:14px; color:#a78bfa; font-style:italic;">{phonetic}</span>
</div>""", unsafe_allow_html=True)
                with col_a:
                    st.audio(word_audio_path)


def _render_session_complete(history: list[dict], total: int):
    """Renderiza tela de sessão completa."""
    completed = len(history)
    avg_score = int(sum(h["score"] for h in history) / completed) if completed > 0 else 0
    all_errors = []
    for h in history:
        all_errors.extend(h.get("errors", []))

    # Palavras mais erradas
    from collections import Counter
    error_counts = Counter(all_errors).most_common(10)

    st.markdown(f"""
<div style="text-align:center; padding:40px 20px; background:linear-gradient(180deg,rgba(6,182,212,0.1),rgba(139,92,246,0.05)); border:1px solid rgba(6,182,212,0.2); border-radius:24px; margin:20px 0;">
<div style="font-size:48px; margin-bottom:10px;">🎉</div>
<h2 style="color:#fff; font-size:28px; margin:0 0 10px;">Sessão Completa!</h2>
<div style="font-size:64px; font-weight:900; background:linear-gradient(135deg,#06b6d4,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent; margin:20px 0;">{avg_score}%</div>
<div style="font-size:14px; color:#94a3b8;">MÉDIA DE PRECISÃO</div>
<div style="font-size:14px; color:#a78bfa; margin-top:10px;">{completed} frases praticadas</div>
</div>
""", unsafe_allow_html=True)

    if error_counts:
        st.markdown("""
<div style="font-size:15px; color:#f59e0b; font-weight:700; margin:20px 0 12px;">⚠️ Palavras para revisar:</div>""", unsafe_allow_html=True)
        for word, count in error_counts:
            phonetic = get_word_phonetic(word)
            st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; padding:10px 16px; margin:4px 0; background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.15); border-radius:10px;">
<div><span style="font-weight:700; color:#fbbf24;">{word.upper()}</span> <span style="color:#94a3b8; font-size:13px;">({phonetic})</span></div>
<span style="color:#f59e0b; font-size:13px; font-weight:600;">{count}x errada</span>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 TREINAR NOVAMENTE", key="coach_restart", use_container_width=True):
            st.session_state["coach_idx"] = 0
            st.session_state["coach_attempt"] = 0
            st.session_state["coach_history"] = []
            st.rerun()
    with c2:
        if st.button("📚 OUTRO MÓDULO", key="coach_change_mod", use_container_width=True):
            st.session_state["coach_module"] = None
            st.session_state["coach_idx"] = 0
            st.session_state["coach_history"] = []
            st.rerun()

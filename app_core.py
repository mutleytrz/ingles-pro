from __future__ import annotations
# app_core.py — Ponto de entrada principal (multi-usuario)
# ====================================================================
# VERSAO: PROFESSIONAL DARK TIER + PT AUDIO (100% ONLY)
# ====================================================================

import streamlit as st
from gtts import gTTS
import os
import base64
from streamlit_mic_recorder import mic_recorder
import string
import json
import io
import wave
import random
import time
import pandas as pd
from vosk import Model, KaldiRecognizer
from typing import Optional

import config
import database
import auth
import auth
import icons
import admin_panel
import neural_sleep

# -- Inicializa banco de dados --
database.init_db()

# -- CONFIG --
st.set_page_config(
    page_title="English Pro",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed", # Sidebar escondida por padrao
)


# -- FUNCOES UTILITARIAS --

def get_img_64(pasta: str, nome_arquivo: str) -> str:
    caminho = os.path.join(pasta, nome_arquivo)
    if os.path.exists(caminho):
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


def get_cover_img_64(nome_modulo: str) -> str:
    """Carrega imagem de capa salva localmente ou retorna vazio."""
    filename = f"{nome_modulo.lower()}.jpg"
    caminho = os.path.join(config.DATA_DIR, "assets", "covers", filename)
    if os.path.exists(caminho):
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


def _get_xp_tier(xp: int) -> tuple[str, str, str]:
    """Retorna (nome_tier, cor_hex, emoji) baseado no XP."""
    if xp >= 5000: return ("MASTER", "#ff6b6b", "👑")
    if xp >= 2000: return ("DIAMOND", "#a78bfa", "💎")
    if xp >= 800:  return ("GOLD", "#fbbf24", "🏆")
    if xp >= 300:  return ("SILVER", "#94a3b8", "🥈")
    return ("BRONZE", "#cd7f32", "🥉")


def aplicar_estilo() -> None:
    # DESIGN: "COSMIC ACADEMY" — Premium Futuristic Design
    st.markdown("""
    <style>
    /* ============================================
       STATIC STYLING (PERFORMANCE OPTIMIZED)
       ============================================ */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }


    /* ============================================
       GLOBAL SETTINGS & COSMIC BACKGROUND (PREMIUM STATIC)
       ============================================ */
    .stApp {
        background-color: #030014;
        background-image:
            radial-gradient(ellipse at 10% 20%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
            radial-gradient(ellipse at 90% 80%, rgba(6, 182, 212, 0.12) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, rgba(236, 72, 153, 0.08) 0%, transparent 60%),
            radial-gradient(circle at 30% 70%, rgba(59, 130, 246, 0.06) 0%, transparent 40%),
            radial-gradient(circle at 70% 30%, rgba(245, 158, 11, 0.05) 0%, transparent 40%);
        background-size: 200% 200%;
        color: #e2e8f0;
        font-family: 'Outfit', sans-serif;
        min-height: 100vh;
    }
    .stApp::before {
        content: '';
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background:
            radial-gradient(2px 2px at 20% 30%, rgba(255,255,255,0.15), transparent),
            radial-gradient(2px 2px at 40% 70%, rgba(255,255,255,0.1), transparent),
            radial-gradient(1px 1px at 60% 20%, rgba(255,255,255,0.12), transparent),
            radial-gradient(2px 2px at 80% 50%, rgba(255,255,255,0.08), transparent),
            radial-gradient(1px 1px at 10% 80%, rgba(139,92,246,0.2), transparent),
            radial-gradient(1px 1px at 90% 10%, rgba(6,182,212,0.2), transparent),
            radial-gradient(1px 1px at 50% 90%, rgba(236,72,153,0.15), transparent),
            radial-gradient(1.5px 1.5px at 25% 55%, rgba(255,255,255,0.1), transparent),
            radial-gradient(1px 1px at 75% 45%, rgba(255,255,255,0.08), transparent),
            radial-gradient(1.5px 1.5px at 15% 10%, rgba(255,255,255,0.12), transparent),
            radial-gradient(1px 1px at 65% 85%, rgba(255,255,255,0.06), transparent),
            radial-gradient(2px 2px at 45% 40%, rgba(255,255,255,0.07), transparent);
        pointer-events: none; z-index: 0;
    }

    header[data-testid="stHeader"], footer { display: none !important; }
    .block-container { padding-top: 1.5rem !important; max-width: 1320px !important; position: relative; z-index: 1; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(3, 0, 20, 0.5); }
    ::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #8b5cf6, #06b6d4); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, #a78bfa, #22d3ee); }

    /* Typography */
    h1, h2, h3 { color: #f8fafc !important; font-family: 'Outfit', sans-serif; letter-spacing: -0.03em; }
    h1 { font-weight: 800 !important; }
    h2 { font-weight: 700 !important; }
    p { line-height: 1.7; color: #a5b4c8; font-family: 'Outfit', sans-serif; }

    /* ============================================
       LOGIN FORM STYLING (COSMIC GLASS)
       ============================================ */
    [data-testid="stForm"] {
        background: rgba(15, 10, 40, 0.65);
        backdrop-filter: blur(24px) saturate(1.5);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 28px;
        padding: 44px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        /* animation: fadeInScale 0.7s ease-out; REMOVED */
    }
    [data-testid="stTextInput"] input {
        background: rgba(3, 0, 20, 0.6) !important;
        border: 1.5px solid rgba(139, 92, 246, 0.15) !important;
        color: #f8fafc !important;
        border-radius: 14px !important;
        padding: 14px 18px !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 15px !important;
        transition: all 0.3s ease;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15), 0 0 20px rgba(139, 92, 246, 0.1) !important;
    }
    [data-testid="stTextInput"] label {
        font-family: 'Outfit', sans-serif !important;
        color: #c4b5fd !important;
        font-weight: 500 !important;
    }

    /* ============================================
       BUTTONS (COSMIC GRADIENT)
       ============================================ */
    div.stButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 50%, #4f46e5 100%);
        color: white !important;
        border: none;
        padding: 15px 30px;
        border-radius: 14px;
        font-weight: 700;
        font-size: 15px;
        font-family: 'Outfit', sans-serif;
        letter-spacing: 0.5px;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow:
            0 4px 15px rgba(124, 58, 237, 0.35),
            0 2px 4px rgba(124, 58, 237, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        width: 100%;
        text-transform: uppercase;
    }
    div.stButton > button:hover {
        transform: translateY(-3px) scale(1.01);
        box-shadow:
            0 12px 25px rgba(124, 58, 237, 0.45),
            0 4px 8px rgba(124, 58, 237, 0.25),
            0 0 30px rgba(139, 92, 246, 0.15);
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6366f1 100%);
    }
    div.stButton > button:active { transform: translateY(-1px) scale(0.99); }
    div.stButton > button:disabled {
        background: rgba(30, 20, 60, 0.6) !important;
        color: #64748b !important;
        cursor: not-allowed;
        box-shadow: none;
        transform: none;
        border: 1px solid rgba(100, 116, 139, 0.2);
    }

    /* ============================================
       TOP NAVBAR (FLOATING COSMIC)
       ============================================ */
    .top-nav {
        display: flex; justify-content: space-between; align-items: center;
        padding: 14px 28px;
        background: rgba(10, 5, 30, 0.75);
        backdrop-filter: blur(20px) saturate(1.8);
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 20px;
        margin-bottom: 36px;
        box-shadow:
            0 8px 32px rgba(0,0,0,0.3),
            0 0 20px rgba(139, 92, 246, 0.05),
            inset 0 1px 0 rgba(255,255,255,0.04);
        /* animation: fadeInUp 0.5s ease-out; REMOVED */
    }
    .app-logo {
        font-size: 22px; font-weight: 900; color: #f8fafc;
        letter-spacing: -0.5px; display: flex; align-items: center; gap: 4px;
        font-family: 'Outfit', sans-serif;
    }
    .app-logo span {
        background: linear-gradient(135deg, #8b5cf6, #06b6d4);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .user-pill {
        display: flex; align-items: center; gap: 14px;
        background: rgba(139, 92, 246, 0.06);
        padding: 8px 8px 8px 18px;
        border-radius: 99px;
        border: 1px solid rgba(139, 92, 246, 0.12);
    }
    .user-pill span { font-family: 'Outfit', sans-serif; font-size: 14px; font-weight: 500; }
    .xp-badge {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: #fff; font-weight: 800; font-size: 13px; padding: 7px 16px; border-radius: 99px;
        box-shadow: 0 3px 12px rgba(245, 158, 11, 0.4);
        /* animation: xpBounce 2s ease-in-out infinite; REMOVED */
        font-family: 'Outfit', sans-serif;
    }
    .xp-count {
        font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 14px;
        color: #fbbf24;
    }
    .xp-tier-badge {
        font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 12px;
        padding: 5px 14px; border-radius: 99px;
        /* animation: glowPulse 3s ease-in-out infinite; REMOVED */
    }

    /* ============================================
       HERO SECTION (HOME)
       ============================================ */
    .hero-badge {
        display: inline-block;
        background: rgba(139, 92, 246, 0.12);
        border: 1px solid rgba(139, 92, 246, 0.25);
        padding: 6px 20px; border-radius: 99px;
        font-size: 12px; font-weight: 700; letter-spacing: 2px;
        color: #c4b5fd; text-transform: uppercase;
        font-family: 'Outfit', sans-serif;
        /* animation: glowPulse 3s ease-in-out infinite; REMOVED */
    }
    .hero-title {
        font-size: 56px !important; font-weight: 900 !important;
        line-height: 1.1 !important; margin: 24px 0 16px !important;
        font-family: 'Outfit', sans-serif !important;
    }
    .hero-highlight {
        background: linear-gradient(135deg, #8b5cf6, #06b6d4, #ec4899, #f59e0b);
        background-size: 300% 300%;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        /* animation: textGradient 4s ease infinite; REMOVED */
    }
    .hero-subtitle {
        font-size: 18px !important; color: #94a3b8 !important;
        line-height: 1.6 !important; max-width: 600px;
        margin: 0 auto !important; font-weight: 400 !important;
    }

    /* ============================================
       FEATURE CARDS (HOME)
       ============================================ */
    .feature-card {
        background: rgba(15, 10, 40, 0.5);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(139, 92, 246, 0.12);
        border-radius: 24px;
        padding: 36px 28px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        /* animation: cardEntrance 0.6s ease-out backwards; REMOVED */
    }
    .feature-card::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #8b5cf6, #06b6d4, #ec4899);
        opacity: 0; transition: opacity 0.4s ease;
    }
    .feature-card:hover {
        transform: translateY(-8px);
        border-color: rgba(139, 92, 246, 0.3);
        box-shadow: 0 20px 50px -15px rgba(139, 92, 246, 0.2), 0 0 30px rgba(139, 92, 246, 0.08);
    }
    .feature-card:hover::before { opacity: 1; }
    .card-icon {
        width: 64px; height: 64px;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(6, 182, 212, 0.1));
        border-radius: 18px; display: flex; align-items: center; justify-content: center;
        font-size: 28px; margin-bottom: 20px;
        border: 1px solid rgba(139, 92, 246, 0.1);
        /* animation: float 4s ease-in-out infinite; REMOVED */
    }
    .card-title {
        font-family: 'Outfit', sans-serif; font-size: 20px; font-weight: 700;
        color: #f1f5f9; margin-bottom: 10px;
    }
    .card-desc {
        font-family: 'Outfit', sans-serif; font-size: 14px; color: #94a3b8; line-height: 1.6;
    }

    /* ============================================
       MODULE CARDS (COSMIC GRID)
       ============================================ */
    .module-card-wrap {
        perspective: 1200px;
        height: 100%;
        margin-bottom: 28px;
        /* animation: cardEntrance 0.6s ease-out backwards; REMOVED */
    }
    .module-card-inner {
        background: rgba(15, 10, 40, 0.55);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(139, 92, 246, 0.1);
        border-radius: 24px;
        overflow: hidden;
        transition: all 0.45s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        height: 100%;
        display: flex; flex-direction: column;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .module-card-inner::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 4px;
        background: linear-gradient(90deg, var(--card-accent, #8b5cf6), var(--card-accent-end, #06b6d4));
        z-index: 2;
    }
    .module-card-inner:hover {
        transform: translateY(-8px) rotateX(2deg);
        border-color: rgba(139, 92, 246, 0.35);
        box-shadow:
            0 25px 50px -12px rgba(0,0,0,0.5),
            0 0 30px rgba(139, 92, 246, 0.12),
            inset 0 1px 0 rgba(255,255,255,0.05);
        background: rgba(20, 15, 50, 0.7);
    }
    .module-cover-wrap {
        height: 170px; overflow: hidden; position: relative;
    }
    .module-cover {
        width: 100%; height: 100%; object-fit: cover;
        transition: transform 0.7s cubic-bezier(0.4, 0, 0.2, 1);
        filter: saturate(0.85) brightness(0.85);
    }
    .module-card-inner:hover .module-cover {
        transform: scale(1.08);
        filter: saturate(1.15) brightness(1.05);
    }
    .module-cover-overlay {
        position: absolute; bottom: 0; left: 0; right: 0; height: 60%;
        background: linear-gradient(to top, rgba(15, 10, 40, 0.9), transparent);
        pointer-events: none;
    }
    .module-version-tag {
        position: absolute; top: 12px; right: 12px;
        background: rgba(0,0,0,0.5); backdrop-filter: blur(8px);
        color: #c4b5fd; font-size: 10px; font-weight: 700;
        padding: 4px 10px; border-radius: 8px;
        letter-spacing: 1px; font-family: 'Outfit', sans-serif;
        border: 1px solid rgba(139,92,246,0.2);
    }
    .module-info {
        padding: 22px; flex: 1; display: flex; flex-direction: column;
    }
    .module-name {
        font-size: 17px; font-weight: 700; color: #f1f5f9;
        margin-bottom: 14px; display: flex; align-items: center; gap: 12px;
        font-family: 'Outfit', sans-serif;
    }
    .module-name svg { flex-shrink: 0; }
    .mod-progress-container { margin-top: auto; }
    .mod-prog-bar {
        height: 7px; background: rgba(30, 20, 60, 0.6);
        border-radius: 4px; overflow: hidden; margin-bottom: 10px;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);
    }
    .mod-prog-fill {
        height: 100%;
        background: linear-gradient(90deg, #8b5cf6, #06b6d4, #22d3ee);
        background-size: 200% 100%;
        border-radius: 4px;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        /* animation: progressGlow 2s ease-in-out infinite; REMOVED */
        box-shadow: 0 0 12px rgba(139, 92, 246, 0.4);
    }
    .mod-meta {
        display: flex; justify-content: space-between;
        font-size: 12px; color: #a5b4c8; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.8px;
        font-family: 'Outfit', sans-serif;
    }
    .mod-status-tag {
        display: inline-block; padding: 3px 10px; border-radius: 8px;
        font-size: 11px; font-weight: 700; letter-spacing: 0.5px;
        font-family: 'Outfit', sans-serif;
    }
    .mod-status-tag.concluido { background: rgba(16, 185, 129, 0.15); color: #34d399; }
    .mod-status-tag.andamento { background: rgba(139, 92, 246, 0.15); color: #a78bfa; }
    .mod-status-tag.pendente { background: rgba(100, 116, 139, 0.15); color: #94a3b8; }

    /* ============================================
       AULA UI - IMAGE (PREMIUM FRAME)
       ============================================ */
    .img-premium-wrap {
        width: 100%;
        height: 460px;
        background: rgba(15, 10, 40, 0.4);
        border-radius: 24px;
        overflow: hidden;
        border: 1px solid rgba(139, 92, 246, 0.15);
        box-shadow:
            0 25px 50px rgba(0,0,0,0.4),
            0 0 30px rgba(139, 92, 246, 0.05);
        position: relative;
        display: flex; align-items: center; justify-content: center;
        /* animation: slideInRight 0.6s ease-out; REMOVED */
    }
    .img-premium-wrap::after {
        content: '';
        position: absolute; bottom: 0; left: 0; right: 0; height: 40%;
        background: linear-gradient(to top, rgba(3, 0, 20, 0.5), transparent);
        pointer-events: none;
    }
    .img-premium-wrap img {
        width: 100%; height: 100%;
        object-fit: cover;
        object-position: center top;
        display: block;
        transition: transform 4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .img-premium-wrap:hover img { transform: scale(1.06); }

    /* Phrase Box */
    .phrase-box {
        background: rgba(15, 10, 40, 0.55);
        backdrop-filter: blur(16px) saturate(1.5);
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 24px;
        padding: 44px;
        text-align: center;
        position: relative;
        min-height: 300px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        /* animation: fadeInUp 0.5s ease-out; REMOVED */
        box-shadow: 0 15px 40px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.04);
        overflow: hidden;
    }
    .phrase-box::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #8b5cf6, #06b6d4, #ec4899);
    }
    .phrase-en {
        font-size: 34px; font-weight: 800; color: #fff;
        margin: 20px 0; line-height: 1.25;
        text-shadow: 0 2px 15px rgba(0,0,0,0.4);
        font-family: 'Outfit', sans-serif;
    }
    .phrase-pt {
        font-size: 17px; color: #a78bfa; font-weight: 500;
        letter-spacing: 0.5px; font-family: 'Outfit', sans-serif;
        background: rgba(139, 92, 246, 0.08); padding: 6px 18px; border-radius: 99px;
    }

    /* Feedback Words */
    .fb-container {
        display: flex; flex-wrap: wrap; justify-content: center;
        gap: 10px; margin-top: 28px; padding: 0 10px;
    }
    .fb-word {
        padding: 10px 20px; border-radius: 14px; font-weight: 700; font-size: 17px;
        font-family: 'Outfit', sans-serif;
        /* animation: wordPop 0.45s cubic-bezier(0.175, 0.885, 0.32, 1.275) backwards; REMOVED */
    }
    .fb-correct {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1.5px solid rgba(16, 185, 129, 0.3);
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.1);
    }
    .fb-wrong {
        background: rgba(244, 63, 94, 0.12);
        color: #f43f5e;
        border: 1.5px solid rgba(244, 63, 94, 0.3);
        box-shadow: 0 0 15px rgba(244, 63, 94, 0.1);
    }

    /* "O que o sistema ouviu" Box */
    .ouvi-box {
        background: rgba(15, 10, 40, 0.7);
        backdrop-filter: blur(12px);
        border: 1.5px solid rgba(6, 182, 212, 0.3);
        border-left: 5px solid #06b6d4;
        border-radius: 16px;
        padding: 18px 22px;
        margin: 16px 0;
        /* animation: fadeInUp 0.4s ease-out; REMOVED */
    }
    .ouvi-label {
        font-size: 11px; font-weight: 700; letter-spacing: 2px;
        color: #06b6d4; text-transform: uppercase;
        margin-bottom: 8px;
        font-family: 'Outfit', sans-serif;
    }
    .ouvi-text {
        font-size: 22px; font-weight: 600; color: #f8fafc;
        font-family: 'Outfit', sans-serif;
        line-height: 1.4;
    }

    /* Result Percent */
    .result-pct {
        font-size: 72px; font-weight: 900; margin: 28px 0;
        letter-spacing: -3px; font-family: 'Outfit', sans-serif;
        position: relative;
    }
    .result-pct.success {
        background: linear-gradient(135deg, #34d399 0%, #06b6d4 50%, #8b5cf6 100%);
        background-size: 200% 200%;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        /* animation: textGradient 3s ease infinite; REMOVED */
    }
    .result-pct.fail {
        color: #f43f5e;
    }

    /* Divider */
    .divider-glow {
        height: 2px; margin: 36px 0;
        background: linear-gradient(90deg,
            transparent, rgba(139, 92, 246, 0.3), rgba(6, 182, 212, 0.3),
            rgba(236, 72, 153, 0.2), transparent);
    }

    /* ============================================
       AULA PROGRESS & EXTRAS
       ============================================ */
    .prog-track {
        width: 100%; height: 10px;
        background: rgba(30, 20, 60, 0.5);
        border-radius: 5px; overflow: hidden; margin-bottom: 28px;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.4);
    }
    .prog-fill {
        height: 100%;
        background: linear-gradient(90deg, #8b5cf6, #06b6d4, #22d3ee);
        background-size: 200% 100%;
        border-radius: 5px;
        transition: width 0.7s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 0 14px rgba(139, 92, 246, 0.5);
        /* animation: shimmer 2s linear infinite; REMOVED */
    }
    .lesson-header {
        font-family: 'Outfit', sans-serif;
    }
    .lesson-header h3 {
        font-size: 24px !important; font-weight: 800 !important;
        letter-spacing: 0.5px;
    }
    .lesson-header .lesson-count {
        font-size: 14px; color: #a78bfa; font-weight: 500;
        background: rgba(139, 92, 246, 0.1);
        padding: 3px 12px; border-radius: 8px;
    }
    .skip-btn button {
        background: rgba(139, 92, 246, 0.08) !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        color: #c4b5fd !important; box-shadow: none !important;
        padding: 8px 18px !important; font-size: 13px !important;
        border-radius: 12px !important;
    }
    .skip-btn button:hover {
        background: rgba(139, 92, 246, 0.15) !important;
        color: #f1f5f9 !important;
        border-color: rgba(139, 92, 246, 0.4) !important;
    }

    /* ============================================
       METRICS DASHBOARD
       ============================================ */
    .metric-hero {
        background:
            radial-gradient(circle at 30% 50%, rgba(139, 92, 246, 0.2), transparent 60%),
            radial-gradient(circle at 70% 50%, rgba(6, 182, 212, 0.15), transparent 60%),
            rgba(15, 10, 40, 0.5);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 28px; padding: 48px; text-align: center;
        margin-bottom: 44px;
        box-shadow: 0 0 50px rgba(139, 92, 246, 0.1), 0 20px 40px rgba(0,0,0,0.3);
        /* animation: fadeInScale 0.7s ease-out; REMOVED */
        position: relative; overflow: hidden;
    }
    .metric-hero::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #8b5cf6, #06b6d4, #ec4899, #f59e0b);
    }
    .metric-hero h1 {
        font-size: 72px !important; margin: 0 !important; color: #fff !important;
        text-shadow: 0 0 30px rgba(139, 92, 246, 0.5);
        font-family: 'Outfit', sans-serif !important; font-weight: 900 !important;
    }
    .metric-label {
        font-size: 13px; letter-spacing: 3px; color: #a78bfa;
        font-weight: 700; margin-top: 10px; text-transform: uppercase;
        font-family: 'Outfit', sans-serif;
    }

    .mod-metric-card {
        background: rgba(15, 10, 40, 0.5);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(139, 92, 246, 0.1);
        border-radius: 20px; padding: 22px; margin-bottom: 18px;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative; overflow: hidden;
    }
    .mod-metric-card::before {
        content: '';
        position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
        background: linear-gradient(180deg, #8b5cf6, #06b6d4);
        border-radius: 0 2px 2px 0;
    }
    .mod-metric-card:hover {
        transform: translateX(6px);
        background: rgba(20, 15, 50, 0.65);
        border-color: rgba(139, 92, 246, 0.25);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }
    .mod-prog-track {
        height: 6px; background: rgba(30, 20, 60, 0.5);
        border-radius: 3px; overflow: hidden; margin-top: 8px;
    }
    .mod-status-row {
        display: flex; justify-content: space-between;
        font-size: 12px; color: #a5b4c8; margin-top: 8px;
        font-family: 'Outfit', sans-serif; font-weight: 500;
    }

    /* ============================================
       SYS BADGE (Login page)
       ============================================ */
    .sys-badge {
        display: inline-block;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.25);
        color: #34d399;
        padding: 5px 16px; border-radius: 99px;
        font-size: 11px; font-weight: 700; letter-spacing: 2px;
        font-family: 'Outfit', sans-serif;
        /* animation: glowPulse 3s ease infinite; REMOVED */
    }

    /* ============================================
       AUDIO PLAYER & MIC RECORDER
       ============================================ */
    audio {
        width: 100%; border-radius: 12px;
        margin-top: 12px;
    }
    [data-testid="stAudio"] {
        border-radius: 14px; overflow: hidden;
    }

    /* Selection highlight */
    ::selection {
        background: rgba(139, 92, 246, 0.3);
        color: #f8fafc;
    }

    /* Streamlit tabs styling */
    [data-testid="stTabs"] button {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        color: #a5b4c8 !important;
        border-bottom-color: transparent !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #c4b5fd !important;
        border-bottom-color: #8b5cf6 !important;
    }

    /* Toast styling */
    [data-testid="stToast"] {
        font-family: 'Outfit', sans-serif !important;
    }

    /* Number input */
    [data-testid="stNumberInput"] input {
        background: rgba(3, 0, 20, 0.6) !important;
        border: 1px solid rgba(139, 92, 246, 0.15) !important;
        color: #f8fafc !important;
        border-radius: 10px !important;
        font-family: 'Outfit', sans-serif !important;
    }

    /* Checkbox */
    [data-testid="stCheckbox"] label {
        font-family: 'Outfit', sans-serif !important;
        color: #a5b4c8 !important;
    }

    /* Selectbox */
    [data-testid="stSelectbox"] > div > div {
        background: rgba(3, 0, 20, 0.6) !important;
        border: 1px solid rgba(139, 92, 246, 0.15) !important;
        border-radius: 10px !important;
        font-family: 'Outfit', sans-serif !important;
    }

    /* Toggle */
    [data-testid="stToggle"] label {
        font-family: 'Outfit', sans-serif !important;
    }

    /* ============================================
       HOME PAGE — RADICAL REDESIGN
       ============================================ */
    .home-hero-wrap {
        position: relative;
        padding: 60px 0 40px;
        text-align: center;
        overflow: hidden;
    }
    .home-hero-wrap::before {
        content: '';
        position: absolute; top: -50%; left: -20%; width: 140%; height: 200%;
        background:
            radial-gradient(ellipse at 20% 50%, rgba(139, 92, 246, 0.2) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 50%, rgba(6, 182, 212, 0.15) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 20%, rgba(236, 72, 153, 0.1) 0%, transparent 50%);
        background-size: 200% 200%;
        pointer-events: none;
        z-index: 0;
    }
    .home-hero-wrap > * { position: relative; z-index: 1; }
    .home-hero-wrap .hero-title {
        font-size: 62px !important; font-weight: 900 !important;
        line-height: 1.05 !important; margin: 28px 0 20px !important;
    }
    .home-hero-wrap .hero-subtitle {
        font-size: 19px !important; max-width: 560px;
    }

    /* Stats Grid */
    .stats-grid {
        display: flex; justify-content: center; gap: 28px;
        margin: 48px auto 0; max-width: 700px;
        flex-wrap: wrap;
    }
    .stat-card {
        background: rgba(15, 10, 40, 0.6);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 20px;
        padding: 28px 32px;
        text-align: center;
        flex: 1; min-width: 160px;
        position: relative;
        overflow: hidden;
        transition: all 0.35s ease;
    }
    .stat-card:hover {
        transform: translateY(-4px);
        border-color: rgba(139, 92, 246, 0.35);
        box-shadow: 0 15px 30px rgba(0,0,0,0.3);
    }
    .stat-card::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: var(--stat-accent, linear-gradient(90deg, #8b5cf6, #06b6d4));
    }
    .stat-number {
        font-size: 36px; font-weight: 900; color: #fff;
        font-family: 'Outfit', sans-serif;
        margin-bottom: 6px;
        background: linear-gradient(135deg, #fff, #c4b5fd);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .stat-label {
        font-size: 12px; font-weight: 700; letter-spacing: 2px;
        color: #a78bfa; text-transform: uppercase;
        font-family: 'Outfit', sans-serif;
    }

    /* Feature Cards — Large Horizontal */
    .feature-grid {
        display: flex; flex-direction: column; gap: 20px;
        margin: 50px auto 0; max-width: 100%;
    }
    .feature-row {
        display: flex; gap: 20px;
    }
    .ft-card {
        background: rgba(15, 10, 40, 0.5);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(139, 92, 246, 0.1);
        border-radius: 24px;
        padding: 32px 36px;
        display: flex; align-items: center; gap: 28px;
        flex: 1;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        /* animation: cardEntrance 0.6s ease-out backwards; REMOVED */
        cursor: pointer;
    }
    .ft-card:hover {
        transform: translateY(-6px);
        border-color: rgba(139, 92, 246, 0.3);
        box-shadow: 0 20px 50px -15px rgba(139, 92, 246, 0.2), 0 0 30px rgba(139, 92, 246, 0.05);
        background: rgba(20, 15, 50, 0.65);
    }
    .ft-card::before {
        content: '';
        position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
        background: var(--ft-accent, linear-gradient(180deg, #8b5cf6, #06b6d4));
        border-radius: 2px;
    }
    .ft-icon-ring {
        width: 72px; height: 72px; min-width: 72px;
        border-radius: 20px;
        background: var(--ft-bg, rgba(139, 92, 246, 0.1));
        border: 1.5px solid var(--ft-border, rgba(139, 92, 246, 0.2));
        display: flex; align-items: center; justify-content: center;
        font-size: 32px;
        /* animation: float 5s ease-in-out infinite; REMOVED */
    }
    .ft-content { flex: 1; }
    .ft-title {
        font-size: 20px; font-weight: 800; color: #f1f5f9;
        margin-bottom: 6px; font-family: 'Outfit', sans-serif;
    }
    .ft-desc {
        font-size: 14px; color: #94a3b8; line-height: 1.5;
        font-family: 'Outfit', sans-serif;
    }
    .ft-arrow {
        font-size: 20px; color: #64748b;
        transition: all 0.3s ease;
    }
    .ft-card:hover .ft-arrow {
        color: #c4b5fd;
        transform: translateX(4px);
    }

    /* Big CTA Button */
    .cta-wrap {
        display: flex; justify-content: center; gap: 16px;
        margin-top: 36px;
        flex-wrap: wrap;
    }

    /* Module Selection Header */
    .mod-sel-header {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 36px; padding-bottom: 20px;
        border-bottom: 1px solid rgba(139, 92, 246, 0.1);
    }
    .mod-sel-header h2 {
        font-size: 28px !important; font-weight: 800 !important;
        margin: 0 !important; display: flex; align-items: center; gap: 12px;
    }
    .mod-sel-header .mod-count {
        font-size: 13px; color: #a78bfa; font-weight: 600;
        background: rgba(139, 92, 246, 0.1);
        padding: 5px 14px; border-radius: 99px;
        font-family: 'Outfit', sans-serif;
    }

    /* Section Divider */
    .section-divider {
        display: flex; align-items: center; gap: 16px;
        margin: 50px 0 36px;
    }
    .section-divider .line {
        flex: 1; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.2), transparent);
    }
    .section-divider .label {
        font-size: 13px; font-weight: 700; letter-spacing: 2px;
        color: #8b5cf6; text-transform: uppercase;
        font-family: 'Outfit', sans-serif;
        white-space: nowrap;
    }

    /* Metrics Redesign */
    .metrics-header {
        text-align: center; margin-bottom: 40px;
    }
    .metrics-header h2 {
        font-size: 32px !important; margin-bottom: 8px !important;
    }
    .metrics-header .subtitle {
        font-size: 15px; color: #94a3b8;
        font-family: 'Outfit', sans-serif;
    }

</style>
""", unsafe_allow_html=True)


def carregar_banco_especifico(nome_arquivo: str) -> list[dict]:
    caminho = os.path.join(config.CSV_DIR, nome_arquivo)
    if os.path.exists(caminho):
        df = pd.read_csv(caminho, on_bad_lines='skip', encoding='utf-8')
        return df.fillna("").to_dict('records')
    return []


def limpar(t: str) -> str:
    return str(t).lower().strip().translate(str.maketrans('', '', string.punctuation))


# -- ESTADO --
for k, v in {
    'pagina': 'inicio',
    'arquivo_atual': 'palavras.csv',
    'indice': 0, 'xp': 0, 'porc_atual': 0, 'tentativa': 0
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

aplicar_estilo()


@st.cache_resource
def carregar_vosk():
    if os.path.exists(config.MODEL_DIR):
        return Model(config.MODEL_DIR)
    return None

model_vosk = carregar_vosk()




# ========================================================
# AUTENTICACAO
# ========================================================
# ========================================================
username = auth.render_login()
if username is None:
    st.stop()

    # -----------------------------------------------------------
    # FIX: Prevents session leaking (User A data persisting to User B)
    # DISABLED: Causing issues with F5 refresh. Auth handles cleanup.
    # -----------------------------------------------------------
    # if 'logged_in_user' not in st.session_state:
    #     st.session_state['logged_in_user'] = None
    #
    # if st.session_state['logged_in_user'] != username:
    #     # Detected user switch or fresh login
    #     st.session_state['logged_in_user'] = username
    #    
    #     # 1. Clear critical session keys - FIX: Only if not matching expected structure
    #     # This prevents accidental wipe on reload
    #     keys_to_reset = ['xp', 'indice', 'porc_atual', 'tentativa', 'pagina', 'arquivo_atual', '_progresso_carregado']
    #     if st.session_state['logged_in_user'] is not None:
    #          # Only reset if we are definitely switching users (e.g. None -> User or User A -> User B)
    #         for k in keys_to_reset:
    #             if k in st.session_state:
    #                 del st.session_state[k]
    #            
    #     # 2. Re-apply defaults for safety
    #     dt_defaults = {
    #         'pagina': 'inicio',
    #         'arquivo_atual': 'palavras.csv',
    #         'indice': 0, 'xp': 0, 'porc_atual': 0, 'tentativa': 0
    #     }
    #     for k, v in dt_defaults.items():
    #         st.session_state[k] = v
        
    # 3. Force rerun removed to avoid infinite reload loops on some systems
    # st.rerun()  <-- REMOVED to improve stability
    pass
if username is None:
    st.stop()

is_admin = database.is_user_admin(username)


# -- NAV BAR --
_tier_name, _tier_color, _tier_emoji = _get_xp_tier(int(st.session_state['xp']))
st.markdown(f"""
<div class="top-nav">
    <div class="app-logo">🚀 ENGLISH<span>PRO</span></div>
    <div class="user-pill">
        <span>👤 {st.session_state.get('name', username)}</span>
        <span class="xp-tier-badge" style="background:rgba(139,92,246,0.1);color:{_tier_color};border:1px solid {_tier_color}33;">{_tier_emoji} {_tier_name}</span>
        <span class="xp-badge">⭐ {st.session_state['xp']} XP</span>
    </div>
</div>
""", unsafe_allow_html=True)

# -- GOD MODE CHECK --
god_mode = st.session_state.get('god_mode', False)


# -- Progresso --
def salvar_progresso():
    database.save_progress(
        username=username,
        pagina=st.session_state['pagina'],
        arquivo_atual=st.session_state['arquivo_atual'],
        indice=st.session_state['indice'],
        xp=st.session_state['xp'],
        porc_atual=st.session_state['porc_atual'],
        tentativa=st.session_state['tentativa'],
    )
    database.save_module_progress(
        username=username,
        module_file=st.session_state['arquivo_atual'],
        indice=st.session_state['indice'],
    )

def carregar_progresso():
    dados = database.load_progress(username)
    if dados:
        for k, v in dados.items():
            st.session_state[k] = v
    else:
        # CRITICAL: Novo usuário (sem dados no banco) deve ter sessão LIMPA
        # Sobrescreve explicitamente para evitar herança de dados da sessão anterior
        defaults = {
            'pagina': 'inicio',
            'arquivo_atual': 'palavras.csv',
            'indice': 0, 'xp': 0, 'porc_atual': 0, 'tentativa': 0
        }
        for k, v in defaults.items():
            st.session_state[k] = v

if '_progresso_carregado' not in st.session_state:
    carregar_progresso()
    st.session_state['_progresso_carregado'] = True


# ========================================================
# ========================================================
# TELAS
# ========================================================

# -- SIDEBAR NAVIGATION --
with st.sidebar:
    st.markdown("### 🧭 Navegação")
    if st.button("🏠 Home / Início", use_container_width=True):
        st.session_state['pagina'] = 'inicio'
        st.rerun()
    
    if st.button("🌙 Modo Zen (Sleep)", use_container_width=True):
        st.session_state['pagina'] = 'neural_sleep'
        st.rerun()

    if is_admin:
        st.markdown("---")
        if st.button("🛡️ Painel Admin", use_container_width=True):
             st.session_state['pagina'] = 'admin_panel'
             st.rerun()
             
    st.markdown("---")
    auth.render_logout(location="sidebar")

# -- ROUTING --
if st.session_state['pagina'] == 'neural_sleep':
    neural_sleep.render_neural_mode(username)

elif st.session_state['pagina'] == 'admin_panel':
    if not is_admin:
        st.error("Acesso negado.")
    else:
        admin_panel.render_admin_panel(username)
        if st.button("⬅ Voltar ao App"):
            st.session_state['pagina'] = 'inicio'
            st.rerun()

elif st.session_state['pagina'] == 'inicio':
    # Calculate dynamic stats
    _all_progress = database.load_all_module_progress(username)
    _total_modules = len(config.MODULOS)
    _completed_modules = sum(1 for mod_file in [m[1] for m in config.MODULOS] if _all_progress.get(mod_file, 0) > 0 and carregar_banco_especifico(mod_file) and _all_progress.get(mod_file, 0) >= len(carregar_banco_especifico(mod_file)))
    _total_lessons = sum(len(carregar_banco_especifico(m[1])) for m in config.MODULOS if carregar_banco_especifico(m[1]))

    # ===== HERO SECTION — Immersive Cosmic Wrapper =====
    st.markdown(f"""
<div class="home-hero-wrap">
<div class="hero-badge">🧠 INTELIGÊNCIA ARTIFICIAL APLICADA</div>
<h1 class="hero-title">
Domine o Inglês com<br>
<span class="hero-highlight">Tecnologia de Ponta</span>
</h1>
<p class="hero-subtitle">
Reconhecimento de voz, feedback em tempo real e algoritmos adaptativos que evoluem com você.
</p>
<div class="stats-grid">
<div class="stat-card" style="--stat-accent: linear-gradient(90deg, #f59e0b, #f97316);">
<div class="stat-number">⭐ {st.session_state['xp']}</div>
<div class="stat-label">PONTOS XP</div>
</div>
<div class="stat-card" style="--stat-accent: linear-gradient(90deg, #8b5cf6, #6366f1);">
<div class="stat-number">📂 {_completed_modules}/{_total_modules}</div>
<div class="stat-label">MÓDULOS</div>
</div>
<div class="stat-card" style="--stat-accent: linear-gradient(90deg, #06b6d4, #22d3ee);">
<div class="stat-number">📖 {_total_lessons}</div>
<div class="stat-label">LIÇÕES TOTAIS</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)

    # ===== CTA BUTTONS =====
    _spacer1, _btn_col, _spacer2 = st.columns([1.5, 1, 1.5])
    with _btn_col:
        if st.button("🚀 COMEÇAR TREINO", use_container_width=True):
            st.session_state['pagina'] = 'selecao_modulos'
            salvar_progresso()
            st.rerun()

    # ===== SECTION DIVIDER =====
    st.markdown("""
<div class="section-divider">
<div class="line"></div>
<div class="label">✦ EXPLORE AS FUNCIONALIDADES ✦</div>
<div class="line"></div>
</div>
""", unsafe_allow_html=True)

    # ===== FEATURE CARDS — Large Horizontal Layout =====
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown("""
<div class="ft-card" style="--ft-accent:linear-gradient(180deg,#8b5cf6,#c084fc); --ft-bg:rgba(139,92,246,0.1); --ft-border:rgba(139,92,246,0.25); animation-delay:0.1s;">
<div class="ft-icon-ring">
<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#c084fc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
</div>
<div class="ft-content">
<div class="ft-title">Aprendizado Neural</div>
<div class="ft-desc">Algoritmos adaptativos que evoluem com seu progresso. O sistema aprende com seus erros e personaliza o treino.</div>
</div>
<div class="ft-arrow">→</div>
</div>
""", unsafe_allow_html=True)
        if st.button("ACESSAR TREINO", key="btn_card1_home", use_container_width=True):
            st.session_state['pagina'] = 'neural_sleep'
            salvar_progresso()
            st.rerun()

    with c_right:
        st.markdown("""
<div class="ft-card" style="--ft-accent:linear-gradient(180deg,#06b6d4,#22d3ee); --ft-bg:rgba(6,182,212,0.1); --ft-border:rgba(6,182,212,0.25); animation-delay:0.2s;">
<div class="ft-icon-ring">
<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#22d3ee" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
</div>
<div class="ft-content">
<div class="ft-title">Síntese de Voz</div>
<div class="ft-desc">Análise de pronúncia em tempo real com reconhecimento de voz avançado. Ouça, fale e melhore a cada sessão.</div>
</div>
<div class="ft-arrow">→</div>
</div>
""", unsafe_allow_html=True)
        if st.button("VER MÉTRICAS", key="btn_card2_home", use_container_width=True):
            st.session_state['pagina'] = 'metricas'
            salvar_progresso()
            st.rerun()

    # Full-width third card
    st.markdown("""
<div class="ft-card" style="--ft-accent:linear-gradient(180deg,#ec4899,#f472b6); --ft-bg:rgba(236,72,153,0.1); --ft-border:rgba(236,72,153,0.25); animation-delay:0.3s;">
<div class="ft-icon-ring">
<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#f472b6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
</div>
<div class="ft-content">
<div class="ft-title">Contexto Global</div>
<div class="ft-desc">13 módulos temáticos — do aeroporto ao hospital. Cenários imersivos cobrindo situações reais do dia a dia para você treinar com confiança.</div>
</div>
<div class="ft-arrow">→</div>
</div>
""", unsafe_allow_html=True)

    # ===== FOOTER SECTION =====
    st.markdown("<br>", unsafe_allow_html=True)
    _l1, _l2, _l3 = st.columns([2, 1, 2])
    with _l2:
        is_admin_check = database.is_user_admin(username)
        if is_admin_check:
             if st.button("🛡️ PAINEL ADMIN", use_container_width=True):
                 st.session_state['pagina'] = 'admin_panel'
                 st.rerun()
             st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        
        auth.render_logout(location="main")




elif st.session_state['pagina'] == 'metricas':
    st.markdown("<h2 style='text-align:center;'>📊 Painel Analítico</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center; color:#64748b; font-size:14px; margin-bottom:30px;'>Progresso de <strong style='color:#e2e8f0;'>{st.session_state.get('name', username)}</strong></div>", unsafe_allow_html=True)
    
    xp_total = st.session_state['xp']
    _m_tier, _m_color, _m_emoji = _get_xp_tier(int(xp_total))
    st.markdown(f"""
<div class="metric-hero">
<h1>⭐ {xp_total}</h1>
<div class="metric-label">XP TOTAL ACUMULADO</div>
<div style="margin-top:12px;"><span class="xp-tier-badge" style="background:rgba(99,102,241,0.1);color:{_m_color};border:1px solid {_m_color}33;font-size:12px;padding:4px 12px;">{_m_emoji} {_m_tier}</span></div>
</div>
""", unsafe_allow_html=True)

    modulos = config.MODULOS
    all_mod_progress = database.load_all_module_progress(username)
    
    for titulo, arquivo, _url in modulos:
        cur_idx = all_mod_progress.get(arquivo, 0)
        banco_mod = carregar_banco_especifico(arquivo)
        if banco_mod:
            total_lições = len(banco_mod)
            pct = int((cur_idx / total_lições) * 100) if total_lições > 0 else 0
            _mod_emoji = config.MODULOS_EMOJI.get(titulo, '📚')
            
            st.markdown(f"""
<div class="mod-metric-card">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
<span style="font-weight:700; font-size:15px;">{_mod_emoji} {titulo}</span>
<span style="color:#06b6d4; font-weight:700; font-size:14px;">{pct}%</span>
</div>
<div class="mod-prog-track">
<div class="mod-prog-fill" style="width:{pct}%;"></div>
</div>
<div class="mod-status-row">
<span>{('✅ COMPLETO' if pct == 100 else '🔄 EM CURSO') if pct > 0 else '⏳ PENDENTE'}</span>
<span class="pct">{cur_idx}/{total_lições} lições</span>
</div>
</div>
""", unsafe_allow_html=True)

    if st.button("⬅ VOLTAR AO MENU"):
        st.session_state['pagina'] = 'inicio'
        st.rerun()

elif st.session_state['pagina'] == 'selecao_modulos':
    # DESIGN: Grid System Real
    modulos = config.MODULOS

    st.markdown(f"""
<div class="mod-sel-header">
<h2>🎯 Selecione um Módulo</h2>
<span class="mod-count">{len(modulos)} módulos disponíveis</span>
</div>
""", unsafe_allow_html=True)

    _sp1, _back_col = st.columns([5, 1])
    with _back_col:
         if st.button("🔙 MENU PRINCIPAL"):
            st.session_state['pagina'] = 'inicio'
            salvar_progresso()
            st.rerun()

    all_mod_progress = database.load_all_module_progress(username)

    # Grid Dinamico (3 Colunas para ficar mais largo e clean)
    for i in range(0, len(modulos), 3):
        cols = st.columns(3)
        batch = modulos[i:i+3]
        for idx, (titulo, arquivo, url_backup) in enumerate(batch):
            with cols[idx]:
                # Logica de Progresso
                banco_temp = carregar_banco_especifico(arquivo)
                mod_total = len(banco_temp) if banco_temp else 1
                mod_indice = all_mod_progress.get(arquivo, 0)
                mod_pct = min(int((mod_indice / mod_total) * 100), 100)
                
                # Assets: Icone SVG e Capa Local
                svg_icon = icons.get_svg(titulo)
                cover_b64 = get_cover_img_64(titulo)
                
                # Se nao tiver capa local (erro de download), usa um placeholder dark
                img_src = f"data:image/jpeg;base64,{cover_b64}" if cover_b64 else url_backup

                # Card Interativo (Premium 3D)
                _status_text = '✅ CONCLUÍDO' if mod_pct == 100 else ('🚀 EM ANDAMENTO' if mod_pct > 0 else '⏳ INICIAR')
                _status_class = 'concluido' if mod_pct == 100 else ('andamento' if mod_pct > 0 else 'pendente')
                
                st.markdown(f"""
<div class="module-card-wrap">
<div class="module-card-inner">
<div class="module-cover-wrap">
<img src="{img_src}" class="module-cover">
<div class="module-cover-overlay"></div>
<div class="module-version-tag">PRO v3.0</div>
</div>
<div class="module-info">
<div class="module-name">{svg_icon} {titulo}</div>
<div class="mod-progress-container">
<div class="mod-meta">
<span class="mod-status-tag {_status_class}">{_status_text}</span>
<span style="color:#06b6d4; font-weight:800;">{mod_pct}%</span>
</div>
<div class="mod-prog-bar">
<div class="mod-prog-fill" style="width:{mod_pct}%;"></div>
</div>
</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)
                
                # Botao de Acao (Invisible overlay simulated by st.button below card)
                if st.button(f"ACESSAR {titulo}", key=f"start_{arquivo}", use_container_width=True):
                    saved_indice = database.load_module_progress(username, arquivo)
                    st.session_state['arquivo_atual'] = arquivo
                    st.session_state['indice'] = saved_indice
                    st.session_state['porc_atual'] = 0
                    st.session_state['tentativa'] = 0
                    st.session_state['pagina'] = 'aula'
                    salvar_progresso()
                    st.rerun()


elif st.session_state['pagina'] == 'aula':
    banco = carregar_banco_especifico(st.session_state['arquivo_atual'])
    if not banco:
        st.error("Erro: Base de dados não encontrada.")
        if st.button("Voltar"):
            st.session_state['pagina'] = 'selecao_modulos'
            st.rerun()
        st.stop()

    atual = banco[st.session_state['indice'] % len(banco)]
    total = len(banco)
    
    current_idx_pos: int = int(st.session_state['indice'])
    pos = (current_idx_pos % len(banco)) + 1
    pct_progresso = int((pos / total) * 100)

    # Max indice = fronteira do progresso (a licao mais avancada ja alcancada)
    max_indice = database.load_module_progress(username, st.session_state['arquivo_atual'])

    # Topo da Aula — Header premium com Botão de Fechar
    c_head_title, c_head_close = st.columns([5, 1])
    with c_head_title:
        st.markdown(f"""
        <div class="lesson-header" style="margin-bottom:0;">
            <h3 style="margin:0;">{st.session_state['arquivo_atual'].replace('.csv','').upper()} <span class="lesson-count">Lição {pos} de {total}</span></h3>
        </div>
        """, unsafe_allow_html=True)
    with c_head_close:
        # Botão Vermelho/Laranja Chamativo
        if st.button("❌ SAIR", key="btn_close_lesson", help="Voltar aos Módulos"):
            st.session_state['pagina'] = 'selecao_modulos'
            salvar_progresso()
            st.rerun()

    st.markdown(f"""
<div class="prog-track" style="margin-top:10px;"><div class="prog-fill" style="width:{pct_progresso}%"></div></div>
""", unsafe_allow_html=True)
    c_tit, c_skip = st.columns([3, 1])
    with c_tit:
        pass
    with c_skip:
        if st.session_state['xp'] >= 50:
            st.markdown('<div class="skip-btn">', unsafe_allow_html=True)
            if st.button("💎 Pular (-50XP)"):
                st.session_state['xp'] = int(st.session_state['xp']) - 50
                st.session_state['indice'] = int(st.session_state['indice']) + 1
                st.session_state['porc_atual'] = 0
                st.session_state['tentativa'] = 0
                salvar_progresso()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.button("💎 Pular (50 XP)", disabled=True)

    # Layout Principal
    col_img, col_txt = st.columns([1, 1.5])
    
    with col_img:
        # LOGICA DE BADGES (SELOS)
        badge_html = ""
        user_score = st.session_state.get('porc_atual', 0)

        # Se estamos revisitando uma licao ja concluida, busca melhor nota do DB
        # Alterado: Busca sempre se score atual for 0 (mesmo na fronteira), para mostrar medalha se ja passamos
        if user_score == 0:
            saved_score = database.load_lesson_score(
                username, st.session_state['arquivo_atual'], int(st.session_state['indice'])
            )
            if saved_score > 0:
                user_score = saved_score
        
        # HTML minificado para evitar indentação que o Markdown interpreta como bloco de código
        # HTML minificado para evitar indentação que o Markdown interpreta como bloco de código
        # HTML minificado para evitar indentação que o Markdown interpreta como bloco de código
        # Badge "Carimbo" (Stamp Style) — Emoji Gigante + Texto do Score
        # Container com rotação -10deg para efeito dinâmico
        # Helper para gerar SVG do Carimbo
        def get_stamp_svg(score, color, label="COMPLETED"):
            rotation = -10
            # IMPORTANTE: HTML não deve ter indentação para não quebrar o Markdown do Streamlit
            return f'''
            <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%) rotate(-5deg); z-index:10; width:180px; height:180px; background:radial-gradient(circle, #fff 60%, #f0f0f0 100%); border-radius:50%; border:8px solid {color}; box-shadow: 0 10px 25px rgba(0,0,0,0.5); display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; font-family:'Arial', sans-serif;">
                <div style="font-size:14px; color:#555; letter-spacing:1px; font-weight:bold; margin-bottom:5px;">ENGLISH PRO</div>
                <div style="font-size:60px; font-weight:900; color:{color}; line-height:1; text-shadow:1px 1px 0px rgba(0,0,0,0.1);">{score}%</div>
                <div style="font-size:16px; font-weight:bold; color:{color}; margin-top:5px; text-transform:uppercase;">{label}</div>
                <div style="margin-top:5px; font-size:20px;">⭐⭐⭐</div>
            </div>
            '''

        if user_score == 100:
            badge_html = get_stamp_svg(100, "#FFD700", "EXCELLENT") # Gold
        elif user_score >= 80:
            badge_html = get_stamp_svg(user_score, "#C0C0C0", "GREAT JOB") # Silver
        elif user_score >= 50:
            badge_html = get_stamp_svg(user_score, "#CD7F32", "COMPLETED") # Bronze

        img64 = get_img_64(config.IMAGES_DIR, f"{atual['id']}.jpg")
        
        # Renderiza imagem com wrapper para posicionamento relativo do badge
        img_src = ""
        if img64:
            img_src = f"data:image/jpeg;base64,{img64}"
        elif 'img' in atual and atual['img']:
            img_src = atual['img']
            
        if img_src:
            st.markdown(f"""<div class="img-premium-wrap" style="position:relative; padding:0; line-height:0;">{badge_html}<img src="{img_src}" style="width:100%; display:block; border-radius:12px;"></div>""", unsafe_allow_html=True)
        else:
            # DEBUG: Se nao achou imagem, mostra warning com info
            st.warning(f"Imagem não encontrada. ID: {atual.get('id')} | URL: {atual.get('img')}")
            # Tenta mostrar o que tem no 'img' cru, caso seja util
            if atual.get('img'):
                st.write(f"Source URL: {atual.get('img')}")

    with col_txt:
        # Box da Frase — Centered & Premium (Com Bandeiras e Texto Maior)
        # CSS para Bandeiras e Estilo Premium
        st.markdown("""
        <style>
            .flag-icon {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                object-fit: cover;
                vertical-align: middle;
                margin-right: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                border: 2px solid rgba(255,255,255,0.1);
            }
            .phrase-pt {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-style: italic;
            }
            .phrase-en {
                font-family: 'Montserrat', sans-serif;
                text-shadow: 0 0 15px rgba(255,255,255,0.3);
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
<div class="phrase-box" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding: 25px 15px; background: linear-gradient(180deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); border-radius: 20px; margin-bottom:20px; border: 1px solid rgba(255,255,255,0.05);">
    <div class="phrase-pt" style="text-align:center; width:100%; font-size: 22px; color: #c0c0c0; margin-bottom: 12px; font-weight:500;">
        <img src="https://flagcdn.com/w40/br.png" class="flag-icon" alt="BR">
        {atual['pt']}
    </div>
    <div class="phrase-en" style="text-align:center; width:100%; font-size: 40px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; line-height: 1.2;">
        <img src="https://flagcdn.com/w40/us.png" class="flag-icon" alt="US">
        {atual['en']}
    </div>
</div>
""", unsafe_allow_html=True)

        # Audio Playback
        modulo = os.path.splitext(st.session_state['arquivo_atual'])[0]
        path_ref = os.path.join(config.AUDIOS_DIR, f"{modulo}_{atual['id']}.mp3")
        if not os.path.exists(path_ref):
            gTTS(text=str(atual['en']), lang='en').save(path_ref)
        st.audio(path_ref)

        # Gravador e Botão de Repetir - Layout Toolbar Profissional
        # CSS para alinhar verticalmente o botão do Streamlit com o componente mic_recorder
        st.markdown("""
            <style>
                div[data-testid="column"] {
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }
                /* Tenta esconder o link de download do componente se possível */
                iframe[title="streamlit_mic_recorder.mic_recorder"] {
                    margin-bottom: 0px !important;
                }
            </style>
        """, unsafe_allow_html=True)

        c_mic, c_rep = st.columns([3, 1], gap="small")
        with c_mic:
            gravacao = mic_recorder(
                start_prompt="🔴 GRAVAR",
                stop_prompt="⏹️ PARAR",
                format="wav",
                key=f"mic_{st.session_state['indice']}_{st.session_state['tentativa']}"
            )
        with c_rep:
            # Botão de Repetir (Texto + Icone) - Visual de Toolbar
            if st.button("🔄 REPETIR", key="btn_retry_top", help="Reiniciar tentativa", use_container_width=True):
                st.session_state['porc_atual'] = 0
                st.session_state['tentativa'] = 0
                st.rerun()

        if gravacao:
            audio_data = io.BytesIO(gravacao['bytes'])
            with wave.open(audio_data, 'rb') as wf:
                rec = KaldiRecognizer(model_vosk, wf.getframerate())
                rec.AcceptWaveform(wf.readframes(wf.getnframes()))
                ouvida = json.loads(rec.FinalResult()).get("text", "").lower()

            # Caixa mostrando o que o sistema ouviu
            _ouvi_display = ouvida.upper() if ouvida.strip() else "(silêncio detectado)"
            st.markdown(f"""
<div class="ouvi-box">
    <div class="ouvi-label">🎤 O SISTEMA ENTENDEU:</div>
    <div class="ouvi-text">{_ouvi_display}</div>
</div>
""", unsafe_allow_html=True)

            alvo = limpar(atual['en']).split()
            dito = limpar(ouvida).split()

            # Renderiza HTML do feedback com animação staggered
            fb_html = '<div class="fb-container">'
            acertos_list = []
            for idx, p in enumerate(alvo):
                if idx < len(dito) and dito[idx] == p:
                    fb_html += f'<span class="fb-word fb-correct">{p.upper()}</span>'
                    acertos_list.append(p)
                else:
                    fb_html += f'<span class="fb-word fb-wrong">{p.upper()}</span>'
            fb_html += '</div>'
            acertos = len(acertos_list)
            st.markdown(fb_html, unsafe_allow_html=True)

            # Logica de XP e Sons
            if acertos > 0:
                current_xp: int = int(st.session_state['xp'])
                st.session_state['xp'] = int(current_xp + acertos)
                st.toast(f"+{acertos} XP", icon="⭐")

            val_total = int(len(alvo))
            st.session_state['porc_atual'] = int((acertos / val_total) * 100) if val_total > 0 else 0
            
            # SHOW RESULT (Premium animated — sem som, sem balloons)
            _pct_class = "success" if st.session_state['porc_atual'] >= 80 else "fail"
            st.markdown(f"""
<div class="result-pct {_pct_class}" style="text-align:center;">
    {st.session_state['porc_atual']}%
</div>
""", unsafe_allow_html=True)
            salvar_progresso()

            # Salva score da licao no DB (persiste para badges)
            database.save_lesson_score(
                username, st.session_state['arquivo_atual'],
                int(st.session_state['indice']),
                st.session_state['porc_atual']
            )

            # --- AUTO-NEXT FLOW (Dinâmica Melhorada) ---
            if st.session_state['porc_atual'] == 100:
                st.markdown("<br>", unsafe_allow_html=True)
                st.success("🎉 Perfeito! Avançando automaticamente...")
                time.sleep(2)
                st.session_state['indice'] = int(st.session_state['indice']) + 1
                st.session_state['porc_atual'] = 0
                st.session_state['tentativa'] = 0
                salvar_progresso()
                st.rerun()


    st.markdown('<div class="divider-glow"></div>', unsafe_allow_html=True)
    
    # Botões de Navegação Inferior — Focados na Aula (Linear)
    # Botões de Navegação Inferior — Focados na Aula (Linear)
    # [ Anterior ] [ Próxima ]
    st.markdown("<br>", unsafe_allow_html=True)
    _nav1, _nav3 = st.columns([1, 1])
    
    # Determina se estamos revisitando licoes ja concluidas
    is_reviewing = int(st.session_state['indice']) < max_indice
        
    # 1. ANTERIOR
    with _nav1:
        if st.session_state['indice'] > 0:
            if st.button("⬅ ANTERIOR", use_container_width=True):
                st.session_state['indice'] = int(st.session_state['indice']) - 1
                st.session_state['porc_atual'] = 0
                st.session_state['tentativa'] = 0
                st.rerun()

    # 3. PROXIMA
    with _nav3:
        # Verifica se tem score salvo suficiente para habilitar (caso max_indice tenha corrompido ou edge case)
        # Proteção contra falha de leitura do DB
        try:
             _saved_best = database.load_lesson_score(username, st.session_state['arquivo_atual'], int(st.session_state['indice']))
        except:
             _saved_best = 0
        
        can_go_next = False
        if is_reviewing:
            can_go_next = True
        elif st.session_state['porc_atual'] >= 80:
            can_go_next = True
        elif _saved_best >= 80:
            can_go_next = True
        elif god_mode:
            can_go_next = True

        if can_go_next:
            if st.button("PRÓXIMA ➡", use_container_width=True):
                st.session_state['indice'] = int(st.session_state['indice']) + 1
                st.session_state['porc_atual'] = 0
                st.session_state['tentativa'] = 0
                salvar_progresso()
                st.rerun()
        else:
            st.button("🔒 Bloqueado", disabled=True, use_container_width=True)



# -- FIM DO APP --

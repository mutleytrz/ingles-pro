from __future__ import annotations
# config.py — Configuracao centralizada de caminhos e variaveis

import os
import json
from typing import Any

_CONFIG_FILE: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def _load_config_file() -> dict[str, Any]:
    """Carrega config.json se existir."""
    if os.path.exists(_CONFIG_FILE):
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


_file_cfg: dict[str, Any] = _load_config_file()


def _get_streamlit_secret(key: str):
    """Tenta ler de st.secrets (Streamlit Cloud)."""
    try:
        import streamlit as st
        return st.secrets.get(key, None)
    except Exception:
        return None


def _get(key: str, default: str = "") -> str:
    """Prioridade: variavel de ambiente > st.secrets > config.json > default."""
    # 1. Variavel de ambiente
    env_val = os.environ.get(key)
    if env_val is not None:
        return env_val
    # 2. Streamlit Cloud secrets
    secret_val = _get_streamlit_secret(key)
    if secret_val is not None:
        return str(secret_val)
    # 3. config.json
    return _file_cfg.get(key, default)


# -- Diretorio raiz dos dados (pode ser /mnt/dados na VPS) --
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
DATA_DIR: str = _get("DATA_DIR", BASE_DIR)

# Resolve caminhos relativos a partir do BASE_DIR
if not os.path.isabs(DATA_DIR):
    DATA_DIR = os.path.join(BASE_DIR, DATA_DIR)
DATA_DIR = os.path.normpath(DATA_DIR)

# -- Caminhos dos arquivos pesados --
_model_raw: str = _get("MODEL_DIR", os.path.join(DATA_DIR, "model"))
_images_raw: str = _get("IMAGES_DIR", os.path.join(DATA_DIR, "imagens"))
_audios_raw: str = _get("AUDIOS_DIR", os.path.join(DATA_DIR, "audios_local"))
_assets_raw: str = _get("ASSETS_DIR", os.path.join(DATA_DIR, "assets"))

MODEL_DIR: str = os.path.normpath(_model_raw if os.path.isabs(_model_raw) else os.path.join(BASE_DIR, _model_raw))
IMAGES_DIR: str = os.path.normpath(_images_raw if os.path.isabs(_images_raw) else os.path.join(BASE_DIR, _images_raw))
AUDIOS_DIR: str = os.path.normpath(_audios_raw if os.path.isabs(_audios_raw) else os.path.join(BASE_DIR, _audios_raw))
ASSETS_DIR: str = os.path.normpath(_assets_raw if os.path.isabs(_assets_raw) else os.path.join(BASE_DIR, _assets_raw))

# -- Banco de Dados --
_db_raw: str = _get("DB_PATH", os.path.join(DATA_DIR, "ingles_pro.db"))
DB_PATH: str = os.path.normpath(_db_raw if os.path.isabs(_db_raw) else os.path.join(BASE_DIR, _db_raw))

# -- Turso (Banco de Dados Externo) --
TURSO_DB_URL: str = _get("TURSO_DB_URL", "")
TURSO_AUTH_TOKEN: str = _get("TURSO_AUTH_TOKEN", "")

# -- Seguranca --
SECRET_KEY: str = _get("SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")

# -- Email (SMTP) --
SMTP_HOST: str = _get("SMTP_HOST", "")
SMTP_PORT: int = int(_get("SMTP_PORT", "587"))
SMTP_USER: str = _get("SMTP_USER", "")
SMTP_PASS: str = _get("SMTP_PASS", "")
SMTP_FROM_NAME: str = _get("SMTP_FROM_NAME", "English Pro")

# -- Modulos de aulas (CSV) --
CSV_DIR: str = DATA_DIR

MODULOS: list[tuple[str, str, str]] = [
    ("ESCOLA",         "escola.csv",         "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=400"),
    ("AEROPORTO",      "aeroporto.csv",      "https://images.unsplash.com/photo-1569154941061-e231b4725ef1?w=400"),
    ("HOTEL",          "hotel.csv",           "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400"),
    ("PALAVRAS",       "palavras.csv",        "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=400"),
    ("TRABALHO",       "trabalho.csv",        "https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=400"),
    ("COMPRAS",        "compras.csv",         "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400"),
    ("SAUDE",          "saude.csv",           "https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?w=400"),
    ("CASUAL",         "casual.csv",          "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=400"),
    ("TRANSPORTE",     "transporte.csv",      "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=400"),
    ("TECNOLOGIA",     "tecnologia.csv",      "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400"),
    ("COTIDIANO",      "cotidiano.csv",       "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=400"),
    ("LAZER",          "lazer.csv",           "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?w=400"),
    ("RELACIONAMENTO", "relacionamento.csv",  "https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=400"),
]

MODULOS_EMOJI: dict[str, str] = {
    "ESCOLA": "🏫", "AEROPORTO": "✈️", "HOTEL": "🏨", "PALAVRAS": "📂",
    "TRABALHO": "💼", "COMPRAS": "🛒", "SAUDE": "🍎", "CASUAL": "☕",
    "TRANSPORTE": "🚌", "TECNOLOGIA": "📱", "COTIDIANO": "🏠",
    "LAZER": "🎮", "RELACIONAMENTO": "❤️",
}

# -- Garante que as pastas existem --
for _d in [MODEL_DIR, IMAGES_DIR, AUDIOS_DIR, ASSETS_DIR]:
    os.makedirs(_d, exist_ok=True)

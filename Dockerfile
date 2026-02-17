# ── Dockerfile — Inglês Local Pro (Multi-Usuário) ──
FROM python:3.11-slim

# Dependências de sistema para áudio e compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependências Python primeiro (cache de camada Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código-fonte e CSVs
COPY *.py .
COPY *.csv .
COPY config.json .
COPY init_db.sql .

# Pastas que serão montadas como volumes na VPS
# (criadas aqui como fallback caso não sejam montadas)
RUN mkdir -p /app/model /app/imagens /app/audios_local /app/assets /app/data

# Variáveis de ambiente padrão para VPS
ENV DATA_DIR=/app
ENV MODEL_DIR=/app/model
ENV IMAGES_DIR=/app/imagens
ENV AUDIOS_DIR=/app/audios_local
ENV ASSETS_DIR=/app/assets
ENV DB_PATH=/app/data/ingles_pro.db

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app_core.py", \
    "--server.headless=true", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--browser.gatherUsageStats=false"]

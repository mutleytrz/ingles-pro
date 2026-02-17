import os
import csv
import requests
import shutil
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "imagens")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
COVERS_DIR = os.path.join(ASSETS_DIR, "covers")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)

# Cache: URL -> Caminho do primeiro arquivo baixado com sucesso
url_cache = {}

def download_image(url, save_path):
    filename = os.path.basename(save_path)
    
    # 1. Se arquivo já existe, pula
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        # print(f"[SKIP] Já existe: {filename}")
        return True

    # 2. Se URL já foi baixada, copia do cache
    if url in url_cache and os.path.exists(url_cache[url]):
        src = url_cache[url]
        try:
            shutil.copy2(src, save_path)
            print(f"[COPY] {os.path.basename(src)} -> {filename}")
            return True
        except Exception as e:
            print(f"[ERR] Erro ao copiar cache: {e}")

    # 3. Baixa da URL
    try:
        if not url.startswith("http"):
            return False

        print(f"[DOWN] Baixando: {url} -> {filename}")
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            
            # Atualiza cache
            url_cache[url] = save_path
            time.sleep(0.5) # Evita rate limit
            return True
        else:
            print(f"[ERR] HTTP {response.status_code} para {url}")
    except Exception as e:
        print(f"[ERR] Falha ao baixar {url}: {e}")
    
    return False

def process_modules():
    try:
        import config
        modulos = config.MODULOS
    except ImportError:
        print("[ERR] config.py não encontrado.")
        return

    # Capas
    print("\n--- Capas ---")
    cover_paths = {} # nome_modulo -> caminho_capa
    for nome, _, url_capa in modulos:
        safe_name = nome.lower().replace(" ", "_") + ".jpg"
        save_path = os.path.join(COVERS_DIR, safe_name)
        if download_image(url_capa, save_path):
            cover_paths[nome] = save_path

    # Lições
    print("\n--- Lições ---")
    for nome, arquivo_csv, _ in modulos:
        csv_path = os.path.join(BASE_DIR, arquivo_csv)
        if not os.path.exists(csv_path):
            continue
        
        print(f"Processando {arquivo_csv}...")
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except:
            continue

        # Capa de fallback para este módulo
        fallback_cover = cover_paths.get(nome)
        
        for row in rows:
            img_id = row.get("id")
            img_url = row.get("img", "").strip()
            
            if not img_id: continue

            save_path = os.path.join(IMAGES_DIR, f"{img_id}.jpg")
            
            success = False
            # Tenta URL do CSV
            if img_url and img_url.startswith("http"):
                success = download_image(img_url, save_path)
            
            # Se falhar e tiver capa, usa capa como fallback (cópia)
            if not success and not os.path.exists(save_path) and fallback_cover:
                print(f"[FALLBACK] {os.path.basename(fallback_cover)} -> {img_id}.jpg")
                shutil.copy2(fallback_cover, save_path)

if __name__ == "__main__":
    process_modules()

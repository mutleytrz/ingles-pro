"""
download_sounds.py — Baixa sons ambientes (Creative Commons) do Wikimedia Commons
para uso offline no modo Neural Sleep.
Usa a API do Wikimedia para resolver URLs reais dos arquivos.
"""
import os
import requests
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "assets", "sounds")
os.makedirs(SOUNDS_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "EnglishProApp/1.0 (Educational; contact@englishpro.app)"
}

# Catálogo: (nome_local, titulo_no_wikimedia_commons)
# Formato: "File:NomeDoArquivo.ogg" exatamente como no Wikimedia Commons
SOUNDS = [
    ("rain_gentle.ogg",   "File:Sound of rain.ogg"),
    ("rain_window.ogg",   "File:Rain against the window.ogg"),
    ("rain_thunder.ogg",  "File:Rain thunder and birds.ogg"),
    ("rain_forest.ogg",   "File:Walk in the rainforest.ogg"),
    ("rain_storm.ogg",    "File:Summer thunderstorm in the woods.ogg"),
    ("stream_forest.ogg", "File:Water stream.ogg"),
    ("white_noise.ogg",   "File:White noise sound.ogg"),
]


def resolve_wikimedia_url(file_title: str) -> str:
    """Usa a API do Wikimedia Commons para obter a URL real de download."""
    api_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": file_title,
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
    }
    try:
        resp = requests.get(api_url, params=params, headers=HEADERS, timeout=15)
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id == "-1":
                return ""
            info = page_data.get("imageinfo", [{}])
            if info:
                return info[0].get("url", "")
    except Exception as e:
        print(f"    [API ERR] {e}")
    return ""


def download_all():
    print(f"📂 Destino: {SOUNDS_DIR}")
    print(f"🎵 Sons para baixar: {len(SOUNDS)}\n")

    for filename, wiki_title in SOUNDS:
        save_path = os.path.join(SOUNDS_DIR, filename)

        # Pula se já existe e tem conteúdo
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            size_kb = os.path.getsize(save_path) / 1024
            print(f"  [SKIP] {filename} ({size_kb:.0f} KB)")
            continue

        # Resolve URL real via API
        print(f"  [RESOLVING] {wiki_title} ...")
        url = resolve_wikimedia_url(wiki_title)
        if not url:
            print(f"         ❌ Não encontrado no Wikimedia")
            continue

        print(f"  [DOWN] {filename} <- {url[:80]}...")
        try:
            resp = requests.get(url, timeout=60, stream=True, headers=HEADERS)
            if resp.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                size_kb = os.path.getsize(save_path) / 1024
                print(f"         ✅ OK ({size_kb:.0f} KB)")
            else:
                print(f"         ❌ HTTP {resp.status_code}")
        except Exception as e:
            print(f"         ❌ Erro: {e}")

        time.sleep(0.5)

    print("\n🏁 Concluído!")

    ok = 0
    for filename, _ in SOUNDS:
        p = os.path.join(SOUNDS_DIR, filename)
        if os.path.exists(p) and os.path.getsize(p) > 0:
            ok += 1
    print(f"   {ok}/{len(SOUNDS)} sons prontos para uso offline.\n")


if __name__ == "__main__":
    download_all()

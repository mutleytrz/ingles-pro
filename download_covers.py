import os
import requests
import config

def download_covers():
    save_dir = os.path.join(config.DATA_DIR, "assets", "covers")
    os.makedirs(save_dir, exist_ok=True)
    
    print(f"Downloading covers to {save_dir}...")
    
    for nome, arquivo_csv, url in config.MODULOS:
        filename = f"{nome.lower()}.jpg"
        filepath = os.path.join(save_dir, filename)
        
        if os.path.exists(filepath):
            print(f"Skipping {nome} (already exists)")
            continue
            
        print(f"Downloading {nome} from {url}...")
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(r.content)
            else:
                print(f"Failed to download {nome}: Status {r.status_code}")
        except Exception as e:
            print(f"Error downloading {nome}: {e}")

if __name__ == "__main__":
    download_covers()

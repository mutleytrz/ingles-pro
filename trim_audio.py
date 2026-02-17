import os
import time

# Configuração
folder = r"d:\games\projeto\sons_relax"
LIMIT_MB = 15
limit_bytes = LIMIT_MB * 1024 * 1024 

print(f"🔪 Iniciando corte de áudios (Limite: {LIMIT_MB}MB)...")

try:
    for filename in os.listdir(folder):
        if filename.lower().endswith(".mp3"):
            filepath = os.path.join(folder, filename)
            
            # Pula arquivos que ja sao pequenos
            if os.path.getsize(filepath) <= limit_bytes:
                print(f"⏩ {filename} já é pequeno ({os.path.getsize(filepath)/1024/1024:.2f}MB). Pulando.")
                continue

            # Se for arquivo grande
            print(f"✂️ Cortando {filename} ({os.path.getsize(filepath)/1024/1024:.2f}MB)...")
            
            try:
                # Le os primeiros X bytes
                with open(filepath, 'rb') as f_in:
                    data = f_in.read(limit_bytes)
                
                # Salva em arquivo temporario
                temp_path = os.path.join(folder, f"temp_{filename}")
                with open(temp_path, 'wb') as f_out:
                    f_out.write(data)
                    
                # Substitui original (Windows precisa remover antes as vezes, mas replace resolve)
                # Vamos garantir
                os.remove(filepath)
                os.rename(temp_path, filepath)
                
                print(f"✅ {filename} atualizado para {LIMIT_MB}MB!")
                
            except Exception as e:
                print(f"❌ Erro ao processar {filename}: {e}")

    print("🏁 Concluído!")

except Exception as e:
    print(f"❌ Erro geral: {e}")

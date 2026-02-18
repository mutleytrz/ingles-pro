import config
import os
import time
from libsql_client import create_client_sync
import database

# Load secrets
def load_secrets():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        import tomllib
        with open(secrets_path, "rb") as f:
            data = tomllib.load(f)
            config.TURSO_DB_URL = data.get("TURSO_DB_URL", "")
            config.TURSO_AUTH_TOKEN = data.get("TURSO_AUTH_TOKEN", "")

load_secrets()

def benchmark():
    # 1. Custom Client (Regional)
    url_reg = config.TURSO_DB_URL
    print(f"Bencmarking Custom Client (Regional): {url_reg}")
    conn = database._get_conn()
    conn.execute("SELECT 1")
    start = time.time()
    for _ in range(5): conn.execute("SELECT 1")
    print(f"  Avg: {(time.time()-start)/5:.3f}s")
    
    # 2. Libsql-client (Regional) - SHOULD FAIL if the KeyError exists
    print(f"\nBenchmarking Libsql-client (Regional): {url_reg}")
    try:
        # We need to manually use https because libsql:// fails with WSS error
        url_https = url_reg.replace("libsql://", "https://")
        libsql_conn = create_client_sync(url_https, auth_token=config.TURSO_AUTH_TOKEN)
        libsql_conn.execute("SELECT 1")
        start = time.time()
        for _ in range(5): libsql_conn.execute("SELECT 1")
        print(f"  Avg: {(time.time()-start)/5:.3f}s")
        libsql_conn.close()
    except Exception as e:
        print(f"  Libsql-client failed: {e}")

    # 3. Libsql-client (Global)
    url_glob = "https://ingles-pro-db-mutleytrz.turso.io"
    print(f"\nBenchmarking Libsql-client (Global): {url_glob}")
    try:
        libsql_conn = create_client_sync(url_glob, auth_token=config.TURSO_AUTH_TOKEN)
        libsql_conn.execute("SELECT 1")
        start = time.time()
        for _ in range(5): libsql_conn.execute("SELECT 1")
        print(f"  Avg: {(time.time()-start)/5:.3f}s")
        libsql_conn.close()
    except Exception as e:
        print(f"  Libsql-client Global failed: {e}")

if __name__ == "__main__":
    benchmark()

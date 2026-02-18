import config
import os
from libsql_client import create_client_sync
import time

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

def test_libsql_proto():
    url = config.TURSO_DB_URL # Should be libsql://...
    print(f"Testing libsql-client with URL: {url}")
    
    try:
        client = create_client_sync(url, auth_token=config.TURSO_AUTH_TOKEN)
        print("Client created successfully.")
        
        start = time.time()
        rs = client.execute("SELECT 1")
        print(f"Query 1 took: {time.time() - start:.3f}s")
        
        start = time.time()
        rs = client.execute("SELECT 1")
        print(f"Query 2 took: {time.time() - start:.3f}s")
        
        client.close()
        print("Success!")
    except Exception as e:
        print(f"Failed with protocol: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_libsql_proto()

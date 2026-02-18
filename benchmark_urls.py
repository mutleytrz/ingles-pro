import requests
import time
import os

# Regional URL (Tokyo)
REGIONAL_URL = "https://ingles-pro-db-mutleytrz.aws-ap-northeast-1.turso.io/v1/execute"
# Sao Paulo URL (Hypothesized)
SA_URL = "https://ingles-pro-db-mutleytrz.aws-sa-east-1.turso.io/v1/execute"
# Global URL
GLOBAL_URL = "https://ingles-pro-db-mutleytrz.turso.io/v1/execute"

TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzEzNDQ1NTUsImlkIjoiYWVlOGUyYjktMDNkNi00OGYzLTg4ODctNTk5YjYwY2JkZjRkIiwicmlkIjoiMzY5YTZmYWUtMmJiMS00MDRiLTliMzMtZWMyNzhkMDYyZjdlIn0.No6m_6mCa734-2vKFt7AHlLP-T311cKVb-rimSfiMIPbx88mNTp8tY4WoGuUAQJcB9Ly4iYmkjFm_IWNTJ9dCw"

headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
payload = {"stmt": {"sql": "SELECT 1"}}

def test_url(name, url):
    print(f"Testing {name}: {url}")
    session = requests.Session()
    # Warmup
    try:
        session.post(url, json=payload, headers=headers, timeout=5)
    except:
        print(f"  {name} failed warmup")
        return None
    
    times = []
    for i in range(3):
        start = time.time()
        session.post(url, json=payload, headers=headers, timeout=5)
        times.append(time.time() - start)
    
    avg = sum(times) / len(times)
    print(f"  Avg time: {avg:.3f}s")
    return avg

reg_time = test_url("Regional (Tokyo)", REGIONAL_URL)
sa_time = test_url("Sao Paulo", SA_URL)
glob_time = test_url("Global", GLOBAL_URL)

if reg_time and sa_time:
    if sa_time < reg_time:
        print(f"\nSUCCESS: Sao Paulo URL is {reg_time/sa_time:.1f}x faster!")
    else:
        print("\nSao Paulo URL is NOT faster.")

if reg_time and glob_time:
    if glob_time < reg_time:
        print(f"Global URL is {reg_time/glob_time:.1f}x faster!")

import urllib.request
import urllib.error
import time
import random
import os

# Allow overriding URL via env var for Docker usage
URL = os.getenv("TARGET_URL", "http://localhost:8080")
SCENARIOS = ['normal', 'latency', 'error', 'saturation']
WEIGHTS = [0.7, 0.1, 0.1, 0.1]

def generate_traffic(count=20):
    print(f"Generating {count} requests to {URL}...")
    
    for i in range(count):
        scenario = random.choices(SCENARIOS, weights=WEIGHTS, k=1)[0]
        print(f"[{i+1}/{count}] Scenario: {scenario}", end="... ", flush=True)
        
        try:
            start = time.time()
            full_url = f"{URL}?scenario={scenario}"
            
            try:
                with urllib.request.urlopen(full_url) as response:
                    status_code = response.getcode()
            except urllib.error.HTTPError as e:
                status_code = e.code
            except Exception as e:
                status_code = "ERR"
                raise e

            duration = (time.time() - start) * 1000
            print(f"Status: {status_code}, Duration: {duration:.0f}ms")
            
        except Exception as e:
            print(f"Request failed: {e}")
            
        time.sleep(random.uniform(0.1, 0.5))

if __name__ == "__main__":
    count = int(os.getenv("REQUEST_COUNT", "50"))
    generate_traffic(count)

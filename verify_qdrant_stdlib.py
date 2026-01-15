import urllib.request
import json
import time
import sys

def verify():
    print("Connecting to Qdrant API...")
    base_url = "http://localhost:6333"
    collection_name = "telemetry_traces"
    
    # Check count
    for i in range(10):
        try:
            req = urllib.request.Request(f"{base_url}/collections/{collection_name}/points/count", method="POST")
            req.add_header('Content-Type', 'application/json')
            data = json.dumps({"exact": True}).encode('utf-8')
            with urllib.request.urlopen(req, data=data) as response:
                res_body = response.read()
                res_json = json.loads(res_body)
                count = res_json['result']['count']
                if count > 0:
                    print(f"Found {count} points!")
                    break
        except Exception as e:
            print(f"Waiting... ({e})")
        time.sleep(2)
    else:
        print("No data found after 20 seconds.")
        sys.exit(1)

    # Scroll points
    req = urllib.request.Request(f"{base_url}/collections/{collection_name}/points/scroll", method="POST")
    req.add_header('Content-Type', 'application/json')
    data = json.dumps({
        "limit": 10,
        "with_payload": True,
        "with_vector": False
    }).encode('utf-8')
    
    found_app_metadata = False
    with urllib.request.urlopen(req, data=data) as response:
        res_json = json.loads(response.read())
        points = res_json['result']['points']
        
        for point in points:
            payload = point['payload']
            metadata = payload.get("metadata", {})
            print(f"Point ID: {point['id']}")
            print(f"Metadata: {metadata}")
            
            if metadata.get("application") == "php-demo-app":
                found_app_metadata = True

    if found_app_metadata:
        print("\nSUCCESS: Found telemetry with 'application=php-demo-app' metadata!")
    else:
        print("\nFAILURE: Did not find 'application=php-demo-app' metadata.")
        sys.exit(1)

if __name__ == "__main__":
    verify()

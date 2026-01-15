from qdrant_client import QdrantClient
import time
import sys

def verify():
    print("Connecting to Qdrant...")
    client = QdrantClient(host="localhost", port=6333)
    
    collection_name = "telemetry_traces"
    
    # Wait for data to arrive (async processing)
    print("Waiting for data to be indexed...")
    for i in range(10):
        try:
            count_result = client.count(collection_name)
            if count_result.count > 0:
                print(f"Found {count_result.count} points!")
                break
        except Exception as e:
            print(f"Error querying Qdrant: {e}")
        time.sleep(2)
    else:
        print("No data found after 20 seconds.")
        sys.exit(1)

    # Scroll points to check metadata
    points, _ = client.scroll(
        collection_name=collection_name,
        limit=10,
        with_payload=True,
        with_vectors=False
    )

    found_app_metadata = False
    for point in points:
        payload = point.payload
        metadata = payload.get("metadata", {})
        print(f"Point ID: {point.id}")
        print(f"Text: {payload.get('text')}")
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

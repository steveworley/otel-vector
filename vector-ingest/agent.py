import os
import google.generativeai as genai
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import sys

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = "telemetry_traces"
MODEL_NAME = "all-MiniLM-L6-v2"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    sys.exit(1)

# Initialize clients
print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

print(f"Loading embedding model {MODEL_NAME}...")
embedding_model = SentenceTransformer(MODEL_NAME)

print("Configuring Gemini...")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-pro-preview')

def get_rag_response(query_text):
    print(f"\nAnalyzing query: '{query_text}'")
    
    # 1. Embed query
    query_vector = embedding_model.encode(query_text).tolist()
    
    # 2. Search Qdrant
    search_results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=15
    ).points
    
    if not search_results:
        print("No relevant traces found.")
        return

    # 3. Construct Context
    context_lines = []
    for hit in search_results:
        payload = hit.payload
        # Add metadata and text content
        meta = payload.get('metadata', {})
        text = payload.get('text', 'N/A')
        timestamp = payload.get('timestamp', 0)
        
        # Format a log line representation
        line = f"- [Score: {hit.score:.2f}] {text} | Metadata: {meta}"
        context_lines.append(line)
        
    context_str = "\n".join(context_lines)
    
    # 4. Prompt Gemini
    prompt = f"""
    You are a Site Reliability Engineer (SRE) Agent. 
    Your goal is to investigate incidents based on the following telemetry traces retrieved from our observability system.
    
    The user is asking: "{query_text}"
    
    Here are the most relevant traces and logs found in the vector database:
    ---
    {context_str}
    ---
    
    Based ONLY on these traces, analyze the root cause. 
    - Identify if there are errors, high latency, or saturation.
    - specific service names or operations involved.
    - Suggest potential fixes only if the evidence supports it.
    - If you don't see evidence of the problem in the traces, say so.
    
    Response:
    """
    
    print("Querying Gemini with retrieved context...")
    response = model.generate_content(prompt)
    
    print("\n" + "="*50)
    print("🤖 SRE AGENT ANALYSIS")
    print("="*50)
    print(response.text)
    print("="*50)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py <query>")
        print("Example: python agent.py 'Why show latency?'")
        sys.exit(1)
        
    query = sys.argv[1]
    get_rag_response(query)

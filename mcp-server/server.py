from mcp.server.fastmcp import FastMCP
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import os

# Configuration
# Default to localhost for local agent usage, but allow override for docker
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = "telemetry_traces"
MODEL_NAME = "all-MiniLM-L6-v2"

# Initialize
mcp = FastMCP("Observability Agent")
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embedding_model = SentenceTransformer(MODEL_NAME)

import jwt
from qdrant_client.http import models

JWT_SECRET = os.getenv("JWT_SECRET", "secret")  # In production, use env var

def validate_token(token: str) -> str:
    """Decodes JWT and returns the org.service.id."""
    try:
        # For POC, we skip verification or use a simple secret
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded.get("org.service.id")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid JWT token")

@mcp.tool()
def search_traces(query: str, token: str, limit: int = 5) -> str:
    """
    Search for traces scoped to your organization.
    
    Args:
        query: Natural language query string.
        token: JWT authorization token.
        limit: Number of results to return.
    """
    try:
        org_id = validate_token(token)
    except ValueError as e:
        return f"Authorization Error: {e}"

    query_vector = embedding_model.encode(query).tolist()
    
    # Filter by org.service.id
    org_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.org.service.id",
                match=models.MatchValue(value=org_id)
            )
        ]
    )
    
    search_results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=org_filter,
        limit=limit
    ).points

    if not search_results:
        return "No traces found matching your query."
    
    results = []
    for hit in search_results:
        payload = hit.payload
        text = payload.get('text', 'N/A')
        meta = payload.get('metadata', {})
        score = hit.score
        
        results.append(f"Trace (Score: {score:.2f}):\nContent: {text}\nMetadata: {meta}\n---")
        
    return "\n".join(results)

@mcp.tool()
def get_trace_details(trace_id: str, token: str) -> str:
    """
    Retrieve full details for a specific trace ID, scoped to your org.
    """
    try:
        org_id = validate_token(token)
    except ValueError as e:
        return f"Authorization Error: {e}"
    
    results = qdrant.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.trace_id",
                    match=models.MatchValue(value=trace_id)
                ),
                models.FieldCondition(
                    key="metadata.org.service.id",
                    match=models.MatchValue(value=org_id)
                )
            ]
        ),
        limit=10,
        with_payload=True
    )[0]
    
    if not results:
        return f"Trace ID {trace_id} not found."
        
    details = []
    for point in results:
        details.append(f"Span: {point.payload}")
        
    return "\n".join(details)


if __name__ == "__main__":
    # fastmcp run server.py
    mcp.run()

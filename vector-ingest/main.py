import os
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, Request, Response
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = "telemetry_traces"
MODEL_NAME = "all-MiniLM-L6-v2"

# Initialize clients
logger.info(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

logger.info(f"Loading Sentence Transformer model {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)

# Ensure collection exists
try:
    qdrant.get_collection(COLLECTION_NAME)
    logger.info(f"Collection {COLLECTION_NAME} exists.")
except Exception:
    logger.info(f"Creating collection {COLLECTION_NAME}...")
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

def extract_attributes(span_resource_attributes, span_attributes) -> Dict[str, Any]:
    """Helper to merge and format attributes for metadata."""
    attrs = {}
    
    # Process resource attributes (e.g. service.name)
    for kv in span_resource_attributes:
        key = kv.key
        if kv.value.HasField('string_value'):
            attrs[key] = kv.value.string_value
        elif kv.value.HasField('int_value'):
            attrs[key] = kv.value.int_value
            
    # Process span attributes
    for kv in span_attributes:
        key = kv.key
        if kv.value.HasField('string_value'):
            attrs[key] = kv.value.string_value
        elif kv.value.HasField('int_value'):
            attrs[key] = kv.value.int_value
            
    return attrs

def span_to_text(span, resource_attrs) -> str:
    """Converts a span to a text representation for embedding."""
    service_name = resource_attrs.get('service.name', 'unknown')
    service_version = resource_attrs.get('service.version', 'unknown')
    operation = span.name
    
    # Extract interesting attributes for the text
    text_parts = [f"Service: {service_name} ({service_version})", f"Operation: {operation}"]
    
    # Code Location
    filepath = resource_attrs.get('code.filepath')
    lineno = resource_attrs.get('code.lineno')
    if filepath:
        text_parts.append(f"Location: {filepath}:{lineno}")
    
    # Add status if error
    if span.status.code == 2: # Error
        text_parts.append(f"Status: Error ({span.status.message})")
        
    # Events often contain logs/errors
    for event in span.events:
        if event.name == 'exception':
            evt_attrs = extract_attributes([], event.attributes)
            exc_type = evt_attrs.get('exception.type', 'Exception')
            exc_msg = evt_attrs.get('exception.message', '')
            text_parts.append(f"Exception: {exc_type}: {exc_msg}")
        else:
            text_parts.append(f"Event: {event.name}")
        
    return " | ".join(text_parts)

@app.post("/v1/traces")
async def ingest_traces(request: Request):
    try:
        content_encoding = request.headers.get("content-encoding", "")
        body = await request.body()
        
        if "gzip" in content_encoding:
            import gzip
            body = gzip.decompress(body)
            
        trace_request = ExportTraceServiceRequest()
        trace_request.ParseFromString(body)
        
        points = []
        
        for resource_span in trace_request.resource_spans:
            resource_attrs = extract_attributes(resource_span.resource.attributes, [])
            
            for scope_span in resource_span.scope_spans:
                for span in scope_span.spans:
                    # Enrich attributes with span-specific ones
                    full_attrs = extract_attributes(resource_span.resource.attributes, span.attributes)
                    full_attrs['span_id'] = span.span_id.hex()
                    full_attrs['trace_id'] = span.trace_id.hex()
                    full_attrs['span_name'] = span.name
                    full_attrs['org.service.id'] = resource_attrs.get('org.service.id', 'unknown')
                    full_attrs['org.service.name'] = resource_attrs.get('org.service.name', 'unknown')
                    
                    # Generate embedding
                    text_rep = span_to_text(span, full_attrs)
                    embedding = model.encode(text_rep).tolist()
                    
                    point_id = str(uuid.uuid4())
                    
                    points.append(PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "text": text_rep,
                            "metadata": full_attrs,
                            "timestamp": span.start_time_unix_nano
                        }
                    ))
        
        if points:
            qdrant.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            logger.info(f"Ingested {len(points)} spans to Qdrant.")
            
        return Response(status_code=200)

    except Exception as e:
        logger.error(f"Error processing trace request: {e}")
        return Response(status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

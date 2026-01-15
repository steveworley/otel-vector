FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY server.py .

# Expose port for SSE (if used)
EXPOSE 8000

# Default to running fastmcp via uvicorn logic (stdio is default for 'run', but for docker we might want sse)
# For now, we keep it simple. If run seamlessly, we might want to expose it via SSE.
# But 'mcp run' typically uses stdio. 
# To allow this container to be an MCP server over stdio:
CMD ["python", "server.py"]

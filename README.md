# OpenTelemetry + Vector DB + RAG Agent POC

This Proof of Concept (POC) demonstrates an Observability pipeline that ingests OpenTelemetry traces into a Vector Database (Qdrant) to enable Semantic Search anc AI-driven Root Cause Analysis (RCA).

## 🏗 Architecture

1.  **PHP App**: Generates traces with simulated scenarios (Latency, Error, Saturation).
2.  **OpenTelemetry Collector**: Receives traces and routes them to two destinations:
    *   **Aspire Dashboard**: For standard trace visualization.
    *   **Vector Ingest Service**: For embedding and storage.
3.  **Vector Ingest Service**: A FastAPI service that:
    *   Receives OTLP traces.
    *   Generates embeddings using `all-MiniLM-L6-v2`.
    *   Stores them in **Qdrant**.
4.  **MCP Server / Agent**: An AI Agent (using Model Context Protocol) that can query the vector database to answer questions about system health.

## 🚀 Getting Started

### Prerequisites

*   Docker & Docker Compose
*   Python 3.11+
*   Google Gemini API Key (for the AI Agent)

### Setup

1.  **Configure Environment**
    Copy the example environment file and add your API key:
    ```bash
    cp .env.example .env
    # Edit .env and paste your GEMINI_API_KEY
    ```

2.  **Start the Stack**
    ```bash
    docker-compose up --build -d
    ```
    This will spin up all services, including the Qdrant database and the Aspire Dashboard.

3.  **Access the Dashboard**
    *   **Aspire Dashboard**: [http://localhost:18888](http://localhost:18888)
    *   **Qdrant UI**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

## 🚦 Usage

### 1. Generate Traffic
Simulate user traffic and specific failure scenarios:

```bash
# Generate 50 requests (mixed scenarios)
python traffic_generator.py

# Or customize
export TARGET_URL=http://localhost:8080
export REQUEST_COUNT=100
python traffic_generator.py
```

### 2. Verify Ingestion
Check if traces have been indexed in Qdrant and if Golden Signals (Latency, Errors) are detected:

```bash
python verify_golden_signals.py
```

### 3. Ask the AI Agent
You can run the agent locally to analyze the traces:

```bash
# Example query
python vector-ingest/agent.py "Why are some requests failing?"

# Example query for latency
python vector-ingest/agent.py "Do we have any high latency issues?"
```

## 🛠 Project Structure

*   `php-app/`: Telemetry source.
*   `vector-ingest/`: Custom OTLP receiver & embedding service.
*   `mcp-server/`: Model Context Protocol server for AI agent integration.
*   `otel-collector-config.yaml`: Pipeline configuration.

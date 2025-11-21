# Semantic Embedding MCP Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY mcp/semantic_embedding/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp/semantic_embedding ./mcp/semantic_embedding
COPY shared ./shared

EXPOSE 9003

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9003/health || exit 1

CMD ["uvicorn", "mcp.semantic_embedding.main:app", "--host", "0.0.0.0", "--port", "9003"]

# Summarization MCP Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY mcp/summarization/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp/summarization ./mcp/summarization
COPY shared ./shared

EXPOSE 9001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9001/health || exit 1

CMD ["uvicorn", "mcp.summarization.main:app", "--host", "0.0.0.0", "--port", "9001"]

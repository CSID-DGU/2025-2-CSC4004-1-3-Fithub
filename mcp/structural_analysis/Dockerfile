# Structural Analysis MCP Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY mcp/structural_analysis/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp/structural_analysis ./mcp/structural_analysis
COPY shared ./shared

EXPOSE 9002

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9002/health || exit 1

CMD ["uvicorn", "mcp.structural_analysis.main:app", "--host", "0.0.0.0", "--port", "9002"]

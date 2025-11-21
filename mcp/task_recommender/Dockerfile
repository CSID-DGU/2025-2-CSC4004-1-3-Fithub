# Task Recommender MCP Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY mcp/task_recommender/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp/task_recommender ./mcp/task_recommender
COPY shared ./shared

EXPOSE 9005

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9005/health || exit 1

CMD ["uvicorn", "mcp.task_recommender.main:app", "--host", "0.0.0.0", "--port", "9005"]

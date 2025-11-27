# Use official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TEMP_DIR=/tmp/temp_repos \
    LOCAL_MODEL_DIR=/app/models/RepoGraph

# Set work directory
WORKDIR /app

# Install system dependencies (required for tree-sitter, git, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Create temp directory
RUN mkdir -p /tmp/temp_repos

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8000"]

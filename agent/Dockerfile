# Hugging Face Space: Adventist Theological Research Agent + Ollama
# Uses Ollama with gemma4 on the free 16GB RAM tier

FROM ollama/ollama:latest AS ollama

FROM python:3.12-slim-bookworm

# Install Ollama
COPY --from=ollama /usr/local/bin/ollama /usr/local/bin/ollama
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy agent code
COPY agent/app.py agent/config.py agent/requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Space files
COPY agent/README.md /app/README.md

# Startup script — launches Ollama, pulls model, starts FastAPI
COPY agent/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose the FastAPI port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["/app/start.sh"]

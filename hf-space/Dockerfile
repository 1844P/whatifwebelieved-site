FROM ollama/ollama:latest AS ollama-base
FROM python:3.12-slim-bookworm

# Install Ollama binary
COPY --from=ollama-base /usr/local/bin/ollama /usr/local/bin/ollama

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python backend
COPY app.py config.py requirements.txt /app/

# Install deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

CMD ["bash", "/app/start.sh"]

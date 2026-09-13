# ---------------------------------------------------------------------------
# JATS RAG retrieval service, with Ollama bundled for query embeddings.
#
# Build from the REPOSITORY ROOT (so the COPY paths below resolve):
#   docker build -f rag-service/Dockerfile -t jats-rag .
#
# Run (store mounted read-only, Ollama model cache persisted):
#   docker run -d --name jats-rag -p 8088:8088 \
#     -v "G:/My Drive/JATS_RAG:/data/JATS_RAG:ro" \
#     -v jats-ollama:/root/.ollama \
#     -e JATS_RAG_TOKEN=your-shared-secret \
#     jats-rag
# ---------------------------------------------------------------------------
FROM ollama/ollama:latest AS ollama

FROM python:3.12-slim-bookworm

# Ollama binary from the official image (query embeddings run in-process)
COPY --from=ollama /usr/local/bin/ollama /usr/local/bin/ollama

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY rag-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY rag-service/rag_service.py /app/rag_service.py
COPY rag-service/start-container.sh /app/start-container.sh
RUN chmod +x /app/start-container.sh

# Ollama bound to loopback only: the service is the single public door.
ENV OLLAMA_HOST=127.0.0.1:11434 \
    OLLAMA_URL=http://127.0.0.1:11434 \
    EMBED_MODEL=nomic-embed-text \
    JATS_STORE_DIR=/data/JATS_RAG \
    RAG_HOST=0.0.0.0 \
    RAG_PORT=8088

EXPOSE 8088

HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD curl -fsS http://localhost:8088/health || exit 1

CMD ["/app/start-container.sh"]

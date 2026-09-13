#!/bin/sh
# Container entrypoint: start Ollama, ensure the embedding model is present,
# then serve the JATS retrieval API.
set -e

echo "[rag] starting ollama ..."
ollama serve &
OLLAMA_PID=$!

echo "[rag] waiting for ollama ..."
i=0
until curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -gt 60 ]; then
        echo "[rag] ollama did not come up in 60s" >&2
        exit 1
    fi
    sleep 1
done
echo "[rag] ollama up (pid $OLLAMA_PID)"

# Pulls ~274 MB on a cold container; persists if /root/.ollama is a volume.
if ! ollama list 2>/dev/null | grep -q "${EMBED_MODEL%%:*}"; then
    echo "[rag] pulling ${EMBED_MODEL} ..."
    ollama pull "${EMBED_MODEL}"
fi

if [ ! -f "${JATS_STORE_DIR}/store/embeddings.npz" ]; then
    echo "[rag] WARNING: no store at ${JATS_STORE_DIR}/store/embeddings.npz" >&2
    echo "[rag] mount it with -v \"/path/to/JATS_RAG:${JATS_STORE_DIR}:ro\"" >&2
fi

echo "[rag] starting retrieval service on ${RAG_HOST}:${RAG_PORT} ..."
exec python -u /app/rag_service.py

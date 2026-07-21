#!/bin/bash
set -e

echo "=== Starting Ollama ==="
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "=== Waiting for Ollama ==="
for i in $(seq 1 60); do
    if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama ready after ${i}s"
        break
    fi
    sleep 2
done

# Pull model only if not already present
if ! ollama list 2>/dev/null | grep -q qwen3; then
    echo "=== Pulling qwen3:8b (~5GB) ==="
    ollama pull qwen3:8b 2>&1
    echo "=== Model pulled ==="
else
    echo "=== qwen3:8b already cached ==="
fi

# Start the FastAPI app on port 7860 (HF Space standard)
echo "=== Starting Research Agent on port 7860 ==="
exec python -m uvicorn app:app --host 0.0.0.0 --port 7860

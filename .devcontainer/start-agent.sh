#!/bin/bash
set -e

echo "=== Starting Ollama ==="
ollama serve &
sleep 3

# Pull model on first start (subsequent starts use cache)
if ! ollama list 2>/dev/null | grep -q qwen3; then
    echo "=== Pulling qwen3:8b (5.2GB - may take a few minutes) ==="
    ollama pull qwen3:8b 2>&1
fi

echo "=== Starting Research Agent on port 8000 ==="
cd /workspaces/whatifwebelieved-site
export OLLAMA_MODEL=qwen3:8b
exec python -m uvicorn agent.app:app --host 0.0.0.0 --port 8000

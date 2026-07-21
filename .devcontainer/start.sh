#!/bin/bash
# Runs every time the codespace starts
set -euo pipefail

WORKSPACE="/workspaces/whatifwebelieved-site"
cd "$WORKSPACE"

# ---------- Ollama ----------
if ! pgrep -x ollama >/dev/null 2>&1; then
    echo "=== Starting Ollama ==="
    ollama serve &>/dev/null &
    sleep 3
fi

# Wait for Ollama to be responsive (up to 5 min)
echo "=== Waiting for Ollama model ==="
for i in $(seq 1 60); do
    if ollama list 2>/dev/null | grep -q "qwen3"; then
        echo "Model ready after ~$((i*5))s"
        break
    fi
    if [ "$i" -eq 60 ]; then
        echo "WARNING: Model not ready yet — still downloading in background."
    fi
    sleep 5
done

# ---------- Kill stale processes ----------
for port in 8000 8080; do
    pid=$(lsof -ti:"$port" 2>/dev/null || true)
    if [ -n "$pid" ]; then
        kill "$pid" 2>/dev/null || true
        sleep 1
    fi
done

# ---------- FastAPI agent (port 8000) ----------
export OLLAMA_MODEL="qwen3:8b"
nohup python -m uvicorn agent.app:app \
    --host 0.0.0.0 --port 8000 \
    > /tmp/agent.log 2>&1 &
echo "=== Agent started on :8000 — logs at /tmp/agent.log ==="

# ---------- Static site (port 8080) ----------
nohup python -m http.server 8080 \
    --directory "$WORKSPACE" \
    > /tmp/site.log 2>&1 &
echo "=== Static site started on :8080 ==="

# ---------- Health check ----------
echo "=== Waiting for services ==="
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        echo "Agent healthy after ${i}s"
        break
    fi
    [ "$i" -eq 30 ] && echo "WARNING: Agent not healthy yet — check /tmp/agent.log"
    sleep 2
done

echo ""
echo "Ready!"
echo "  Static site:   http://localhost:8080"
echo "  Agent API:     http://localhost:8000/health"
echo "  HF Compat:     http://localhost:7860"

#!/bin/bash
# Runs every time the codespace starts
set -e

# Start Ollama if not already running
if ! pgrep -x ollama > /dev/null; then
    echo "=== Starting Ollama ==="
    ollama serve 2>&1 &
    sleep 3
fi

# Wait for model (up to 10 min for first pull)
echo "=== Waiting for model ==="
for i in $(seq 1 120); do
    if ollama list 2>/dev/null | grep -q qwen3 2>/dev/null; then
        echo "Model ready after ${i}s"
        break
    fi
    if [ $i -eq 120 ]; then
        echo "Model not ready yet — still downloading in background..."
    fi
    sleep 5
done

# Kill any existing agent process
kill $(lsof -t -i:8000) 2>/dev/null || true
sleep 1

# Start the research agent
echo "=== Starting Research Agent on port 8000 ==="
cd /workspaces/whatifwebelieved-site
export OLLAMA_MODEL="qwen3:8b"
nohup python -m uvicorn agent.app:app --host 0.0.0.0 --port 8000 > /tmp/agent.log 2>&1 &
echo "Agent started — logs at /tmp/agent.log"
echo "Health check: http://localhost:8000/health"
echo "Public URL will be shown in VS Code Ports panel (port 8000)"

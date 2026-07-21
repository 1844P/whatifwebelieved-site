#!/bin/bash
set -e

echo "=== Installing Ollama (one-time setup) ==="
curl -fsSL https://ollama.com/install.sh | sh

echo "=== Installing Python dependencies ==="
cd /workspaces/whatifwebelieved-site
pip install -q -r agent/requirements.txt

# Start Ollama and pull model in background
ollama serve 2>&1 &
echo "=== Pulling qwen3:8b in background (continues after setup) ==="
nohup ollama pull qwen3:8b > /tmp/ollama-pull.log 2>&1 &

echo "=== Setup initiated. Agent will start automatically in each session. ==="

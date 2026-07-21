#!/bin/bash
# One-time setup when codespace is first created
set -e

echo "=== Installing Ollama ==="
curl -fsSL https://ollama.com/install.sh | sh

echo "=== Installing Python deps ==="
cd /workspaces/whatifwebelieved-site
pip install -q -r agent/requirements.txt

echo "=== Starting Ollama and pulling model in background ==="
ollama serve 2>&1 &
sleep 3
ollama pull qwen3:8b 2>&1 &
echo "Setup complete — model continues downloading in background."
echo "Run 'ollama list' to check progress."

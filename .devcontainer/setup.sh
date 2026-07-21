#!/bin/bash
# One-time setup when codespace is first created
set -euo pipefail

WORKSPACE="/workspaces/whatifwebelieved-site"
cd "$WORKSPACE"

echo "=== Installing Ollama ==="
if command -v ollama &>/dev/null; then
    echo "Ollama already installed, skipping."
else
    curl -fsSL https://ollama.com/install.sh | sh
    echo "Ollama installed successfully."
fi

echo "=== Pulling qwen3:8b model ==="
ollama serve &>/dev/null &
sleep 2
ollama pull qwen3:8b
echo "Model qwen3:8b ready."

echo "=== Installing Python dependencies ==="
pip install -q -r agent/requirements.txt
echo "Python deps installed."

echo "=== Setup complete ==="

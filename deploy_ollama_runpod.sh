#!/bin/bash
# Quick deploy Ollama to RunPod for WhatIfWeBelieved Agent
# Prereqs: pip install runpodctl && runpodctl config set api_key YOUR_KEY

set -e

POD_NAME="ollama-theology-agent"
GPU_TYPE="RTX A6000"        # $0.17/hr - runs Llama 3.3 70B q4
IMAGE="ollama/ollama:latest"
CONTAINER_DISK=50
PORTS="11434/http"
OLLAMA_ORIGINS="https://whatifwebelieved.vercel.app"

echo "🚀 Deploying Ollama to RunPod..."
echo "Pod: $POD_NAME"
echo "GPU: $GPU_TYPE"
echo "Origin: $OLLAMA_ORIGINS"

# Check if pod already exists
EXISTING=$(runpodctl get pods --name "$POD_NAME" --output json 2>/dev/null | jq -r '.[0].id // empty')

if [ -n "$EXISTING" ]; then
    echo "⚠️ Pod exists (ID: $EXISTING). Starting..."
    runpodctl start pod "$EXISTING"
    POD_ID=$EXISTING
else
    echo "📦 Creating new pod..."
    POD_ID=$(runpodctl create pod \
        --name "$POD_NAME" \
        --image "$IMAGE" \
        --gpu-type "$GPU_TYPE" \
        --gpu-count 1 \
        --ports "$PORTS" \
        --container-disk "$CONTAINER_DISK" \
        --env OLLAMA_ORIGINS="$OLLAMA_ORIGINS" \
        --env OLLAMA_HOST="0.0.0.0:11434" \
        --output json | jq -r '.id')
    echo "✅ Created pod: $POD_ID"
fi

echo "⏳ Waiting for pod to be ready..."
runpodctl wait pod "$POD_ID" --status RUNNING --timeout 120

# Get public URL
URL=$(runpodctl get pod "$POD_ID" --output json | jq -r '.ports[] | select(.privatePort==11434) | .publicUrl')

if [ -z "$URL" ] || [ "$URL" = "null" ]; then
    echo "❌ Could not get public URL. Check RunPod console."
    exit 1
fi

echo ""
echo "✅ Ollama deployed successfully!"
echo ""
echo "🔗 Public URL: $URL"
echo "📋 Test: curl $URL/api/tags"
echo ""
echo "📝 Next steps:"
echo "1. Open RunPod console → Connect → Web Terminal"
echo "2. Run: ollama pull llama3.3:70b-instruct-q4_K_M"
echo "3. In agent page: Select 'Ollama (Local)' → Paste URL → Connect"
echo ""
echo "💰 Cost: ~$0.17/hr (auto-stops after 5 min idle)"
echo "🛑 Stop: runpodctl stop pod $POD_ID"
echo "🗑️ Delete: runpodctl remove pod $POD_ID"
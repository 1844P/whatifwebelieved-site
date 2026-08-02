# Ollama Production Deployment - RunPod (Most Efficient)

## Why RunPod?
- **Per-second billing** - pay only when running
- **GPU access** - run Llama 3.3 70B, Mixtral, etc.
- **Auto-stop** - configure to stop after 5 min idle
- **Public HTTPS** - no tunnels, no CORS proxies needed
- **~$0.34/hr** for A100 40GB (runs 70B quantized)
- **~$0.17/hr** for RTX A6000 48GB (runs 70B 4-bit)

---

## Quick Deploy (3 minutes)

### Option 1: RunPod Web UI (Easiest)
1. Go to https://runpod.io/console/pods
2. Click **"Deploy"** → **"Community Templates"**
3. Search: **`ollama`** → Select **"ollama/ollama:rocm"** (AMD) or **"ollama/ollama:latest"** (NVIDIA)
4. GPU: **RTX A6000 48GB** ($0.17/hr) or **A100 40GB** ($0.34/hr)
5. Container Disk: **50 GB** (for models)
6. Volume Disk: **0 GB** (ephemeral)
7. Ports: **11434/http** (public)
8. Click **Deploy**

### Option 2: RunPod CLI (Scriptable)
```bash
# Install runpodctl
pip install runpodctl

# Set API key (from https://runpod.io/console/user/settings)
runpodctl config set api_key YOUR_API_KEY

# Deploy
runpodctl create pod \
  --name ollama-theology \
  --image ollama/ollama:latest \
  --gpu-type "RTX A6000" \
  --gpu-count 1 \
  --ports "11434/http" \
  --container-disk 50 \
  --env OLLAMA_ORIGINS="https://whatifwebelieved.vercel.app" \
  --env OLLAMA_HOST="0.0.0.0:11434"
```

---

## After Deploy: Get Public URL

1. Wait 30-60s for pod to start
2. In RunPod console → **Connect** → **HTTPS URL**
3. Copy URL: `https://abc123-11434.proxy.runpod.net`
4. **Test**: `curl https://abc123-11434.proxy.runpod.net/api/tags`

---

## Pull Models (One-time)

```bash
# Via RunPod web terminal or SSH
ollama pull llama3.3:70b-instruct-q4_K_M    # 70B 4-bit (~40GB)
ollama pull llama3.1:8b-instruct-q4_K_M     # 8B fallback (~5GB)
ollama pull mistral:7b-instruct-q4_K_M      # 7B fast (~4GB)
```

---

## Connect to Agent Page

1. Open https://whatifwebelieved.vercel.app/agent/index.html
2. Select **"Ollama (Local)"** in dropdown
3. **URL**: Paste your RunPod HTTPS URL
4. **Model**: Select `llama3.3:70b-instruct-q4_K_M`
5. Click **"Connect"** → Status shows "Connected (X models)"
6. Start asking questions

---

## Cost Control

| Setting | Value | Why |
|---------|-------|-----|
| **Auto-stop** | 5 min idle | Stops billing when unused |
| **Max runtime** | 8 hrs | Prevents runaway |
| **Spot instance** | Yes | 50-70% cheaper, may preempt |
| **Model quantization** | q4_K_M | Best quality/size ratio |

**Estimated monthly** (1 hr/day avg): **$5-10/mo**

---

## Alternative: Lambda Labs (If RunPod Full)

```bash
# Lambda Labs - similar pricing, often more availability
# https://cloud.lambdalabs.com/instances
# Use their Ubuntu 22.04 + Docker template
# Install ollama: curl -fsSL https://ollama.com/install.sh | sh
```

---

## Production Hardening (Optional)

```yaml
# docker-compose.yml for VPS (Hetzner/DO)
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    environment:
      - OLLAMA_ORIGINS=https://whatifwebelieved.vercel.app
      - OLLAMA_HOST=0.0.0.0:11434
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

volumes:
  ollama_data:
```

---

## Summary: RunPod is Best For You Because

| Need | RunPod Delivers |
|------|-----------------|
| **Zero maintenance** | Managed infrastructure |
| **Public HTTPS** | Built-in proxy, no tunnels |
| **CORS handled** | `OLLAMA_ORIGINS` env var |
| **Pay per use** | Per-second, auto-stop |
| **70B model** | A6000 48GB fits q4_K_M |
| **Scales** | Add more pods instantly |
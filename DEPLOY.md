# Deployment Guide

## Architecture

| Layer | Tech | Port |
|-------|------|------|
| Frontend | Vite (static HTML/CSS/JS) | 8080 (dev) / static hosting |
| Backend API | FastAPI + Ollama (local LLM) | 8000 |
| LLM | Ollama with `qwen3:8b` | 11434 |

---

## Option A: GitHub Codespaces (Recommended for First-Timers)

One-click full development environment with Ollama pre-installed.

1. Go to the repo on GitHub
2. Click **Code > Codespaces > Create codespace on master**
3. Wait for the container to build (~2 min)
4. The `postStartCommand` automatically:
   - Installs npm dependencies
   - Installs Python requirements
   - Starts Ollama and pulls `qwen3:8b` (~5 min first time)
   - Launches the FastAPI backend on port 8000
   - Serves the Vite dev server on port 8080

5. When prompted, make these ports **public**:
   - **Port 8000** — Research Agent API (`/research`, `/health`)
   - **Port 8080** — Static site preview

6. Open the Port 8080 URL in your browser to see the site

> **Note:** Codespaces are free for 60 hours/month on the Individual plan.
> After first use the model is cached so subsequent starts take ~30 seconds.

---

## Option B: HuggingFace Spaces (Free GPU Inference)

Deploys only the backend API to HF Spaces with a Docker-based environment.

```bash
# From the repo root
cd hf-space

# Install the HF CLI
pip install -U huggingface_hub

# Login (one-time)
huggingface-cli login

# Create and push the Space
huggingface-cli repo create whatifwebelieved-agent --type space --space-sdk docker
git init && git add . && git commit -m "deploy"
git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/whatifwebelieved-agent
git push -u origin main
```

The Space will build the Dockerfile, install Ollama inside the container, and serve
the API on the Space's public URL (typically `https://YOUR_USERNAME-whatifwebelieved-agent.hf.space`).

Update the frontend's API URL to point to this endpoint (see **Frontend API URL** below).

---

## Option C: Local Development

### Prerequisites

- [Node.js](https://nodejs.org/) 18+
- [Python](https://python.org/) 3.10+
- [Ollama](https://ollama.com/download) installed and running

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/1844P/whatifwebelieved-site.git
cd whatifwebelieved-site

# 2. Pull the LLM model (one-time, ~5 GB)
ollama pull qwen3:8b

# 3. Install Python dependencies and start the API
cd agent
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
# API is now at http://localhost:8000

# 4. In a separate terminal, start the frontend
cd ..  # back to repo root
npm install
npm run dev
# Site is now at http://localhost:8000 (or 8080 if vite.config is changed)
```

> **Tip:** The Vite dev server defaults to port 8000 (`vite.config.js`).
> To run both frontend and API simultaneously, change the Vite port:
> ```bash
> npx vite --port 8080
> ```

---

## Option D: Render.com / Railway / Fly.io (Cloud Backend)

These platforms can host the FastAPI backend. The frontend is a static site
and works best on Netlify, Vercel, or GitHub Pages.

### Render.com

1. Connect your GitHub repo
2. Create a **Background Worker** service:
   - **Build Command:** `cd agent && pip install -r requirements.txt`
   - **Start Command:** `cd agent && uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:**
     - `OLLAMA_BASE_URL` = your Ollama endpoint (see below)
     - `OLLAMA_MODEL` = `qwen3:8b`

> **Important:** Render doesn't provide Ollama natively. You need either:
> - A separate Ollama service (e.g., on a GPU instance)
> - Switch to a cloud LLM provider by modifying `agent/app.py`

### Railway

```bash
# Install Railway CLI
npm i -g @railway/cli
railway login
railway init
railway up
```

### Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh
fly auth signup
fly launch
fly deploy
```

For Fly.io, modify the `fly.toml` to expose port 8000 and ensure
the OLLAMA_BASE_URL environment variable points to your LLM backend.

---

## Frontend API URL Configuration

The frontend communicates with the backend API. Update the API URL in
`research.html` or the relevant JS file to match your deployment:

| Deployment | API URL |
|------------|---------|
| Local | `http://localhost:8000` |
| Codespaces | Port 8000 URL from the Ports panel |
| HuggingFace Spaces | `https://YOUR_USERNAME-whatifwebelieved-agent.hf.space` |
| Render/Railway/Fly | Your service's public URL |

---

## Building for Static Hosting

The Vite build produces a `dist/` folder with optimized static files:

```bash
npm run build
# Output in dist/ — deploy this folder to any static host
```

### Netlify

Already configured via `netlify.toml`. Just connect the repo to Netlify
and it will auto-build on every push.

### Vercel

```bash
npm i -g vercel
vercel --prod
```

### GitHub Pages

See `.github/workflows/deploy-pages.yml` — auto-deploys on every push to `master`.
The site will be available at:

```
https://1844P.github.io/whatifwebelieved-site/
```

---

## Health Check

After deploying the API, verify it's running:

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","ollama_connected":true,"model":"qwen3:8b",...}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Ollama won't start | Run `ollama serve` manually, or open the Ollama desktop app |
| Model not found | `ollama pull qwen3:8b` (or use a smaller model like `gemma3:4b`) |
| Out of memory | Use a smaller model: set `OLLAMA_MODEL=gemma3:4b` or `llama3.2:3b` |
| CORS errors | Ensure `allow_origins=["*"]` is set in `agent/app.py` |
| Port 8000 conflict | Kill the process using it, or change the port in the startup command |
| Codespace slow | The first run downloads ~5GB of model weights; subsequent runs are cached |

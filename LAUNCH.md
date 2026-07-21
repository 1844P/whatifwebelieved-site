# What If We Believed — Codespace Launch Guide

## One-Click Launch

Click the green **Code** button on GitHub → **Codespaces** → **Create codespace on main**.

Everything installs automatically:

| Step | What happens |
|------|-------------|
| **Create** | `setup.sh` installs Ollama, pulls `qwen3:8b`, installs Python deps |
| **Start** | `start.sh` boots Ollama, the FastAPI agent (:8000), and static site (:8080) |

## Ports

| Port | Service | URL |
|------|---------|-----|
| **8080** | Static site (research.html, index.html) | Use the public URL from the Ports panel |
| **8000** | FastAPI Research Agent API | `http://localhost:8000/health` |
| **7860** | HF Spaces compatibility | Same server, alternate port |

Set each port to **Public** in the Ports panel if you want external access.

## Manual Setup (if needed)

```bash
# Re-run setup
bash .devcontainer/setup.sh

# Re-run start
bash .devcontainer/start.sh

# Check Ollama model
ollama list

# Check agent logs
tail -f /tmp/agent.log

# Check site logs
tail -f /tmp/site.log
```

## Model

The agent uses **qwen3:8b** via Ollama (local inference, no API key needed).

Override with: `export OLLAMA_MODEL=qwen3:8b`

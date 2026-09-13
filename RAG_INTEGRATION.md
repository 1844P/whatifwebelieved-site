# JATS RAG integration — what changed and how to go live

The theology agent at `whatifwebelieved.vercel.app/agent/index.html` now answers
from the **Journal of the Adventist Theological Society** archive instead of
model memory alone.

```
Browser (public/agent/index.html on Vercel)
   |  POST { message, history, modes… }
   v
Cloudflare Worker  (worker.js — holds the LLM keys)
   |  1. POST /search { query }          <-- NEW
   |----------------------------------> JATS RAG service (rag-service/)
   |  2. inject passages into the         nomic-embed-text + cosine top-k
   |     system prompt, cite as [1][2]    over store/embeddings.npz
   |  3. Gemini 3.5 Flash (OpenRouter fallback)
   v
Answer + "Grounded in the JATS corpus" source list
```

Retrieval is **best-effort**: if the service is unreachable, slow, or not
configured, the agent answers exactly as it does today.

## What changed

| File | Change |
|---|---|
| `worker.js` | Retrieval + grounding block injection; new `sources` / `rag` fields in every response |
| `public/agent/index.html` | `renderSources()` lists the retrieved passages under a reply |
| `rag-service/rag_service.py` | **New** — retrieval API (`/health`, `/search`) |
| `rag-service/requirements.txt`, `Dockerfile`, `start-container.sh`, `start-rag-service.bat` | **New** — packaging |
| `rag-service/test_worker_e2e.mjs` | **New** — 9-scenario end-to-end test |
| `rag-service/README.md` | Service reference |

Nothing else in the site was touched — modes (essay/sermon/bible study), file
upload, provider switching and the hallucination clamp all behave as before.

## Step 1 — give the retrieval service a public HTTPS URL

The Worker runs on Cloudflare's edge, so `localhost` is not reachable from it.
Pick one host:

### A. Cloudflare Tunnel (free, recommended)

Best if the machine that holds the store can stay on. A *named* tunnel keeps the
URL stable across restarts (a quick tunnel URL changes every time).

```powershell
# one-time: install cloudflared, then
cloudflared tunnel login
cloudflared tunnel create jats-rag
cloudflared tunnel route dns jats-rag rag.example.com
cloudflared tunnel run --url http://127.0.0.1:8088 jats-rag
```

Quick tunnel (no domain, throwaway URL — fine for a first test):

```powershell
cloudflared tunnel --url http://127.0.0.1:8088
```

### B. VPS / always-on box (Docker)

```bash
docker build -f rag-service/Dockerfile -t jats-rag .
docker run -d --name jats-rag --restart unless-stopped -p 8088:8088 \
  -v /srv/JATS_RAG:/data/JATS_RAG:ro -v jats-ollama:/root/.ollama \
  -e JATS_RAG_TOKEN=your-shared-secret jats-rag
```

Put TLS in front (Caddy/nginx) or attach it to the same Cloudflare Tunnel.

### C. RunPod (hourly GPU pod)

`rag-service/Dockerfile` builds the same image; expose container port `8088`
and use the pod's public proxy URL. Note that pods bill while running and are
built for GPU work — only worth it if you already keep a pod warm for Ollama.
See `deploy_ollama_runpod.sh` and `OLLAMA_DEPLOY.md` for the existing pattern.

### Lock it down

A public `/search` endpoint can be called by anyone. Set a shared secret on both
sides:

```powershell
$env:JATS_RAG_TOKEN = "a-long-random-string"; .\start-rag-service.bat
```

`/health` stays open (handy for uptime checks) and reports `auth_required: true`.

## Step 2 — point the Worker at it

Cloudflare dashboard → **Workers & Pages → your worker → Settings → Variables
and Secrets**, then add:

| Name | Value | Required |
|---|---|---|
| `RAG_URL` | `https://rag.example.com` (no trailing `/search`) | yes — omit it and retrieval is off |
| `RAG_TOKEN` | same secret as `JATS_RAG_TOKEN` | if you set one |
| `RAG_TOP_K` | `6` default | no |
| `RAG_MIN_SCORE` | `0.2` default (service-side default is `0.15` for direct calls; the Worker's value wins) | no |
| `RAG_TIMEOUT_MS` | `9000` default | no |
| `RAG_DISABLED` | `true` to temporarily bypass retrieval while keeping the URL | no |

Then paste the updated `worker.js` into **Edit code → Deploy** (this repo's
Worker is deployed manually; there is no `wrangler.toml` here).

Check `GEMINI_API_KEY` / `OPENROUTER_API_KEY` are still present — they are what
generate the answer.

## Step 3 — ship the site

```powershell
cd C:\Users\pswwp\AccioWork\2026-09-03-08-04-39-216-40beca5b
git add worker.js public/agent/index.html rag-service RAG_INTEGRATION.md
git commit -m "Ground the theology agent in the JATS RAG corpus"
git push            # Vercel auto-deploys the GitHub repo
```

## Verify

```powershell
# 1. service alive?
curl.exe -s http://127.0.0.1:8088/health

# 2. retrieval sane?  (expect scores ~0.7 on real JATS vocabulary)
curl.exe -s "http://127.0.0.1:8088/search?q=investigative%20judgment%20sanctuary&k=3"

# 3. full stack, no LLM quota spent
python rag-service\rag_service.py       # terminal 1
node rag-service\test_worker_e2e.mjs    # terminal 2 -> ALL CHECKS PASSED

# 4. live: ask "What does the JATS say about the investigative judgment?"
#    -> answer cites [1]/[2] and a "Grounded in the JATS corpus" list appears.
#    -> the worker response should show "rag":{"used":true,"passages":6}
```

Expected cold-start numbers from this machine: store load ~1.8 s, query embed
~0.2 s, cosine search over 8,342 chunks ~0.01 s.

## Tuning

- **Too much prompt** — lower `RAG_TOP_K` (6 → 4). Each passage adds up to 1,200
  chars; the grounding block is capped at 12,000 chars total.
- **Irrelevant passages** — raise `RAG_MIN_SCORE` (0.2 → 0.3). Nothing is
  injected when every passage falls below it.
- **Repetitive passages** — `RAG_MAX_PER_DOC` (default 2, service-side).
- **Follow-ups ("tell me more")** — the Worker merges the previous user turn into
  the retrieval query automatically when the new message is ≤ 6 words.

## Rollback

Set `RAG_DISABLED=true` on the Worker (keeps the URL, stops retrieval) or delete
`RAG_URL`. Both restore the pre-integration behaviour immediately, no code
deploy needed. Revert the page with
`git checkout public/agent/index.html` if you also want the source list gone.

## Notes and limits

- **Corpus scope** — JATS volumes 4–33 (1993–2022, vol. 6 absent), 8,342 embedded chunks. Questions
  about Ellen White's books or Scripture at large are *not* covered by this corpus;
  the prompt tells the model to say so and answer from general knowledge instead.
- **Grounding is not verification** — retrieved passages are scholarly articles and
  they disagree with each other. The prompt keeps the model's normal citation and
  uncertainty rules, and adds "retrieval is not endorsement".
- **Cost** — retrieval runs on your own Ollama; only the answer generation consumes
  Gemini/OpenRouter quota.
- **Not implemented** — reranking, per-question opt-out UI, and caching. Add if the
  corpus grows or latency becomes visible.

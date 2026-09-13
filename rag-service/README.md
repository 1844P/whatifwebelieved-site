# JATS RAG retrieval service

HTTP retrieval over the **Journal of the Adventist Theological Society** vector
store, so `whatifwebelieved.vercel.app/agent/index.html` (via the Cloudflare
Worker) can answer from the corpus instead of model memory alone.

- Store: `G:\My Drive\JATS_RAG` — 8,615 chunks × 768 dims (`nomic-embed-text`),
  8,342 usable after masking the zero-vector rows the hardened ingest left behind.
- Query embedding: local Ollama (`nomic-embed-text`), L2-normalised, cosine top-k.
- HTTP layer: Python standard library only. The sole dependency is `numpy`.

## Run it

```powershell
# Windows
py -3 -m pip install -r requirements.txt
.\start-rag-service.bat          # or: py -3 rag_service.py
```

```bash
# Docker (build from the repository root)
docker build -f rag-service/Dockerfile -t jats-rag .
docker run -d --name jats-rag -p 8088:8088 `
  -v "G:/My Drive/JATS_RAG:/data/JATS_RAG:ro" -v jats-ollama:/root/.ollama jats-rag
```

Prerequisite: Ollama running with the embedding model present
(`ollama pull nomic-embed-text`, ~274 MB).

## Endpoints

| Method | Path | Notes |
|---|---|---|
| `GET` | `/health` | Store stats, embedding model, Ollama reachability, `auth_required` |
| `GET` | `/search?q=...&k=6&min_score=0.2` | Browser-friendly retrieval |
| `POST` | `/search` | `{"query": "...", "k": 6, "min_score": 0.2}` |

```bash
curl -s http://127.0.0.1:8088/health
curl -s "http://127.0.0.1:8088/search?q=sanctuary%20doctrine&k=2"
```

Response shape:

```json
{
  "query": "sanctuary doctrine",
  "k": 2, "min_score": 0.2, "count": 2,
  "results": [
    { "score": 0.7357, "citation": "JATS 10/1 (1999), p. 3",
      "source": "vol10-iss1/1405.pdf", "doc_id": "…",
      "chunk_index": 0, "page": 3, "text": "…" }
  ],
  "timings": { "embed_seconds": 0.19, "search_seconds": 0.006 }
}
```

`citation` is derived from the volume folder and the `[Page N]` marker inside the
chunk, so the model can cite `JATS 17/2 (2006), p. 25` instead of guessing.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `JATS_STORE_DIR` | `G:\My Drive\JATS_RAG` | Store root |
| `JATS_EMB_FILE` / `JATS_META_FILE` | `<store>/store/…` | Explicit artifact paths |
| `OLLAMA_URL` | `http://localhost:11434` | Embedding backend |
| `EMBED_MODEL` | `nomic-embed-text` | Must match the model that built the store |
| `RAG_HOST` / `RAG_PORT` | `0.0.0.0` / `8088` | Listen address |
| `JATS_RAG_TOKEN` | *(unset)* | When set, callers must send `x-rag-token` |
| `JATS_RAG_ALLOW_ORIGIN` | `*` | CORS allow-origin |
| `RAG_TOP_K` | `6` | Default passages returned |
| `RAG_MIN_SCORE` | `0.15` | Similarity floor for direct callers. The Worker sends its own value (0.2 by default), which wins. |
| `RAG_MAX_PER_DOC` | `2` | Cap passages from one PDF (result diversity) |
| `RAG_MAX_K` | `20` | Upper bound on a requested `k` |

## Troubleshooting

- **`Store not found`** — set `JATS_STORE_DIR`; the folder must contain
  `store/embeddings.npz` and `store/chunk_metadata.json`.
- **`Embedding dimension mismatch`** — `EMBED_MODEL` differs from the model used
  to build the store (the store is 768-dim `nomic-embed-text`).
- **`retrieval failed: … connection refused`** — Ollama is not running
  (`ollama serve`) or `OLLAMA_URL` is wrong.
- **Low scores everywhere** — the query is outside the corpus (JATS covers
  Adventist theological scholarship; this store holds volumes 4–33, 1993–2022).
  That is a correct "no relevant
  content" signal; `RAG_MIN_SCORE` decides when nothing is injected.

## Test

```bash
node test_worker_e2e.mjs        # service on :8088 + ../worker.js
```

Nine scenarios: grounding injected, sources returned, RAG off, service down,
per-request opt-out, kill switch, follow-up context, essay mode, sermon mode,
OpenRouter fallback.

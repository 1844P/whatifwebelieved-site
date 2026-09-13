#!/usr/bin/env python3
"""
JATS RAG retrieval service
==========================

Serves the Journal of the Adventist Theological Society (JATS) vector store over
HTTP so that any caller -- the Cloudflare Worker that powers
https://whatifwebelieved.vercel.app/agent/index.html, a browser, or a local
script -- can retrieve grounded passages.

Endpoints
---------
GET  /health                      -> store + Ollama status
GET  /search?q=...&k=6            -> same as POST /search (handy for browsers)
POST /search  {"query": "...", "k": 6, "min_score": 0.15}
      -> {"query", "k", "count", "results": [{score, citation, source, doc_id,
                                              chunk_index, page, text}]}

Configuration (environment variables)
-------------------------------------
JATS_STORE_DIR          store root (default: G:\\My Drive\\JATS_RAG)
JATS_EMB_FILE           override embeddings path (default <store>/store/embeddings.npz)
JATS_META_FILE          override metadata path  (default <store>/store/chunk_metadata.json)
OLLAMA_URL              Ollama base URL (default http://localhost:11434)
EMBED_MODEL             embedding model (default nomic-embed-text)
RAM_PORT / PORT         listen port (default 8088)
RAG_HOST                listen host (default 0.0.0.0)
JATS_RAG_TOKEN          optional shared secret; when set, callers must send
                        header "x-rag-token: <token>" (or ?token=<token>)
JATS_RAG_ALLOW_ORIGIN   CORS allow-origin (default *)
RAG_TOP_K               default number of passages (default 6)
RAG_MIN_SCORE           default similarity floor (default 0.15)
RAG_MAX_PER_DOC         cap passages from one PDF (default 2)

Only dependency beyond the standard library: numpy.
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
STORE_DIR = Path(os.environ.get("JATS_STORE_DIR", r"G:\My Drive\JATS_RAG"))
EMB_FILE = Path(os.environ.get("JATS_EMB_FILE", STORE_DIR / "store" / "embeddings.npz"))
META_FILE = Path(os.environ.get("JATS_META_FILE", STORE_DIR / "store" / "chunk_metadata.json"))

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")

PORT = int(os.environ.get("RAG_PORT", os.environ.get("PORT", "8088")))
HOST = os.environ.get("RAG_HOST", "0.0.0.0")

TOKEN = os.environ.get("JATS_RAG_TOKEN", "").strip()
ALLOW_ORIGIN = os.environ.get("JATS_RAG_ALLOW_ORIGIN", "*")

DEFAULT_K = int(os.environ.get("RAG_TOP_K", "6"))
MAX_K = int(os.environ.get("RAG_MAX_K", "20"))
DEFAULT_MIN_SCORE = float(os.environ.get("RAG_MIN_SCORE", "0.15"))
MAX_PER_DOC = int(os.environ.get("RAG_MAX_PER_DOC", "2"))

MAX_QUERY_CHARS = 2000      # nomic-embed-text has a 2048-token window
MAX_PASSAGE_CHARS = 1800    # hard cap on a single returned passage

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
_PAGE_RE = re.compile(r"\[Page (\d+)\]")
_SOURCE_RE = re.compile(r"vol(\d+)-iss(\d+)", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Store
# --------------------------------------------------------------------------- #
class Store:
    """L2-normalised embedding matrix + parallel metadata, with garbage masked."""

    def __init__(self, emb_file: Path, meta_file: Path) -> None:
        t0 = time.time()
        data = np.load(emb_file)
        key = "embeddings" if "embeddings" in data.files else data.files[0]
        raw = np.asarray(data[key], dtype=np.float32)

        with open(meta_file, encoding="utf-8") as fh:
            meta = json.load(fh)

        if len(meta) != raw.shape[0]:
            raise SystemExit(
                "Store mismatch: %d vectors vs %d metadata records" % (raw.shape[0], len(meta))
            )

        norms = np.linalg.norm(raw, axis=1)
        # The hardened ingest leaves all-zero rows behind for chunks it refused to
        # embed (broken-font PDFs). They can never match, so mask them out.
        self.usable = norms > 1e-6
        self.matrix = raw / np.maximum(norms[:, None], 1e-9)
        self.meta = meta
        self.dim = int(raw.shape[1])
        self.n_total = int(raw.shape[0])
        self.n_usable = int(self.usable.sum())
        self.load_seconds = round(time.time() - t0, 2)

        # doc_id -> first chunk, used to enrich a hit with its document header
        self.doc_first: dict[str, int] = {}
        for i, m in enumerate(meta):
            if m["doc_id"] not in self.doc_first:
                self.doc_first[m["doc_id"]] = i

    # -- helpers ---------------------------------------------------------- #
    @staticmethod
    def _citation(source: str, page: int | None) -> str:
        m = _SOURCE_RE.search(source or "")
        if m:
            vol, iss = int(m.group(1)), int(m.group(2))
            year = 1989 + vol  # JATS vol 1 = 1990
            label = "JATS %d/%d (%d)" % (vol, iss, year)
        else:
            label = "JATS"
        if page:
            label += ", p. %d" % page
        return label

    def search(self, query: str, k: int, min_score: float) -> list[dict]:
        query = (query or "").strip()
        if not query:
            return []

        t0 = time.time()
        qvec = embed_query(query)
        t_embed = time.time() - t0

        if qvec.shape[0] != self.dim:
            raise RuntimeError(
                "Embedding dimension mismatch: query %d vs store %d. "
                "Is EMBED_MODEL the same model used to build the store?" % (qvec.shape[0], self.dim)
            )

        t1 = time.time()
        scores = self.matrix @ qvec
        scores[~self.usable] = -1.0
        order = np.argsort(-scores)
        t_search = time.time() - t1

        results: list[dict] = []
        per_doc: dict[str, int] = {}
        for i in order:
            if len(results) >= k:
                break
            score = float(scores[i])
            if score < min_score:
                break
            item = self.meta[i]
            doc_id = item.get("doc_id", "")
            if per_doc.get(doc_id, 0) >= MAX_PER_DOC:
                continue
            per_doc[doc_id] = per_doc.get(doc_id, 0) + 1

            text = item.get("text", "")
            page_match = _PAGE_RE.search(text)
            page = int(page_match.group(1)) if page_match else None
            source = item.get("source", "")

            results.append({
                "score": round(score, 4),
                "citation": self._citation(source, page),
                "source": source.replace("\\", "/"),
                "doc_id": doc_id,
                "chunk_index": item.get("chunk_index"),
                "page": page,
                "text": text[:MAX_PASSAGE_CHARS],
            })

        timings = {"embed_seconds": round(t_embed, 3), "search_seconds": round(t_search, 4)}
        return results, timings


# --------------------------------------------------------------------------- #
# Query embedding (Ollama)
# --------------------------------------------------------------------------- #
def embed_query(text: str) -> np.ndarray:
    """Embed with the local Ollama instance; normalised to unit length."""
    text = text[:MAX_QUERY_CHARS]
    payload = json.dumps({"model": EMBED_MODEL, "input": text}).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL + "/api/embed", data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with _OPENER.open(req, timeout=120) as resp:
            body = json.loads(resp.read())
        vec = body["embeddings"][0]
    except urllib.error.HTTPError as exc:
        if exc.code not in (400, 404):  # older Ollama: /api/embeddings with "prompt"
            raise
        payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode("utf-8")
        req = urllib.request.Request(
            OLLAMA_URL + "/api/embeddings", data=payload,
            headers={"Content-Type": "application/json"},
        )
        with _OPENER.open(req, timeout=120) as resp:
            vec = json.loads(resp.read())["embedding"]

    arr = np.asarray(vec, dtype=np.float32)
    norm = float(np.linalg.norm(arr))
    return arr / norm if norm > 1e-9 else arr


def ollama_status() -> dict:
    try:
        with _OPENER.open(OLLAMA_URL + "/api/tags", timeout=5) as resp:
            models = [m.get("name", "") for m in json.loads(resp.read()).get("models", [])]
        hit = any(m.split(":")[0] == EMBED_MODEL.split(":")[0] for m in models)
        return {"reachable": True, "model_present": hit, "models": models}
    except Exception as exc:  # noqa: BLE001 - report any failure to the caller
        return {"reachable": False, "model_present": False, "error": str(exc)}


# --------------------------------------------------------------------------- #
# HTTP layer
# --------------------------------------------------------------------------- #
class Handler(BaseHTTPRequestHandler):
    server_version = "JATSRAG/1.0"
    store: Store = None  # type: ignore[assignment]

    # -- plumbing --------------------------------------------------------- #
    def log_message(self, fmt, *args):  # quieter, timestamped logging
        sys.stderr.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", ALLOW_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, x-rag-token")

    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _authorised(self, query: dict) -> bool:
        if not TOKEN:
            return True
        supplied = self.headers.get("x-rag-token") or (query.get("token") or [""])[0]
        return supplied == TOKEN

    # -- routes ----------------------------------------------------------- #
    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):  # noqa: N802
        self._guarded(self._handle_get)

    def do_POST(self):  # noqa: N802
        self._guarded(self._handle_post)

    def _guarded(self, fn) -> None:
        """Never drop the connection: turn any handler bug into a JSON 500."""
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            try:
                self._send(500, {"error": "internal error: %s" % exc})
            except Exception:  # noqa: BLE001 - headers already sent
                pass

    def _handle_get(self) -> None:
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query or "")

        if path in ("/", "/health", "/healthz"):
            self._send(200, {
                "ok": True,
                "service": "jats-rag",
                "chunks_total": self.store.n_total,
                "chunks_usable": self.store.n_usable,
                "dim": self.store.dim,
                "embed_model": EMBED_MODEL,
                "store": str(EMB_FILE),
                "load_seconds": self.store.load_seconds,
                "ollama": ollama_status(),
                "auth_required": bool(TOKEN),
            })
            return

        if path == "/search":
            if not self._authorised(query):
                self._send(401, {"error": "unauthorized"})
                return
            self._run_search(
                query.get("q", [""])[0],
                query.get("k", [None])[0],
                query.get("min_score", [None])[0],
            )
            return

        self._send(404, {"error": "not found", "paths": ["/health", "/search"]})

    def _handle_post(self) -> None:
        from urllib.parse import urlparse

        path = urlparse(self.path).path.rstrip("/") or "/"
        if path != "/search":
            self._send(404, {"error": "not found", "paths": ["/health", "/search"]})
            return

        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError as exc:
            self._send(400, {"error": "invalid JSON: %s" % exc})
            return

        if not self._authorised({}):
            self._send(401, {"error": "unauthorized"})
            return

        self._run_search(body.get("query") or body.get("q") or "",
                         body.get("k"), body.get("min_score"))

    # -- shared search path ----------------------------------------------- #
    def _run_search(self, query: str, k, min_score) -> None:
        try:
            k = int(k) if k is not None else DEFAULT_K
        except (TypeError, ValueError):
            k = DEFAULT_K
        k = max(1, min(k, MAX_K))
        try:
            min_score = float(min_score) if min_score is not None else DEFAULT_MIN_SCORE
        except (TypeError, ValueError):
            min_score = DEFAULT_MIN_SCORE

        if not (query or "").strip():
            self._send(400, {"error": "missing 'query'"})
            return

        try:
            results, timings = self.store.search(query, k, min_score)
        except Exception as exc:  # noqa: BLE001
            self._send(502, {"error": "retrieval failed: %s" % exc})
            return

        self._send(200, {
            "query": query,
            "k": k,
            "min_score": min_score,
            "count": len(results),
            "results": results,
            "timings": timings,
        })


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> int:
    if not EMB_FILE.exists() or not META_FILE.exists():
        print("Store not found.\n  embeddings: %s\n  metadata:   %s" % (EMB_FILE, META_FILE))
        print("Set JATS_STORE_DIR (or JATS_EMB_FILE / JATS_META_FILE) to point at the store.")
        return 1

    print("Loading JATS store ...")
    store = Store(EMB_FILE, META_FILE)
    Handler.store = store
    print("  %d chunks (%d usable), dim %d, loaded in %.2fs"
          % (store.n_total, store.n_usable, store.dim, store.load_seconds))

    st = ollama_status()
    if not st["reachable"]:
        print("  WARNING: Ollama unreachable at %s -- %s" % (OLLAMA_URL, st.get("error", "")))
    elif not st["model_present"]:
        print("  WARNING: embedding model '%s' not found. Run: ollama pull %s" % (EMBED_MODEL, EMBED_MODEL))
    else:
        print("  Ollama OK, embedding model '%s' present" % EMBED_MODEL)

    # warm the embedder so the first real query is not cold
    threading.Thread(target=lambda: embed_query("warmup"), daemon=True).start()

    print("Serving on http://%s:%d  (/health, /search)%s"
          % (HOST, PORT, "  [token required]" if TOKEN else ""))
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

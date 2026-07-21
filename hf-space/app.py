"""
Adventist Theological Research Agent — FastAPI Backend (Ollama Edition)

A research agent that answers theological questions from a Seventh-day Adventist
worldview, using web search for source discovery and a local Ollama LLM for analysis.

Usage:
    pip install -r requirements.txt
    Make sure Ollama is running with nemotron pulled:  ollama pull nemotron
    uvicorn app:app --host 0.0.0.0 --port 8000
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import sys

_agent_dir = os.path.dirname(os.path.abspath(__file__))
if _agent_dir not in sys.path:
    sys.path.insert(0, _agent_dir)

from config import ADVENTIST_SYSTEM_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:8b")

app = FastAPI(
    title="Adventist Theological Research Agent",
    description="AI-powered theological research grounded in the Seventh-day Adventist worldview (Ollama/Nemotron)",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=2000, description="The theological question to research")
    model: Optional[str] = Field(None, description=f"Ollama model override (default: {DEFAULT_MODEL})")

class ResearchResponse(BaseModel):
    report: str
    question: str
    model_used: str
    generated_at: str
    search_results_count: int

# ---------------------------------------------------------------------------
# Web Search via DuckDuckGo
# ---------------------------------------------------------------------------

async def search_web(query: str, max_results: int = 8) -> list[dict]:
    """Search the web using DuckDuckGo HTML endpoint (no API key needed)."""
    results = []
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            params = {"q": query, "t": "h_", "ia": "web"}
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params=params,
                headers={"User-Agent": "Mozilla/5.0 (compatible; TheologicalResearchBot/1.0)"},
            )
            if resp.status_code == 200:
                from html.parser import HTMLParser
                class DDGParser(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.results = []
                        self._in_result = False
                        self._in_title = False
                        self._in_snippet = False
                        self._current = {}
                    def handle_starttag(self, tag, attrs):
                        attrs_dict = dict(attrs)
                        cls = attrs_dict.get("class", "")
                        if tag == "div" and "result" in cls and "links" not in cls and "results_links" not in cls:
                            self._in_result = True
                            self._current = {"title": "", "snippet": "", "url": ""}
                        if self._in_result:
                            if tag == "a" and "result__a" in cls:
                                self._in_title = True
                                self._current["url"] = attrs_dict.get("href", "")
                            if tag == "a" and "result__snippet" in cls:
                                self._in_snippet = True
                    def handle_data(self, data):
                        if self._in_title:
                            self._current["title"] += data.strip()
                        if self._in_snippet:
                            self._current["snippet"] += data.strip()
                    def handle_endtag(self, tag):
                        if self._in_title and tag == "a":
                            self._in_title = False
                        if self._in_snippet and tag == "a":
                            self._in_snippet = False
                            self.results.append(self._current.copy())
                            self._in_result = False
                            self._current = {}

                parser = DDGParser()
                parser.feed(resp.text)
                results = parser.results[:max_results]
    except Exception as e:
        logger.warning(f"Web search failed: {e}")
    return results

async def build_search_queries(question: str) -> list[str]:
    """Generate targeted search queries for theological research."""
    base = question.strip()
    return [
        f"{base} site:egwwritings.org OR site:adventist.org",
        f"{base} Seventh-day Adventist theology",
        f"{base} Bible study",
    ]

# ---------------------------------------------------------------------------
# Ollama LLM Integration
# ---------------------------------------------------------------------------

async def call_ollama(
    question: str,
    search_context: str,
    model: str | None = None,
    stream: bool = False,
) -> str | AsyncGenerator:
    """Call Ollama with the Adventist system prompt and search context."""

    model = model or DEFAULT_MODEL

    user_message = f"""Based on the following web search results, provide a comprehensive theological research report answering the question. Use the web results as source material, but ensure all conclusions are grounded in Scripture and consistent with Seventh-day Adventist theology.

QUESTION: {question}

WEB SEARCH RESULTS:
{search_context if search_context else "No web results available. Use your training knowledge of Adventist theology and Scripture."}

Remember: Output a well-structured Markdown report following the required format. Every claim must include a citation."""

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": ADVENTIST_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "stream": stream,
        "options": {
            "num_predict": 8192,
            "temperature": 0.3,
        },
    }

    if stream:
        return _stream_ollama(payload, model)
    else:
        return await _call_ollama_sync(payload, model)


async def _call_ollama_sync(payload: dict, model: str) -> str:
    """Non-streaming Ollama call."""
    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Ollama is not running. Start it with: ollama serve")
        if resp.status_code != 200:
            body = resp.text[:500]
            logger.error(f"Ollama error: {resp.status_code} {body}")
            if "allocate" in body or "memory" in body.lower():
                raise HTTPException(status_code=502, detail=f"Model '{model}' is too large for available RAM. Try a smaller model like gemma3:4b or llama3.2:3b.")
            raise HTTPException(status_code=502, detail=f"Ollama error ({resp.status_code}): {body}")
        data = resp.json()
        return data["message"]["content"]


async def _stream_ollama(payload: dict, model: str):
    """Streaming Ollama call — yields JSON chunks for SSE."""
    async with httpx.AsyncClient(timeout=600.0) as client:
        async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/chat", json=payload) as resp:
            if resp.status_code != 200:
                body = await resp.aread()
                logger.error(f"Ollama stream error: {resp.status_code} {body[:500]}")
                yield json.dumps({"type": "error", "message": f"Ollama error: {resp.status_code}"})
                return
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                    if chunk.get("done"):
                        return
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        yield json.dumps({"type": "token", "content": token})
                except json.JSONDecodeError:
                    continue

# ---------------------------------------------------------------------------
# Research Pipeline
# ---------------------------------------------------------------------------

async def run_research(question: str, model: str | None) -> ResearchResponse:
    """Full research pipeline: search -> assemble context -> LLM -> report."""

    logger.info(f"Research request: {question[:80]}... (model={model or DEFAULT_MODEL})")

    queries = await build_search_queries(question)
    search_results_lists = await asyncio.gather(*[search_web(q, max_results=5) for q in queries])
    all_results = []
    seen_urls = set()
    for results in search_results_lists:
        for r in results:
            url = r.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)

    logger.info(f"Found {len(all_results)} unique search results")

    search_context_parts = []
    for i, r in enumerate(all_results[:12], 1):
        title = r.get("title", "Untitled")
        snippet = r.get("snippet", "")
        url = r.get("url", "")
        search_context_parts.append(f"[{i}] {title}\n    {snippet}\n    URL: {url}")
    search_context = "\n\n".join(search_context_parts)

    model_name = model or DEFAULT_MODEL
    report = await call_ollama(question, search_context, model, stream=False)

    return ResearchResponse(
        report=report,
        question=question,
        model_used=model_name,
        generated_at=datetime.utcnow().isoformat() + "Z",
        search_results_count=len(all_results),
    )

# ---------------------------------------------------------------------------
# Streaming via SSE
# ---------------------------------------------------------------------------

async def stream_research(question: str, model: str | None):
    """Stream the research pipeline with Server-Sent Events."""

    async def event_stream():
        yield f"data: {json.dumps({'type': 'status', 'message': 'Starting research...'})}\n\n"

        queries = await build_search_queries(question)
        yield f"data: {json.dumps({'type': 'status', 'message': f'Searching {len(queries)} sources...'})}\n\n"

        search_results_lists = await asyncio.gather(*[search_web(q, max_results=5) for q in queries])
        all_results = []
        seen_urls = set()
        for results in search_results_lists:
            for r in results:
                url = r.get("url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(r)

        yield f"data: {json.dumps({'type': 'status', 'message': f'Found {len(all_results)} sources. Generating analysis...'})}\n\n"

        search_context_parts = []
        for i, r in enumerate(all_results[:12], 1):
            title = r.get("title", "Untitled")
            snippet = r.get("snippet", "")
            url = r.get("url", "")
            search_context_parts.append(f"[{i}] {title}\n    {snippet}\n    URL: {url}")
        search_context = "\n\n".join(search_context_parts)

        model_name = model or DEFAULT_MODEL
        yield f"data: {json.dumps({'type': 'status', 'message': f'Calling {model_name} via Ollama — streaming tokens...'})}\n\n"

        try:
            full_report = ""
            token_stream = await call_ollama(question, search_context, model, stream=True)
            async for chunk in token_stream:
                event = json.loads(chunk)
                if event.get("type") == "token":
                    full_report += event["content"]
                    # Forward token to client for live rendering
                    yield f"data: {json.dumps({'type': 'token', 'content': event['content']})}\n\n"
                elif event.get("type") == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event['message']})}\n\n"
                    return

            result = ResearchResponse(
                report=full_report,
                question=question,
                model_used=model_name,
                generated_at=datetime.utcnow().isoformat() + "Z",
                search_results_count=len(all_results),
            )
            yield f"data: {json.dumps({'type': 'complete', 'data': result.model_dump()})}\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"status": "ok", "service": "Adventist Theological Research Agent", "version": "2.0.0", "backend": "ollama", "default_model": DEFAULT_MODEL}

@app.get("/health")
async def health():
    """Check health including Ollama connectivity."""
    ollama_ok = False
    models = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                ollama_ok = True
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return {"status": "healthy", "ollama_connected": ollama_ok, "model": DEFAULT_MODEL, "available_models": models}

@app.get("/models")
async def list_models():
    """List available Ollama models."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                return {"models": [m["name"] for m in data.get("models", [])]}
    except Exception:
        pass
    return {"models": [], "error": "Ollama not reachable"}

@app.post("/research", response_model=ResearchResponse)
async def research(req: ResearchRequest):
    """Submit a theological question for Adventist-grounded research."""
    return await run_research(req.question, req.model)

@app.post("/research/stream")
async def research_stream(req: ResearchRequest):
    """Submit a theological question with streaming progress updates (SSE)."""
    return await stream_research(req.question, req.model)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

---
title: Adventist Theological Research Agent
emoji: 📖
colorFrom: "#8b6914"
colorTo: "#6b4f10"
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# Adventist Theological Research Agent

AI-powered theological research grounded in the Seventh-day Adventist worldview.

Ask any theological question and receive a structured Markdown report with Scripture citations, Ellen G. White references, and Adventist theological analysis.

## API

- `POST /research` — Submit a question: `{"question": "..."}`
- `POST /research/stream` — Streaming SSE endpoint for live progress
- `GET /health` — Health check

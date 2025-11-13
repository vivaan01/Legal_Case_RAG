## Legal Case RAG (Adaptive, Tool-Enriched, Feedback-Healing) — Ollama Local

### Overview
End-to-end adaptive RAG for legal cases with:
- Hybrid retrieval (FAISS + BM25)
- Self-healing via feedback (< 3 triggers re-query with refined prompt)
- Memory (extracts case type like "contract" into a dict)
- Citation-check tool (mock lookup)
- Streaming responses token-by-token
- Redis rating cache using `HINCRBY`
- FastAPI backend + Streamlit UI
- LLM and embeddings served locally via Ollama

### Requirements
- Python 3.10+
- Ollama running locally (`http://localhost:11434`)
- Models:
  - LLM: set `OLLAMA_MODEL` (default: `mystrial`)
  - Embeddings: set `OLLAMA_EMBED_MODEL` (default: `nomic-embed-text`)
- Optional Redis server (Windows: use Docker or local port 6379). Falls back to in-memory if unavailable.

### Install
```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
```

### Run
1) Start backend:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

2) Start UI:
```bash
streamlit run ui/app.py
```

3) In UI:
- Upload PDF(s) to ingest
- Ask a question (e.g., "Breach damages?")
- Rate the answer; rating < 3 triggers self-heal re-query

### API Quick Test (PowerShell)
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
```

Ingest:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/ingest" -Method Post -InFile ".\sample.pdf" -ContentType "application/pdf"
```

Query (streaming):
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/query_stream?query=Breach%20damages%3F" -UseBasicParsing
```

Feedback heal:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/feedback" -Method Post -Body (@{ query="Breach damages?"; rating=2 } | ConvertTo-Json) -ContentType "application/json"
```

### Notes
- Vector search uses DocArray in-memory store (rebuilt at ingest) and `data/bm25_docs.pkl` for BM25.
- Backend modules:
  - `backend/core/` → settings and dependency providers
  - `backend/api/routes.py` → FastAPI endpoints
  - `backend/services/` → retrieval, LLM, memory, tools, feedback, RAG chains, utilities
- Ratings cached in Redis hash `ratings:{case_key}`; fields are `1..5`.
- If Redis is unavailable, counts persist only in-memory for this run.



from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from backend.core.deps import get_app_settings, get_memory_manager, get_rating_store
from backend.core.settings import Settings
from backend.models import IngestResponse, QueryRequest, QueryResponse, FeedbackRequest
from backend.services.memory import MemoryManager
from backend.services.feedback import RatingStore
from backend.services.retrieval import load_pdf_and_chunk
import pickle
from backend.services.rag_chain import build_query_chain, build_stream_chain
from backend.services.utils import heal_query

router = APIRouter()


@router.get("/health")
def health(settings: Settings = Depends(get_app_settings)):
	return {"status": "ok", "data_dir": str(settings.data_dir.resolve())}


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
	file: UploadFile = File(...),
	settings: Settings = Depends(get_app_settings),
):
	if not file.filename.lower().endswith(".pdf"):
		raise HTTPException(status_code=400, detail="Please upload a PDF.")

	tmp_path = settings.data_dir / f"upload_{file.filename}"
	with open(tmp_path, "wb") as f:
		f.write(await file.read())

	try:
		new_docs = load_pdf_and_chunk(str(tmp_path))
	except Exception as exc:
		raise HTTPException(status_code=400, detail=f"PDF parsing failed: {exc}")

	bm25_pickle = settings.data_dir / "bm25_docs.pkl"
	try:
		if bm25_pickle.exists():
			with open(bm25_pickle, "rb") as f:
				existing_docs = pickle.load(f)
		else:
			existing_docs = []
		combined_docs = existing_docs + new_docs
		with open(bm25_pickle, "wb") as f:
			pickle.dump(combined_docs, f)
		num_docs = len(combined_docs)
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f"Failed to update BM25 docs: {exc}")

	vector_saved = True
	return IngestResponse(chunks=len(new_docs), vectordb_saved=vector_saved, bm25_docs=num_docs)


@router.post("/query", response_model=QueryResponse)
async def query(
	payload: QueryRequest,
	settings: Settings = Depends(get_app_settings),
	memory: MemoryManager = Depends(get_memory_manager),
):
	user_id = payload.user_id or "default_user"
	history = memory.build_history(user_id, payload.query)
	chain = build_query_chain(settings, settings.data_dir)
	answer = await chain.ainvoke({"query": payload.query, "history": history})
	return QueryResponse(answer=answer, sources=[], meta={"healed": False})


@router.post("/summary", response_model=QueryResponse)
async def summary(
	payload: QueryRequest,
	settings: Settings = Depends(get_app_settings),
	memory: MemoryManager = Depends(get_memory_manager),
):
	user_id = payload.user_id or "default_user"
	history = memory.build_history(user_id, payload.query)
	chain = build_query_chain(settings, settings.data_dir)
	answer = await chain.ainvoke({"query": payload.query, "history": history})
	return QueryResponse(answer=answer, sources=[], meta={"alias": "summary", "healed": False})


@router.get("/query_stream")
async def query_stream(
	query: str = Query(...),
	user_id: str = "default_user",
	settings: Settings = Depends(get_app_settings),
	memory: MemoryManager = Depends(get_memory_manager),
):
	try:
		history = memory.build_history(user_id, query)
	except Exception as exc:
		return JSONResponse({"error": f"Memory build failed: {exc}"}, status_code=500)

	try:
		chain = build_stream_chain(settings, settings.data_dir, history)
		print(f"Chain built successfully: {chain}")
	except RuntimeError as exc:
		print(f"RuntimeError in chain build: {str(exc)}")
		return JSONResponse({"error": str(exc), "hint": "Please ingest at least one PDF via /ingest or UI first."}, status_code=400)
	except Exception as exc:
		print(f"Exception in chain build: {str(exc)}")
		return JSONResponse({"error": f"Chain build failed: {exc}", "type": type(exc).__name__}, status_code=500)

	try:
		stream = chain.astream({"query": query, "history": history})
		print("Stream initialized successfully")
	except Exception as exc:
		print(f"Exception in stream init: {str(exc)}")
		return JSONResponse({"error": f"Stream initialization failed: {exc}", "type": type(exc).__name__}, status_code=500)

	async def token_gen() -> AsyncGenerator[bytes, None]:
		try:
			async for chunk in stream:
				text = getattr(chunk, "content", "")
				if text:
					yield text.encode("utf-8")
					await asyncio.sleep(0)
		except Exception as exc:
			yield f"\n[stream-error] {exc}".encode("utf-8")

	return StreamingResponse(token_gen(), headers={"Content-Type": "text/plain; charset=utf-8"})


@router.post("/feedback")
async def feedback(
	payload: FeedbackRequest,
	settings: Settings = Depends(get_app_settings),
	memory: MemoryManager = Depends(get_memory_manager),
	ratings: RatingStore = Depends(get_rating_store),
):
	case_key = "default"
	ratings.record(case_key, payload.rating)

	if payload.rating < 3:
		healed_q = heal_query(payload.query)
		history = memory.build_history(payload.user_id or "default_user", healed_q)
		chain = build_query_chain(settings, settings.data_dir)
		answer = await chain.ainvoke({"query": healed_q, "history": history})
		return JSONResponse({"healed": True, "answer": answer})

	return JSONResponse({"healed": False, "message": "Thanks for your feedback"})



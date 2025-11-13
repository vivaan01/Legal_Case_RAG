from __future__ import annotations

import pickle
from pathlib import Path
from typing import List, Tuple, Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever

from backend.core.settings import Settings
from backend.services.llm import get_embedder


def load_pdf_and_chunk(file_path: str) -> List[Document]:
	loader = PyPDFLoader(file_path)
	raw_docs = loader.load()
	splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
	return splitter.split_documents(raw_docs)


def build_or_load_docarray(docs: List[Document], settings: Settings) -> Tuple[DocArrayInMemorySearch, bool]:
	embedder = get_embedder(settings)
	vdb = DocArrayInMemorySearch.from_documents(docs, embedding=embedder)
	return vdb, True


def build_or_load_bm25(docs: List[Document], data_dir: Path) -> Tuple[BM25Retriever, int]:
	# Ensure absolute path
	data_dir = data_dir.resolve()
	data_dir.mkdir(parents=True, exist_ok=True)
	bm25_pickle = data_dir / "bm25_docs.pkl"
	if bm25_pickle.exists():
		with open(bm25_pickle, "rb") as f:
			stored = pickle.load(f)
		retriever = BM25Retriever.from_documents(stored)
		retriever.k = 6
		return retriever, len(stored)

	with open(bm25_pickle, "wb") as f:
		pickle.dump(docs, f)
	retriever = BM25Retriever.from_documents(docs)
	retriever.k = 6
	return retriever, len(docs)


def get_hybrid_retriever(settings: Settings, data_dir: Path) -> Any:
	# Ensure absolute path
	data_dir = data_dir.resolve()
	bm25_pickle = data_dir / "bm25_docs.pkl"
	print(f"Data dir: {data_dir}")
	print(f"BM25 pickle path: {bm25_pickle}")
	print(f"Exists: {bm25_pickle.exists()}")
	
	if not bm25_pickle.exists():
		print("Pickle not found")
		raise RuntimeError(f"BM25 docs not found at {bm25_pickle}. Please ingest first.")
	
	try:
		print("Attempting to load pickle")
		with open(bm25_pickle, "rb") as f:
			docs = pickle.load(f)
		print(f"Loaded {len(docs)} documents")
	except Exception as exc:
		print(f"Load exception: {exc}")
		raise RuntimeError(f"Failed to load BM25 pickle from {bm25_pickle}: {exc}")

	print("Creating BM25 retriever")
	bm25 = BM25Retriever.from_documents(docs)
	bm25.k = 6

	print("Attempting to create vector store")
	try:
		vector = DocArrayInMemorySearch.from_documents(docs, embedding=get_embedder(settings))
		print("Vector store created successfully")
		return EnsembleRetriever(
			retrievers=[vector.as_retriever(search_kwargs={"k": 6}), bm25],
			weights=[0.55, 0.45],
		)
	except Exception as e:
		print(f"Vector creation failed: {str(e)}")
		return bm25




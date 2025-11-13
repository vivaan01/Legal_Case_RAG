from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class QueryRequest(BaseModel):
	query: str = Field(..., description="User query")
	user_id: Optional[str] = Field(default="default_user")


class FeedbackRequest(BaseModel):
	query: str
	rating: int = Field(ge=1, le=5)
	user_id: Optional[str] = Field(default="default_user")
	extra: Optional[Dict[str, Any]] = None


class IngestResponse(BaseModel):
	chunks: int
	vectordb_saved: bool
	bm25_docs: int


class QueryResponse(BaseModel):
	answer: str
	sources: List[Dict[str, Any]] = []
	meta: Dict[str, Any] = {}



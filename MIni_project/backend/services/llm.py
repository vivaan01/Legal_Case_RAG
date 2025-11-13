from __future__ import annotations

from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings

from backend.core.settings import Settings


def get_chat_model(settings: Settings) -> ChatOllama:
	return ChatOllama(
		model=settings.ollama_model,
		base_url=settings.ollama_base_url,
		temperature=0.2,
	)


def get_embedder(settings: Settings) -> OllamaEmbeddings:
	return OllamaEmbeddings(
		model=settings.ollama_embed_model,
		base_url=settings.ollama_base_url,
	)




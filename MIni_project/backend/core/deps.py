from __future__ import annotations

from functools import lru_cache

from backend.core.settings import get_settings, Settings
from backend.services.memory import MemoryManager
from backend.services.feedback import RatingStore


@lru_cache
def get_memory_manager() -> MemoryManager:
	return MemoryManager()


@lru_cache
def get_rating_store() -> RatingStore:
	return RatingStore(get_settings())


def get_app_settings() -> Settings:
	return get_settings()




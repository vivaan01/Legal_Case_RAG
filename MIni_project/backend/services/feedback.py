from __future__ import annotations

from typing import Dict

try:
	import redis  # type: ignore
except Exception:  # pragma: no cover
	redis = None  # type: ignore

from backend.core.settings import Settings


class RatingStore:
	def __init__(self, settings: Settings):
		self.settings = settings
		self.client = self._init_client()
		self.memory_store: Dict[str, Dict[str, int]] = {}

	def _init_client(self):
		if redis is None:
			return None
		try:
			client = redis.Redis(
				host=self.settings.redis_host,
				port=self.settings.redis_port,
				db=0,
				decode_responses=True,
			)
			client.ping()
			return client
		except Exception:
			return None

	def record(self, case_key: str, rating: int) -> None:
		score_field = str(rating)
		if self.client:
			self.client.hincrby(f"ratings:{case_key}", score_field, 1)
			return
		store = self.memory_store.setdefault(case_key, {})
		store[score_field] = store.get(score_field, 0) + 1




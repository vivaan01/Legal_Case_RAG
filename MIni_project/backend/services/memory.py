from __future__ import annotations

import re
from typing import Dict, Any, Optional, List

from langchain_core.messages import SystemMessage


class MemoryManager:
	def __init__(self) -> None:
		self.user_prefs: Dict[str, Dict[str, Any]] = {}

	def update_case_type(self, user_id: str, text: str) -> Optional[str]:
		types = ["contract", "tort", "criminal", "constitutional", "property", "tax"]
		found = None
		for t in types:
			if re.search(rf"\b{re.escape(t)}\b", text, flags=re.IGNORECASE):
				found = t
				break
		if found:
			self.user_prefs.setdefault(user_id, {})["case_type"] = found
		return found

	def get_user_pref(self, user_id: str, key: str, default=None):
		return self.user_prefs.get(user_id, {}).get(key, default)

	def build_history(self, user_id: str, query: str) -> List[SystemMessage]:
		self.update_case_type(user_id, query)
		case_type = self.get_user_pref(user_id, "case_type")
		history: List[SystemMessage] = []
		if case_type:
			history.append(
				SystemMessage(
					content=f"User is interested in {case_type} cases. Prefer such precedents when relevant."
				)
			)
		return history




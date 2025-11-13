from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_core.tools import tool


class CitationLookupInput(BaseModel):
	case_name: str = Field(..., description="Legal case name to look up, e.g., 'Hadley v. Baxendale'")


MOCK_CITATIONS = {
	"Hadley v. Baxendale": "9 Exch 341 (1854)",
	"Carlill v Carbolic Smoke Ball Co": "[1893] 1 QB 256",
	"Donoghue v Stevenson": "[1932] AC 562",
}


@tool("citation_lookup", args_schema=CitationLookupInput, return_direct=False)
def citation_lookup(case_name: str) -> str:
	"""Check the citation of a given case name. Returns the formal citation if found, else 'Not found'."""
	return MOCK_CITATIONS.get(case_name.strip(), "Not found")




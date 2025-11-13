from __future__ import annotations

from typing import Dict, Any, Iterable, Optional

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnableLambda
from langchain_core.messages import BaseMessage

from backend.core.settings import Settings
from backend.services.llm import get_chat_model
from backend.services.tools import citation_lookup
from backend.services.retrieval import get_hybrid_retriever


def _system_message() -> str:
	return (
		"You are a helpful legal research assistant. "
		"Use provided context chunks to answer. Cite case names you rely on. "
		"If the user seems to be asking about contract disputes, surface relevant precedents."
	)


def build_query_chain(settings: Settings, data_dir) -> RunnableParallel:
	retriever = get_hybrid_retriever(settings, data_dir)
	prompt = ChatPromptTemplate.from_messages(
		[
			("system", _system_message()),
			MessagesPlaceholder("history"),
			("human", "Query: {query}\n\nContext:\n{context}\n\nIf useful, you may call tools."),
		]
	)

	llm = get_chat_model(settings).bind_tools([citation_lookup])

	def _get_context(inputs: Dict[str, Any]) -> str:
		documents = retriever.invoke(inputs["query"])
		return "\n---\n".join(d.page_content for d in documents)

	return RunnableParallel(
		context=RunnableLambda(_get_context),
		query=RunnableLambda(lambda inp: inp["query"]),
		history=RunnableLambda(lambda inp: inp.get("history", [])),
	) | prompt | llm | StrOutputParser()


def build_stream_chain(settings: Settings, data_dir, history: Optional[Iterable[BaseMessage]] = None):
    retriever = get_hybrid_retriever(settings, data_dir)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _system_message()),
            MessagesPlaceholder("history"),
            ("human", "Query: {query}\n\nContext:\n{context}\n\nStream your response."),
        ]
    )
    llm = get_chat_model(settings).bind_tools([citation_lookup])

    def _get_context(inputs: Dict[str, Any]) -> str:
        docs = retriever.invoke(inputs["query"])
        return "\n---\n".join(d.page_content for d in docs)

    chain = (
        RunnableParallel(
            context=RunnableLambda(_get_context),
            query=RunnableLambda(lambda inp: inp["query"]),
            history=RunnableLambda(lambda inp: inp.get("history", [])),
        )
        | prompt
        | llm
    )
    return chain



from typing import TypedDict


class GraphState(TypedDict):

    query: str

    rewritten_query: str

    documents: list

    reranked_documents: list

    context: str

    answer: str

    sources: list
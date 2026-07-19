from app.config import (
    llm,
    llm_rewrite,
    reranker
)
from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)
from app.core.vector_store import (
    vector_store
)

retriever = vector_store.as_retriever(
    search_kwargs={"k": 8}
)

def rewrite_query_node(state):

    query = state["query"]

    history = state.get(
        "chat_history",
        []
    )
    # if len(history) == 0:
    #     return {"rewritten_query": query}
    history_text = ""

    for msg in history[-3:]:

        history_text += (
            f"{msg['role']}: "
            f"{msg['content']}\n"
        )

    prompt_rewrite = f"""
You are a RAG query rewriter rewrite the query if you think this is not answerable with the provided context other wise return the original query.

Rewrite the user's question into a clear, self-contained search query for retrieving internal documents

History:
{history_text}

User Question:
{query}

Rewritten Query:
"""

    response = llm_rewrite.invoke(prompt_rewrite)
    print("Rewritten Query:", response.content.strip())
    return {
        "rewritten_query":
            response.content.strip()
    }

def retrieve_node(state):

    query = state[
        "rewritten_query"
    ]

    docs = retriever.invoke(
        query
    )

    print(
        "Retrieved:",
        len(docs)
    )

    return {

        "documents":
            docs
    }



def rerank_node(state):

    query = state[
        "rewritten_query"
    ]

    docs = state[
        "documents"
    ]

    pairs = [

        [query, doc.page_content]

        for doc in docs
    ]

    scores = reranker.predict(
        pairs
    )

    ranked = sorted(

        zip(scores, docs),

        key=lambda x: x[0],

        reverse=True
    )

    top_docs = [

        doc

        for score, doc

        in ranked[:2]
    ]

    return {

        "reranked_documents":
            top_docs
    }



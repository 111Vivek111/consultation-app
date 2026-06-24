from app.config import (
    llm,
    llm_rewrite,
    reranker
)
from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)
from app.ingestion.chunker import get_embeddings
from app.ingestion.vectorstore import load_vector_store

embeddings = get_embeddings()

vector_store = load_vector_store(
    embeddings
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

    history_text = ""

    for msg in history[-3:]:

        history_text += (
            f"{msg['role']}: "
            f"{msg['content']}\n"
        )

    prompt_rewrite = f"""
You are a query rewriting assistant for a RAG system.

Your task:
Convert the user's latest question into a standalone query.

Rules:
- Resolve pronouns like:
  "it"
  "that"
  "those"
  "this"
  "they"

using chat history.

- Preserve the topic from previous turns.

- If the current question refers to something discussed earlier,
rewrite it as a fully self-contained question.

- Output ONLY the rewritten query.

History:
{history_text}

Current Question:
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


def generate_node(state):

    query = state[
        "rewritten_query"
    ]

    docs = state[
        "reranked_documents"
    ]

    history = state.get(
        "chat_history",
        []
    )

    context = "\n\n".join(

        doc.page_content

        for doc in docs
    )
    print("Context length:", len(context))
    history_text = ""

    for msg in history[-3:]:

        history_text += (
            f"{msg['role']}: "
            f"{msg['content']}\n"
        )


    
    response = llm.invoke([
    SystemMessage(
        content="""
Answer ONLY using the provided context.

Rules:
- No outside knowledge
- No guessing
- If information is missing, say so
- Use concise answers
- keep the answer under 200 words
"""
    ),
    HumanMessage(
        content=f"""
History:
{history_text}

Context:
{context}

Question:
{query}
"""
    )
])
    print("Generated Answer:", response.content)
    output = {
    "answer": response.content,
    "context": context
}

    return output

def citation_node(state):

    docs = state[
        "reranked_documents"
    ]

    sources = []

    seen = set()

    for doc in docs:

        source = doc.metadata.get(
            "source",
            "Unknown"
        )

        page = doc.metadata.get(
            "page",
            "N/A"
        )

        key = (
            source,
            page
        )

        if key not in seen:

            seen.add(key)

            sources.append({

                "source":
                    source,

                "page":
                    page
            })

    answer = state["answer"]

    if sources:

        answer += "\n\nSources:\n"

        for s in sources:

            answer += (
                f"- {s['source']} "
                f"(Page {s['page']})\n"
            )

    return {

        "answer":
            answer,

        "sources":
            sources
    }


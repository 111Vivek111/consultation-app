# app/ingestion/chunker.py

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_experimental.text_splitter import (
    SemanticChunker
)


def get_embeddings():

    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )


def create_chunks(documents):

    embeddings = get_embeddings()

    splitter = SemanticChunker(
        embeddings
    )

    chunks = splitter.split_documents(
        documents
    )

    for idx, chunk in enumerate(chunks):

        chunk.metadata["chunk_id"] = idx

    print(
        f"Chunks Created: {len(chunks)}"
    )

    return chunks, embeddings
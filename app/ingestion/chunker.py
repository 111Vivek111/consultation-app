# app/ingestion/chunker.py

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_experimental.text_splitter import (
    SemanticChunker
)


def get_embeddings():

    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )


def create_chunks(
    documents,
    user_id=None,
    document_id=None,
    document_name=None
):

    embeddings = get_embeddings()

    splitter = SemanticChunker(
        embeddings
    )

    chunks = splitter.split_documents(
        documents
    )

    for idx, chunk in enumerate(chunks):

        chunk.metadata["chunk_id"] = idx

        if user_id:

            chunk.metadata["user_id"] = (
                str(user_id)
            )

        if document_id:

            chunk.metadata["document_id"] = (
                str(document_id)
            )

        if document_name:

            chunk.metadata["document_name"] = (
                document_name
            )

    print(
        f"Chunks Created: {len(chunks)}"
    )

    return chunks, embeddings
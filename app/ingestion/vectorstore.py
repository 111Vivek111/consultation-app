# app/ingestion/vectorstore.py
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from app.config import (
    QDRANT_URL,
    QDRANT_API_KEY
)
def build_vector_store(
    chunks,
    embeddings
):

    vector_store = (
        QdrantVectorStore.from_documents(

            documents=chunks,

            embedding=embeddings,

            url=QDRANT_URL,

            collection_name="policy_manuals"
        )
    )

    return vector_store





def load_vector_store(embeddings):

    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )

    return QdrantVectorStore(

        client=client,

        collection_name="policy_manuals",

        embedding=embeddings
    )
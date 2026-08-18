# app/ingestion/vectorstore.py
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from app.config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION_NAME
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





# app/ingestion/vectorstore.py
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from langchain_qdrant import QdrantVectorStore


def load_vector_store(embeddings):

    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )

    if not client.collection_exists(QDRANT_COLLECTION_NAME):

        vector_size = len(embeddings.embed_query("dimension probe"))

        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )

    return QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION_NAME,
        embedding=embeddings
    )
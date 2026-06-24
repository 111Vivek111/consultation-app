# app/ingestion/vectorstore.py
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore

def build_vector_store(
    chunks,
    embeddings
):

    vector_store = (
        QdrantVectorStore.from_documents(

            documents=chunks,

            embedding=embeddings,

            path="./qdrant_data",

            collection_name="policy_manuals"
        )
    )

    return vector_store





def load_vector_store(embeddings):

    client = QdrantClient(
        path="./qdrant_data"
    )

    return QdrantVectorStore(

        client=client,

        collection_name="policy_manuals",

        embedding=embeddings
    )
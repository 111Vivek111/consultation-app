# build_index.py
import pickle

from app.ingestion.loader import (
    load_documents
)

from app.ingestion.cleaner import (
    clean_documents
)

from app.ingestion.metadata import (
    add_metadata
)

from app.ingestion.chunker import (
    create_chunks
)

from app.ingestion.vectorstore import (
    build_vector_store
)


docs = load_documents(
    "knowladge"
)

docs = clean_documents(
    docs
)

docs = add_metadata(
    docs
)

chunks, embeddings = (
    create_chunks(docs)
)

with open("bm25_chunks.pkl", "wb") as f:
    pickle.dump(chunks, f)

vector_store = (
    build_vector_store(
        chunks,
        embeddings
    )
)

print(
    "Qdrant Index Created"
)
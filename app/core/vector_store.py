from app.ingestion.chunker import (
    get_embeddings
)

from app.ingestion.vectorstore import (
    load_vector_store
)

embeddings = get_embeddings()

vector_store = load_vector_store(
    embeddings
)
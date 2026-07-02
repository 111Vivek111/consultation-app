# consultation-app Project Summary

## 1. Project Purpose

This repository implements a local retrieval-augmented generation application for consulting or policy-style document question answering. The system ingests documents from a knowledge folder, builds a Qdrant-backed vector index, rewrites user questions for better retrieval, retrieves and reranks relevant chunks, and streams an answer back to a browser client with source references.

The current implementation is centered on a single backend chat flow rather than a broader multi-endpoint platform. The most important runtime endpoint is `POST /chat-stream`, which returns server-sent events for live token delivery.

## 2. High-Level System Shape

The application has four practical layers:

1. Document ingestion and indexing.
2. Retrieval and generation orchestration in LangGraph.
3. A FastAPI backend that streams answers.
4. A minimal browser frontend that consumes the stream and renders markdown.

The project also includes Langfuse observability and a Docker Compose stack for the Langfuse dependencies.

## 3. Repository Layout

### Backend and orchestration

- `app/config.py` defines the LLMs, reranker, and Langfuse environment variables.
- `app/langfuse_client.py` creates the Langfuse callback handler.
- `app/api/main.py` exposes the FastAPI application and the streaming chat endpoint.
- `app/graph/state.py` defines the LangGraph state shape.
- `app/graph/nodes.py` contains query rewriting, retrieval, reranking, and generation logic.
- `app/graph/workflow.py` compiles the active LangGraph workflow.
- `app/graph/retrieval_graph.py` contains an older alternate graph implementation with overlapping logic.
- `app/evaluation/judges.py` provides LLM-based evaluation helpers for faithfulness and relevance.

### Ingestion and indexing

- `build_index.py` runs the indexing pipeline end to end.
- `app/ingestion/loader.py` loads PDF and TXT documents.
- `app/ingestion/cleaner.py` normalizes and filters document content.
- `app/ingestion/metadata.py` adds lightweight metadata such as section labels.
- `app/ingestion/chunker.py` creates semantic chunks and embedding objects.
- `app/ingestion/vectorstore.py` writes and loads the Qdrant vector store.

### Frontend

- `frontend/index.html` is the page shell.
- `frontend/script.js` sends user questions to the backend and renders the streamed response.
- `frontend/style.css` provides the basic visual styling.

### Data and infrastructure

- `knowladge/` is the document source folder used by indexing. The folder name is misspelled in the repository and in the code.
- `qdrant_data/` stores the local Qdrant collection data.
- `docker-compose.yml` runs Langfuse and its backing services.

## 4. Ingestion Pipeline

The indexing entry point is `build_index.py`. Its execution order is simple and linear:

1. Load documents from `knowladge/`.
2. Clean the extracted text.
3. Add metadata.
4. Create semantic chunks.
5. Persist the chunks and embeddings into Qdrant.

### 4.1 Document loading

`app/ingestion/loader.py` scans the input directory with `os.listdir` and supports two file types:

- PDF files are loaded through `PDFPlumberLoader`.
- TXT files are loaded through `TextLoader` with UTF-8 encoding.

Loaded documents are returned as LangChain `Document` objects. The loader prints the number of loaded documents.

### 4.2 Cleaning

`app/ingestion/cleaner.py` normalizes whitespace and removes some recurring noise patterns.

Behavior includes:

- collapsing repeated newlines to a single newline;
- collapsing all whitespace runs to a single space;
- removing page-number text matching `Page <number>`;
- filtering out documents whose content contains any of the ignore terms `table of contents`, `copyright`, `all rights reserved`, or `confidential`.

This means the pipeline is intentionally opinionated and discards pages that look like boilerplate.

### 4.3 Metadata

`app/ingestion/metadata.py` extracts a lightweight section label from the first few lines of each document chunk candidate. The logic treats the first short line as a probable section heading and falls back to `Unknown Section`.

It also ensures TXT-derived documents have a `page` field set to `N/A` so downstream citation formatting does not fail on missing page metadata.

### 4.4 Chunking and embeddings

`app/ingestion/chunker.py` creates embeddings with `HuggingFaceEmbeddings` using `all-MiniLM-L6-v2` and then applies `SemanticChunker` from `langchain_experimental`.

Important details:

- The chunker is semantic rather than fixed-size token splitting.
- Each chunk receives a `chunk_id` metadata field.
- The function returns both the chunk list and the embedding model instance.

### 4.5 Vector store

`app/ingestion/vectorstore.py` uses `QdrantVectorStore.from_documents` to create a local collection stored under `./qdrant_data`.

Key characteristics:

- Collection name: `policy_manuals`.
- Storage is file-based and local, not a remote Qdrant server.
- `load_vector_store` rebuilds a client from `QdrantClient(path="./qdrant_data")` and reattaches the embedding model for retrieval.

## 5. Runtime Retrieval and Generation

The active runtime graph is compiled in `app/graph/workflow.py`. It has three explicit nodes:

1. `rewrite`
2. `retrieve`
3. `rerank`

The current workflow ends after reranking. Generation is handled separately in `app/api/main.py` during the streaming endpoint execution rather than as a LangGraph node.

### 5.1 State schema

`app/graph/state.py` defines the graph state with these fields:

- `query`
- `rewritten_query`
- `documents`
- `reranked_documents`
- `context`
- `answer`
- `sources`

The actual runtime also passes `chat_history` through the state dictionary even though it is not explicitly listed in the typed dict.

### 5.2 Query rewriting

`rewrite_query_node` in `app/graph/nodes.py` rewrites the user question using the last three turns of chat history.

Current behavior:

- It concatenates the most recent history messages into a plain-text context block.
- It asks the rewrite model to convert the question into a standalone query.
- The prompt explicitly instructs the model to resolve pronouns like “it”, “that”, “those”, “this”, and “they”.
- The rewritten text is printed and returned as `rewritten_query`.

There is also an older variant in `app/graph/retrieval_graph.py` with a slightly different prompt that frames rewriting as conditional on whether the query is answerable from context. That file is not the compiled workflow used by `app/api/main.py`.

### 5.3 Retrieval

`retrieve_node` uses the Qdrant retriever with `k=8` and fetches documents based on the rewritten query.

The retriever is built from the local vector store loaded at module import time.

### 5.4 Reranking

`rerank_node` scores the retrieved documents using the `cross-encoder/ms-marco-MiniLM-L-6-v2` model.

Implementation details:

- Query-document pairs are created from the rewritten query and each document chunk.
- Scores are produced by `reranker.predict`.
- Documents are sorted by score descending.
- Only the top two documents are kept as `reranked_documents`.

This means the final generation context is intentionally narrow and constrained to the strongest matches.

## 6. Answer Generation and Streaming

The actual answer generation happens in `app/api/main.py` inside the `POST /chat-stream` endpoint.

### 6.1 Backend application

The FastAPI app is named `RAG Knowledge Assistant` and has CORS configured with a permissive `allow_origins=["*"]` policy.

The root endpoint `GET /` returns a simple health payload:

- `status: running`
- `service: RAG Knowledge Assistant`

### 6.2 Streaming endpoint

`POST /chat-stream` accepts a JSON body with one field:

- `query: str`

Request processing flow:

1. The graph is invoked with the query and the current in-memory chat history.
2. The reranked documents are extracted from the graph state.
3. A prompt is built with `app/utils/prompt_builder.py`.
4. The answer model is streamed token by token.
5. Each token is emitted as a server-sent event with type `token`.
6. After completion, a `sources` event is emitted.
7. The global `chat_history` list is updated with the user query and final answer.

### 6.3 Prompt construction

`app/utils/prompt_builder.py` builds a strict context-grounded prompt with these constraints:

- only answer from the supplied context;
- do not use outside knowledge;
- do not guess;
- if information is missing, say `I could not find this information in the documents.`;
- use headings and bullet points;
- avoid markdown tables.

The prompt also includes the last three turns of chat history and the concatenated content of the retrieved documents.

### 6.4 LLM configuration

`app/config.py` defines the main LLM and rewrite LLM:

- `llm` uses OpenRouter via `https://openrouter.ai/api/v1` and model `openai/gpt-oss-20b:free`.
- `llm_rewrite` uses Groq via `https://api.groq.com/openai/v1` and model `llama-3.1-8b-instant`.
- `judge_llm` is also configured against OpenRouter with the same GPT-OSS 20B family.
- `reranker` is `CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")`.

The main generation model is configured with `temperature=0` and `max_tokens=200`, which keeps answers short and deterministic.

## 7. Citation Handling

The current streamed endpoint does not use a separate citation node from the graph. Instead, it extracts source metadata directly from the reranked documents inside the API layer.

Each source entry contains:

- `source`
- `page`

Those sources are emitted as the final SSE event and are also rendered by the frontend.

## 8. Observability

Langfuse is integrated through `app/langfuse_client.py` and `langfuse.get_client()` in the API layer.

The endpoint wraps generation in a `start_as_current_observation` span named `HR-RAG-generator`.

Recorded metadata includes:

- the original query;
- the retrieved context;
- source metadata;
- the generated answer.

This makes the project suitable for trace inspection, prompt debugging, and generation analysis in the Langfuse UI.

## 9. Evaluation Utilities

`app/evaluation/judges.py` contains helper functions for scoring answers with an LLM:

- `evaluate_faithfulness(llm, question, context, answer)` checks whether the answer is supported by the retrieved context.
- `evaluate_answer_relevance(llm, question, answer)` checks whether the answer addresses the question.

Both helpers ask the model to return only a numeric score between 0.0 and 1.0, then extract the first decimal number from the response.

These evaluators exist as utilities, but the current streaming endpoint does not call them automatically.

## 10. Frontend Behavior

The browser UI is intentionally minimal and uses plain HTML, CSS, and vanilla JavaScript.

### 10.1 Layout

`frontend/index.html` contains:

- a page title;
- a chat container;
- a text input for the question;
- a send button;
- Marked.js loaded from a CDN for markdown rendering.

### 10.2 Chat flow

`frontend/script.js`:

- reads the input field;
- appends the user message to the chat window;
- sends the query to `http://127.0.0.1:8000/chat-stream`;
- reads the SSE response stream with `ReadableStream.getReader()`;
- updates the assistant message incrementally as tokens arrive;
- renders markdown through `marked.parse`;
- appends the final source list when the `sources` event arrives.

This is a direct browser-to-backend flow and does not use a frontend framework.

### 10.3 Styling

`frontend/style.css` provides a basic light UI with:

- Arial typography;
- a centered container;
- a white chat panel;
- simple right-aligned user messages;
- simple left-aligned assistant messages;
- a compact input row.

## 11. Infrastructure

`docker-compose.yml` is dedicated to the Langfuse stack, not the RAG app itself.

Services defined there include:

- `langfuse-web`
- `langfuse-worker`
- `postgres`
- `redis`
- `clickhouse`
- `minio`

The configuration exposes Langfuse on port 3000 and MinIO on port 9090, with most other ports bound to localhost only.

## 12. Data Storage and Runtime State

Important storage locations and runtime behaviors:

- `qdrant_data/` persists the local vector store.
- `chat_history` is an in-memory Python list inside `app/api/main.py`.
- The in-memory history is capped conceptually by `MAX_HISTORY = 20`, though the current endpoint does not enforce trimming yet.

This means conversations are not durable across process restarts and are shared within the running Python process.

## 13. Notable Implementation Characteristics

This repository has a few important practical traits worth remembering:

- The app is optimized for local or developer-machine use rather than multi-user production deployment.
- The retrieval graph is intentionally small and simple.
- The answer path is streaming-first and UI-friendly.
- The main answer model is constrained to short outputs with source references.
- The vector store is local on disk, which makes rebuilding the index easy but ties the system to the local environment.
- There is a duplicate/legacy graph module in `app/graph/retrieval_graph.py`; the active workflow is defined in `app/graph/workflow.py`.

## 14. End-to-End Data Flow

1. Add documents to `knowladge/`.
2. Run `python build_index.py` to rebuild `qdrant_data/`.
3. Start the FastAPI app.
4. Open the frontend page.
5. Enter a question.
6. The backend rewrites the query, retrieves documents, reranks them, and streams the answer.
7. The frontend renders the response and sources.
8. Langfuse records the run for inspection.

## 15. Quick Operational Commands

- Build the index: `python build_index.py`
- Run the backend: `uvicorn app.api.main:app --reload`
- Serve the frontend: `cd frontend && python -m http.server 8080`
- Start Langfuse and supporting services: `docker compose up`

## 16. Concise Takeaway

This project is a local RAG consultation assistant with a semantic chunking and Qdrant retrieval pipeline, a LangGraph-powered rewrite/retrieve/rerank flow, a streaming FastAPI endpoint, a minimal browser UI, and Langfuse observability. The current code favors clarity, local development, and traceable answer generation over production-scale complexity.

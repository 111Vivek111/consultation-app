# LangFuse RAG (Retrieval-Augmented Generation) Project Summary

## Project Overview

This is a **Retrieval-Augmented Generation (RAG) Knowledge Assistant** that combines LangGraph orchestration, vector-based retrieval (Qdrant), and LLM-powered generation with comprehensive observability through Langfuse. The system processes user queries through a multi-stage pipeline to retrieve relevant documents, generate contextual answers, and evaluate response quality.

**Purpose:** Answer user questions based on knowledge base documents (PDFs/TXT files) using intelligent retrieval and generation powered by LLMs.

---

## Architecture Components

### 1. **Vector Database (Qdrant)**
- Stores chunked documents as embeddings
- Location: `qdrant_data/`
- Collection: `policy_manuals`
- Enables semantic search for document retrieval

### 2. **Knowledge Base**
- Location: `knowladge/` (note: folder name has typo)
- Supported formats: PDF, TXT files
- Content: Policy manuals and documentation

### 3. **LLM Providers (OpenRouter)**
- **Main LLM**: OpenAI GPT-OSS 120B (for answering questions)
- **Rewrite LLM**: OpenAI GPT-OSS 120B (for query enhancement)
- **Judge LLM**: OpenAI GPT-OSS 20B (for evaluation)
- **Reranker**: CrossEncoder (ms-marco-MiniLM-L-6-v2)

### 4. **Observability Stack (Langfuse)**
- Tracks all LLM calls and pipeline execution
- Stores traces, spans, and metrics
- Docker services: PostgreSQL, Redis, ClickHouse, MinIO

### 5. **API Layer (FastAPI)**
- REST endpoint: `POST /chat`
- Health check: `GET /`
- CORS enabled for frontend communication

### 6. **Frontend**
- Location: `frontend/`
- Files: `index.html`, `script.js`, `style.css`
- Serves as user interface for querying the RAG system

---

## Complete Workflow

### **PHASE 1: INDEX BUILDING** (`build_index.py`)

This phase prepares the knowledge base for retrieval. Run once or when knowledge base changes.

```
build_index.py execution flow:
```

#### Step 1: Document Loading (`loader.py`)
- Scans `knowladge/` folder for PDF and TXT files
- Loads documents using LangChain loaders:
  - `PDFPlumberLoader` → extracts text from PDFs
  - `TextLoader` → reads TXT files with UTF-8 encoding
- **Output**: List of Document objects with `page_content` and metadata

#### Step 2: Document Cleaning (`cleaner.py`)
- Removes noise, special characters, and formatting artifacts
- Normalizes text (whitespace, line breaks)
- Handles encoding issues
- **Output**: Cleaned documents ready for chunking

#### Step 3: Metadata Enrichment (`metadata.py`)
- Adds metadata to documents (source filename, page number, etc.)
- Preserves document context for citations
- **Output**: Documents with enhanced metadata fields

#### Step 4: Document Chunking (`chunker.py`)
- Splits documents into manageable chunks (semantic units)
- Generates embeddings for each chunk using sentence-transformers
- Handles overlap to maintain context continuity
- **Output**: Chunks + corresponding embeddings

#### Step 5: Vector Store Creation (`vectorstore.py`)
- Stores chunks and embeddings in Qdrant vector database
- Creates `policy_manuals` collection
- Indexes for fast semantic search
- **Output**: Qdrant index ready for retrieval

**Result**: `qdrant_data/` folder populated with indexed documents

---

### **PHASE 2: RUNTIME QUERY PROCESSING** (`/chat` endpoint)

Each user query goes through a 5-node LangGraph pipeline:

```
User Query → [Rewrite] → [Retrieve] → [Rerank] → [Generate] → [Cite] → Answer
```

#### Node 1: Query Rewriting (`rewrite_query_node`)
- **Purpose**: Enhance user query for better retrieval
- **Input**: User query + chat history (last 3 messages)
- **Process**:
  - Analyzes conversation context
  - Rewrites query into clear, self-contained search terms
  - Uses LLM (`llm_rewrite`) for intelligent rewriting
- **Output**: Optimized query string
- **Example**: "What about the new policy?" → "New company policy updates and changes"

#### Node 2: Document Retrieval (`retrieve_node`)
- **Purpose**: Find relevant documents from knowledge base
- **Input**: Rewritten query
- **Process**:
  - Converts query to embeddings using same encoder as index
  - Performs semantic search in Qdrant
  - Retrieves top-k (8) documents with highest similarity scores
  - Preserves document metadata for citations
- **Output**: List of relevant documents with scores

#### Node 3: Relevance Reranking (`rerank_node`)
- **Purpose**: Refine document order by relevance
- **Input**: Retrieved documents
- **Process**:
  - Uses CrossEncoder model to score document-query pairs
  - Reorders documents by predicted relevance
  - Filters low-scoring documents if needed
  - More sophisticated than vector similarity alone
- **Output**: Re-ranked document list

#### Node 4: Answer Generation (`generate_node`)
- **Purpose**: Generate contextual answer from documents
- **Input**: Query + reranked documents
- **Process**:
  - Constructs prompt with:
    - System instructions for helpful, accurate responses
    - Reranked documents as context
    - User query
  - Calls main LLM (`llm`) to generate answer
  - Temperature = 0 (deterministic output)
- **Output**: Generated answer string

#### Node 5: Citation Addition (`citation_node`)
- **Purpose**: Add source references to answer
- **Input**: Generated answer + source documents
- **Process**:
  - Extracts document sources from metadata
  - Adds citations to answer (document names, page numbers)
  - Provides transparency on answer origins
- **Output**: Answer with citations

---

### **PHASE 3: ANSWER EVALUATION**

After answer generation, automatic quality evaluation occurs:

#### Faithfulness Evaluation
- **Question**: "Is the answer grounded in provided context?"
- **Process**: Judge LLM evaluates if answer doesn't contradict retrieved documents
- **Output**: Faithfulness score (0-1)
- **Function**: `evaluate_faithfulness()` in `evaluation/judges.py`

#### Answer Relevance Evaluation
- **Question**: "Does the answer address the user's query?"
- **Process**: Judge LLM assesses if answer answers what was asked
- **Output**: Relevance score (0-1)
- **Function**: `evaluate_answer_relevance()` in `evaluation/judges.py`

---

### **PHASE 4: OBSERVABILITY & LOGGING** (Langfuse)

All pipeline events are tracked:

- **Trace ID**: Generated for each `/chat` request
- **Callbacks**: `LangfuseCallbackHandler` captures:
  - LLM calls (tokens, latency, model)
  - Retrieval operations
  - Node execution times
  - Evaluation results
- **Stored in**: Langfuse database (PostgreSQL backend)
- **Accessible via**: Langfuse web dashboard (port 3000)

---

## Data Flow Summary

```
USER QUERY
    ↓
┌─────────────────────────────────────────┐
│        RUNTIME PIPELINE                  │
├─────────────────────────────────────────┤
│ 1. Query Rewrite (LLM enhancement)      │
│ 2. Vector Search (Qdrant retrieval)     │
│ 3. Reranking (CrossEncoder refinement)  │
│ 4. Generation (LLM answer creation)     │
│ 5. Citation (Source attribution)        │
└─────────────────────────────────────────┘
    ↓
EVALUATION
├── Faithfulness Score (Judge LLM)
└── Answer Relevance Score (Judge LLM)
    ↓
RESPONSE TO USER
├── Answer with Citations
├── Evaluation Metrics
└── Trace ID (for monitoring)
    ↓
LANGFUSE OBSERVABILITY
└── Logged in database for analysis
```

---

## Technology Stack

### **Core Libraries**
- **LangGraph**: Workflow orchestration (nodes + edges)
- **LangChain**: Document loading, vector operations, LLM interfaces
- **FastAPI**: REST API framework
- **Pydantic**: Request/response validation
- **Qdrant**: Vector database
- **sentence-transformers**: Embedding generation & reranking
- **PDFPlumber**: PDF text extraction

### **LLM & AI**
- **OpenRouter API**: Access to open-source LLMs
- **GPT-OSS Models**: Inference engines

### **Observability**
- **Langfuse**: Tracing and monitoring
- **CallbackHandler**: Integrated tracking

### **Infrastructure**
- **Docker**: Containerization (docker-compose)
- **PostgreSQL**: Langfuse database
- **Redis**: Caching layer
- **ClickHouse**: Analytics database
- **MinIO**: S3-compatible object storage

### **Frontend**
- **HTML/CSS/JavaScript**: Static web interface
- **HTTP Server**: Simple file serving (port 8080)

---

## File Structure & Responsibilities

```
lang_fuse/
├── build_index.py              # INDEX BUILDING ORCHESTRATION
├── docker-compose.yml          # INFRASTRUCTURE SETUP
├── test.ipynb                  # TESTING & EXPERIMENTATION
│
├── app/
│   ├── config.py               # CONFIGURATION & LLM INSTANCES
│   ├── langfuse_client.py      # OBSERVABILITY SETUP
│   │
│   ├── api/
│   │   └── main.py             # FASTAPI ENDPOINTS (/chat, /)
│   │
│   ├── graph/
│   │   ├── state.py            # GRAPH STATE SCHEMA (GraphState class)
│   │   ├── nodes.py            # 5-NODE PIPELINE LOGIC
│   │   └── workflow.py         # LANGGRAPH COMPILATION
│   │
│   ├── ingestion/
│   │   ├── loader.py           # DOCUMENT LOADING (PDF, TXT)
│   │   ├── cleaner.py          # TEXT CLEANING
│   │   ├── metadata.py         # METADATA ENRICHMENT
│   │   ├── chunker.py          # DOCUMENT CHUNKING & EMBEDDINGS
│   │   └── vectorstore.py      # QDRANT INDEX CREATION
│   │
│   └── evaluation/
│       └── judges.py           # QUALITY EVALUATION FUNCTIONS
│
├── frontend/
│   ├── index.html              # WEB INTERFACE
│   ├── script.js               # CHAT INTERACTION LOGIC
│   └── style.css               # STYLING
│
├── knowladge/                  # KNOWLEDGE BASE (PDFs, TXTs)
├── qdrant_data/                # VECTOR DATABASE STORAGE
└── PROJECT_SUMMARY.md          # THIS FILE
```

---

## Quick Start Commands

### 1. Build Index
```bash
python build_index.py
```
**When to run**: First setup or when knowledge base changes

### 2. Start Backend API
```bash
uvicorn app.api.main:app --reload
```
**Runs on**: http://localhost:8000

### 3. Start Frontend Server
```bash
cd frontend
python -m http.server 8080
```
**Runs on**: http://localhost:8080

### 4. Start Langfuse Stack
```bash
docker compose up
```
**Services**:
- Langfuse Dashboard: http://localhost:3000
- MinIO: http://localhost:9090

---

## Key Configuration Files

- **`.env`**: Environment variables (API keys, database URLs)
- **`docker-compose.yml`**: Service definitions and dependencies
- **`app/config.py`**: LLM model selection and parameters
- **`app/graph/state.py`**: Data schema for pipeline state

---

## Performance & Monitoring

### Metrics Tracked
- **Query Processing Time**: Total end-to-end latency
- **Retrieval Performance**: Document relevance and ranking
- **LLM Metrics**: Token usage, generation time, cost
- **Quality Scores**: Faithfulness and answer relevance
- **Error Rates**: API failures and pipeline issues

### Langfuse Dashboard Features
- View trace timelines for each query
- Analyze LLM call details (prompts, completions)
- Monitor token usage and costs
- Track evaluation metrics over time

---

## Common Workflows

### Updating Knowledge Base
1. Add PDF/TXT files to `knowladge/` folder
2. Run `python build_index.py`
3. Restart API: `uvicorn app.api.main:app --reload`

### Testing New LLM Model
1. Update `config.py` with new model name
2. Restart API
3. Send test query to `/chat`
4. Monitor Langfuse traces for performance

### Debugging Query Issues
1. Check Langfuse dashboard for trace details
2. Review evaluation scores (Faithfulness/Relevance)
3. Inspect retrieved documents in trace
4. Modify reranking threshold if needed

---

## Summary

This RAG system provides:
- ✅ Intelligent document retrieval using vector embeddings
- ✅ Context-aware query enhancement
- ✅ Relevance reranking for better results
- ✅ Citation-based answer generation
- ✅ Automatic quality evaluation
- ✅ Full observability and monitoring
- ✅ Scalable architecture with vector database

The pipeline balances retrieval accuracy, generation quality, and operational observability to deliver reliable answers from domain-specific knowledge bases.

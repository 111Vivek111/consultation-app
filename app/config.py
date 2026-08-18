import os

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI


import cohere


load_dotenv()

# LLM used for answering

llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model_name="openai/gpt-oss-20b:free",
    temperature=0,
    max_tokens=200
)

# LLM used for query rewriting

llm_rewrite = ChatOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.1-8b-instant",
    temperature=0
)

# Reranker

# reranker = CrossEncoder(
#     "cross-encoder/ms-marco-MiniLM-L-6-v2"
# )


COHERE_API_KEY = os.getenv("COHERE_API_KEY")

if not COHERE_API_KEY:
    raise RuntimeError("COHERE_API_KEY is not set")

reranker = cohere.Client(
    api_key=COHERE_API_KEY
)

judge_llm = ChatOpenAI(
    model="openai/gpt-oss-20b:free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0
)


LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST")


QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY=os.getenv("QDRANT_API_KEY")

QDRANT_COLLECTION_NAME=os.getenv("QDRANT_COLLECTION_NAME")

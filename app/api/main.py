
import json

from app.utils.prompt_builder import build_prompt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from time import time
from fastapi.middleware.cors import CORSMiddleware
from app.graph.workflow import app_graph
from langfuse import get_client
from app.config import judge_llm
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
from app.config import llm
from app.langfuse_client import langfuse_handler
from fastapi import Depends
from sqlalchemy.orm import Session
from app.auth.hashing import verify_password
from app.schemas.auth import LoginRequest
from app.database.database import get_db
from app.database.user_repository import UserRepository
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    SignupRequest,
    AuthResponse
)

from app.auth.hashing import hash_password
from app.auth.jwt import create_access_token
from app.session_manager import (
    get_history,
    add_message
)

langfuse = get_client()

app = FastAPI(
    title="RAG Knowledge Assistant",
    description="LangGraph + Qdrant + FastAPI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)
# In-memory conversation history


class QueryRequest(BaseModel):
    query: str


@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "RAG Knowledge Assistant"
    }

from app.evaluation.judges import (
    evaluate_faithfulness,
    evaluate_answer_relevance
)

@app.post(
    "/signup",
    response_model=AuthResponse
)
def signup(
    request: SignupRequest,
    db: Session = Depends(get_db)
):

    existing = UserRepository.get_by_email(
        db,
        request.email
    )

    if existing:

        raise HTTPException(
            status_code=409,
            detail="Email already exists."
        )

    hashed = hash_password(
        request.password
    )

    user = UserRepository.create(
        db,
        request.full_name,
        request.email,
        hashed
    )

    token = create_access_token(
        user_id=str(user.id),
        email=user.email
    )

    return AuthResponse(
        access_token=token,
        user=user
    )

@app.post(
    "/login",
    response_model=AuthResponse
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    user = UserRepository.get_by_email(
        db,
        request.email
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    if not verify_password(
        request.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    token = create_access_token(
        user_id=str(user.id),
        email=user.email
    )

    return AuthResponse(
        access_token=token,
        user=user
    )

@app.post("/chat-stream")
async def chat_stream(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    history = get_history(
        str(current_user.id)
    )

    state = app_graph.invoke(
        {
            "query": request.query,
            "chat_history": history
        },
        config={
            "callbacks": [langfuse_handler],
            "run_name": "HR-RAG-Streaming"
        }
    )

    docs = state["reranked_documents"]
    context = "\n\n".join(doc.page_content for doc in docs)
    sources = [
        {"source": doc.metadata.get("source"), "page": doc.metadata.get("page")}
        for doc in docs
    ]
    prompt = build_prompt(
        request.query,
        docs,
        history
    )

    async def token_generator():
        answer = ""

        # ✅ Use a named span — the evaluator will filter by this name
        with langfuse.start_as_current_observation(
            as_type="generation",
            name="HR-RAG-generator",      # <-- you'll filter on this name in UI
            input={                        # <-- maps to {{input}} in evaluator
                "query": request.query,
                "context": context
            },
            metadata={"sources": sources}
        ) as gen_span:

            async for chunk in llm.astream(prompt):
                if not chunk.content:
                    continue
                answer += chunk.content
                yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"

            # ✅ Set output after streaming completes — maps to {{output}}
            gen_span.update(output=answer)

        yield f"data: {json.dumps({'type': 'sources', 'content': sources})}\n\n"

        add_message(
            str(current_user.id),
            "user",
            request.query
        )

        add_message(
            str(current_user.id),
            "assistant",
            answer
        )



    return StreamingResponse(token_generator(), media_type="text/event-stream")
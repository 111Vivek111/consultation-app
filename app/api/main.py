
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
from sqlalchemy.orm import Session
from fastapi import Depends
from app.schemas.message import MessageResponse
from app.database.conversation_repository import ConversationRepository
from app.schemas.conversation import (
    ConversationResponse,
    ConversationListResponse
)
from app.utils.source_formatter import (
    format_sources
)


from app.auth.hashing import hash_password
from app.auth.jwt import create_access_token
from app.database.message_repository import MessageRepository
from app.schemas.document import DocumentResponse
from app.database.document_repository import DocumentRepository
from app.schemas.document import (
    UploadResponse
)
from app.ingestion.loader import (
    load_single_document
)
from app.ingestion.chunker import (
    create_chunks
)

from pathlib import Path
from fastapi import UploadFile, File
from pathlib import Path

from app.core.vector_store import vector_store
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue
)
from app.database.document_repository import (
    DocumentRepository
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

UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(
    exist_ok=True
)

from uuid import UUID

class QueryRequest(BaseModel):
    conversation_id: UUID
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

@app.get(
    "/documents",
    response_model=list[DocumentResponse]
)
def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return DocumentRepository.get_user_documents(
        db=db,
        user_id=current_user.id
    )

@app.post(
    "/documents/upload",
    response_model=UploadResponse
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    allowed_extensions = {
        ".pdf",
        ".txt",
        ".docx"
    }

    extension = (
        Path(file.filename)
        .suffix
        .lower()
    )

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail="Unsupported file type"
        )

    file_path = (
        UPLOAD_DIR /
        file.filename
    )

    with open(
        file_path,
        "wb"
    ) as buffer:

        content = await file.read()

        buffer.write(content)

    document = (
        DocumentRepository.create(
            db=db,
            user_id=current_user.id,
            filename=file.filename,
            file_type=extension.replace(".", "")
        )
    )
    print("\n========== UPLOAD ==========")
    print("Current User ID :", current_user.id)
    print("Type :", type(current_user.id))
    print("============================\n")

    docs = load_single_document(
        str(file_path)
    )

    chunks, embeddings = create_chunks(
        documents=docs,
        user_id=current_user.id,
        document_id=document.id,
        document_name=file.filename
    )
    for chunk in chunks:

        print(chunk.metadata)
    from app.core.vector_store import (
        vector_store
    )
    vector_store.add_documents(
        chunks
    )
    print(document.id)
    return UploadResponse(
        message="Document uploaded successfully",
        document_id=str(document.id),
        filename=file.filename
    )

@app.delete(
    "/documents/{document_id}"
)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    document = (
        DocumentRepository.get_by_id(
            db,
            document_id
        )
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if document.user_id != current_user.id:

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    # Delete vectors from Qdrant
    vector_store.client.delete(
        collection_name="policy_manuals",
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(
                        value=str(document.id)
                    )
                )
            ]
        )
    )

    # Delete physical file
    file_path = (
        UPLOAD_DIR /
        document.filename
    )

    if file_path.exists():

        file_path.unlink()

    # Delete database row
    DocumentRepository.delete(
        db,
        document
    )

    return {
        "message":
        "Document deleted successfully"
    }


@app.post(
    "/conversation",
    response_model=ConversationResponse
)
def create_conversation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    conversation = ConversationRepository.create(
        db=db,
        user_id=current_user.id
    )

    return conversation

@app.get(
    "/conversations",
    response_model=list[ConversationListResponse]
)
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    conversations = (
        ConversationRepository.get_user_conversations(
            db=db,
            user_id=current_user.id
        )
    )

    return conversations

@app.get(
    "/conversation/{conversation_id}",
    response_model=list[MessageResponse]
)
def get_conversation_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    conversation = (
        ConversationRepository.get_user_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
    )

    if conversation is None:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    return MessageRepository.get_messages(
        db=db,
        conversation_id=conversation_id
    )


@app.post("/chat-stream")
async def chat_stream(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = ConversationRepository.get_user_conversation(
        db=db,
        conversation_id=request.conversation_id,
        user_id=current_user.id
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )
    history = MessageRepository.get_history(
        db=db,
        conversation_id=request.conversation_id
    )

    state = app_graph.invoke(
        {
            "user_id": str(current_user.id),

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

    sources = format_sources(docs)
    prompt = build_prompt(
        request.query,
        docs,
        history
    )

    async def token_generator():
        answer = ""
        try:
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="HR-RAG-generator",
                input={"query": request.query, "context": context},
                metadata={"sources": sources}
            ) as gen_span:
                async for chunk in llm.astream(prompt):
                    if not chunk.content:
                        continue
                    answer += chunk.content
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"

                try:
                    gen_span.update(output=answer)
                except Exception as e:
                    print("Langfuse span update failed:", e)
        except Exception as e:
            print("Streaming/tracing error:", e)

        # ALWAYS send sources, regardless of what happened above
        yield f"data: {json.dumps({'type': 'sources', 'content': sources})}\n\n"
        if conversation.title == "New Chat":

            ConversationRepository.update_title(
                db=db,
                conversation_id=request.conversation_id,
                title=request.query[:50]
            )
        MessageRepository.add_message(
            db=db,
            conversation_id=request.conversation_id,
            role="user",
            content=request.query
        )

        MessageRepository.add_message(
            db=db,
            conversation_id=request.conversation_id,
            role="assistant",
            content=answer
        )



    return StreamingResponse(token_generator(), media_type="text/event-stream")

@app.delete(
    "/conversation/{conversation_id}"
)
def delete_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    conversation = (
        ConversationRepository.get_user_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
    )

    if conversation is None:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    ConversationRepository.delete(
        db=db,
        conversation_id=conversation_id
    )

    return {
        "message":
        "Conversation deleted successfully"
    }
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import Document
from .schemas import ChatRequest, ChatResponse, DocumentCreate, DocumentRead


SEED_DOCUMENTS = [
    {
        "title": "浮空器基础概念占位文档",
        "category": "基础知识",
        "status": "seed",
        "filename": "aerostat-basics-placeholder.md",
        "source_type": "seed",
        "chunk_count": 0,
    },
    {
        "title": "系留气球应用场景占位文档",
        "category": "应用场景",
        "status": "seed",
        "filename": "tethered-balloon-use-cases-placeholder.md",
        "source_type": "seed",
        "chunk_count": 0,
    },
    {
        "title": "飞行安全与维护占位文档",
        "category": "安全维护",
        "status": "seed",
        "filename": "flight-safety-maintenance-placeholder.md",
        "source_type": "seed",
        "chunk_count": 0,
    },
]


def init_database() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        has_documents = db.scalars(select(Document.id).limit(1)).first() is not None
        if has_documents:
            return

        db.add_all(Document(**document) for document in SEED_DOCUMENTS)
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(title="Aerostat Knowledge Site Backend", lifespan=lifespan)

DEV_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://100.122.3.8:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Basic service health endpoint for frontend connectivity checks."""
    return {"status": "ok"}


@app.get("/documents", response_model=list[DocumentRead])
def list_documents(db: Session = Depends(get_db)) -> list[Document]:
    """Return document metadata stored in SQLite."""
    return list(db.scalars(select(Document).order_by(Document.created_at.desc())))


@app.post(
    "/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db),
) -> Document:
    """Create a document metadata record without uploading a file."""
    db_document = Document(**document.model_dump())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


@app.get("/documents/{document_id}", response_model=DocumentRead)
def get_document(document_id: int, db: Session = Depends(get_db)) -> Document:
    """Return one document metadata record by id."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    """Return placeholder chat reply for minimal end-to-end flow."""
    question = request.question.strip()
    if question:
        reply = f"已收到你的问题：“{question}”。当前问答仍为占位能力，尚未接入真实知识库检索。"
    else:
        reply = "当前问答仍为占位能力，请输入一个关于浮空器知识的问题。"

    return ChatResponse(reply=reply, sources=[])

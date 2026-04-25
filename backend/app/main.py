from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import Document
from .reconcile import reconcile_document_files
from .schemas import ChatRequest, ChatResponse, DocumentCreate, DocumentRead
from .storage import save_raw_document_file


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
    ensure_document_columns()

    with SessionLocal() as db:
        has_documents = db.scalars(select(Document.id).limit(1)).first() is not None
        if has_documents:
            return

        db.add_all(Document(**document) for document in SEED_DOCUMENTS)
        db.commit()


def ensure_document_columns() -> None:
    inspector = inspect(engine)
    if "documents" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("documents")}
    expected_columns = {
        "storage_path": "ALTER TABLE documents ADD COLUMN storage_path VARCHAR(500)",
        "file_ext": "ALTER TABLE documents ADD COLUMN file_ext VARCHAR(20)",
        "mime_type": "ALTER TABLE documents ADD COLUMN mime_type VARCHAR(100)",
        "file_size": "ALTER TABLE documents ADD COLUMN file_size INTEGER",
        "sha256": "ALTER TABLE documents ADD COLUMN sha256 VARCHAR(64)",
        "parse_status": (
            "ALTER TABLE documents ADD COLUMN parse_status "
            "VARCHAR(50) NOT NULL DEFAULT 'NOT_PARSED'"
        ),
        "parse_output_dir": "ALTER TABLE documents ADD COLUMN parse_output_dir VARCHAR(500)",
        "parsed_markdown_path": (
            "ALTER TABLE documents ADD COLUMN parsed_markdown_path VARCHAR(500)"
        ),
        "parse_error": "ALTER TABLE documents ADD COLUMN parse_error VARCHAR(1000)",
    }

    with engine.begin() as connection:
        for column_name, statement in expected_columns.items():
            if column_name not in column_names:
                connection.execute(text(statement))


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


@app.post(
    "/documents/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Document:
    """Store a raw .txt, .md, or .pdf file and create document metadata."""
    saved_file = save_raw_document_file(file)
    title = saved_file.storage_path.stem

    db_document = Document(
        title=title,
        category="未分类",
        status="UPLOADED",
        filename=saved_file.original_filename,
        storage_path=str(saved_file.storage_path),
        file_ext=saved_file.file_ext,
        mime_type=saved_file.mime_type,
        file_size=saved_file.file_size,
        sha256=saved_file.sha256,
        source_type="upload",
        chunk_count=0,
        parse_status="NOT_PARSED",
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


@app.get("/admin/reconcile/dry-run")
def reconcile_dry_run(db: Session = Depends(get_db)) -> dict[str, list[dict]]:
    """Check database file references against local storage without modifying data."""
    return reconcile_document_files(db)


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

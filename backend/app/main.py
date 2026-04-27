from contextlib import asynccontextmanager
from pathlib import Path
import shutil

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from .chunking import build_markdown_chunks
from .database import Base, SessionLocal, engine, get_db
from .mineru import get_document_output_dir
from .models import Document, DocumentChunk
from .parse_queue import enqueue_parse, start_parse_worker
from .reconcile import reconcile_document_files
from .schemas import (
    ChatRequest,
    ChatResponse,
    DocumentChunkRead,
    DocumentCreate,
    DocumentRead,
    ParseResult,
)
from .storage import save_raw_document_file


STALE_PARSE_ERROR = (
    "Parser task was interrupted by backend restart. Please submit parse again."
)

def init_database() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_document_columns()
    recover_stale_parse_tasks()


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
        "page_count": "ALTER TABLE documents ADD COLUMN page_count INTEGER",
        "sha256": "ALTER TABLE documents ADD COLUMN sha256 VARCHAR(64)",
        "parse_status": (
            "ALTER TABLE documents ADD COLUMN parse_status "
            "VARCHAR(50) NOT NULL DEFAULT 'NOT_PARSED'"
        ),
        "parse_output_dir": "ALTER TABLE documents ADD COLUMN parse_output_dir VARCHAR(500)",
        "parsed_markdown_path": (
            "ALTER TABLE documents ADD COLUMN parsed_markdown_path VARCHAR(500)"
        ),
        "parse_error_code": "ALTER TABLE documents ADD COLUMN parse_error_code VARCHAR(50)",
        "parse_error": "ALTER TABLE documents ADD COLUMN parse_error VARCHAR(1000)",
    }

    with engine.begin() as connection:
        for column_name, statement in expected_columns.items():
            if column_name not in column_names:
                connection.execute(text(statement))


def recover_stale_parse_tasks() -> None:
    with SessionLocal() as db:
        stale_documents = list(
            db.scalars(select(Document).where(Document.parse_status.in_(["QUEUED", "PARSING"])))
        )
        if not stale_documents:
            return

        for document in stale_documents:
            document.parse_status = "FAILED"
            document.parse_error_code = "INTERRUPTED"
            document.parse_error = STALE_PARSE_ERROR

        db.commit()


def cleanup_document_files(document: Document) -> None:
    if document.storage_path:
        storage_path = Path(document.storage_path).expanduser()
        if storage_path.is_file():
            storage_path.unlink()
            try:
                storage_path.parent.rmdir()
            except OSError:
                pass

    if document.parse_output_dir:
        parse_output_dir = Path(document.parse_output_dir).expanduser()
        if parse_output_dir.exists():
            shutil.rmtree(parse_output_dir)


def ensure_parsed_markdown_ready(document: Document) -> Path:
    if document.parse_status != "PARSED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must have parse_status PARSED before building chunks.",
        )

    if not document.parsed_markdown_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no parsed_markdown_path.",
        )

    markdown_path = Path(document.parsed_markdown_path).expanduser()
    if not markdown_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parsed Markdown file not found: {document.parsed_markdown_path}",
        )

    return markdown_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    start_parse_worker()
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
    return list(db.scalars(select(Document).order_by(Document.id.asc())))


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
        page_count=saved_file.page_count,
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


@app.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)) -> dict[str, int | str]:
    """Delete a document metadata record and its local raw/parse artifacts."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    cleanup_document_files(document)
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
    db.delete(document)
    db.commit()
    return {"status": "deleted", "id": document_id}


@app.post("/documents/{document_id}/parse", response_model=DocumentRead)
def parse_document(
    document_id: int,
    db: Session = Depends(get_db),
) -> Document:
    """Queue MinerU parsing for an uploaded PDF document."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.parse_status in {"QUEUED", "PARSING"}:
        return document

    if not document.storage_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no storage_path and cannot be parsed.",
        )

    storage_path = Path(document.storage_path).expanduser()
    if not storage_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Original file not found: {document.storage_path}",
        )

    file_ext = (document.file_ext or storage_path.suffix).lower()
    if file_ext != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents can be parsed by MinerU in this version.",
        )

    document.parse_status = "QUEUED"
    document.parse_output_dir = str(get_document_output_dir(document_id))
    document.parsed_markdown_path = None
    document.parse_error_code = None
    document.parse_error = None
    db.commit()
    db.refresh(document)

    enqueue_parse(document_id)
    return document


@app.get("/documents/{document_id}/parse-result", response_model=ParseResult)
def get_parse_result(document_id: int, db: Session = Depends(get_db)) -> ParseResult:
    """Return parsed Markdown content for a document when MinerU has produced it."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.parsed_markdown_path:
        raise HTTPException(status_code=404, detail="Parsed Markdown path not found")

    markdown_path = Path(document.parsed_markdown_path).expanduser()
    if not markdown_path.exists():
        raise HTTPException(status_code=404, detail="Parsed Markdown file not found")

    content = markdown_path.read_text(encoding="utf-8", errors="replace")
    return ParseResult(
        document_id=document.id,
        parsed_markdown_path=document.parsed_markdown_path,
        content=content,
    )


@app.post("/documents/{document_id}/chunks/build", response_model=DocumentRead)
def build_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
) -> Document:
    """Build SQLite chunks from a parsed Markdown artifact."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    markdown_path = ensure_parsed_markdown_ready(document)
    chunks = build_markdown_chunks(markdown_path)

    db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
    for chunk in chunks:
        db.add(
            DocumentChunk(
                document_id=document_id,
                chunk_index=chunk.chunk_index,
                heading_path=chunk.heading_path,
                heading_text=chunk.heading_text,
                content=chunk.content,
                char_count=chunk.char_count,
                token_estimate=chunk.token_estimate,
                source_path=chunk.source_path,
            )
        )

    document.chunk_count = len(chunks)
    db.commit()
    db.refresh(document)
    return document


@app.get("/documents/{document_id}/chunks", response_model=list[DocumentChunkRead])
def list_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
) -> list[DocumentChunk]:
    """Return chunks for a document ordered by chunk index."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return list(
        db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
    )


@app.delete("/documents/{document_id}/chunks")
def delete_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
) -> dict[str, int | str]:
    """Delete all chunks for a document and reset its chunk count."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    deleted_count = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).delete()
    document.chunk_count = 0
    db.commit()
    return {
        "status": "deleted",
        "document_id": document_id,
        "deleted_count": deleted_count,
    }


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

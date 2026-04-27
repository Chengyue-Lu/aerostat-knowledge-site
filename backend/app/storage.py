import hashlib
import mimetypes
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status


ALLOWED_DOCUMENT_EXTENSIONS = {".md", ".pdf", ".txt"}
DEFAULT_DOCS_RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "docs_raw"
READ_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class SavedRawDocument:
    original_filename: str
    storage_path: Path
    file_ext: str
    mime_type: str | None
    file_size: int
    page_count: int | None
    sha256: str


def get_docs_raw_dir() -> Path:
    configured_dir = os.getenv("DOCS_RAW_DIR")
    if configured_dir:
        return Path(configured_dir).expanduser().resolve()

    return DEFAULT_DOCS_RAW_DIR.resolve()


def validate_upload_filename(filename: str | None) -> str:
    if filename is None or not filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required.",
        )

    safe_name = Path(filename.replace("\\", "/")).name
    if not safe_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required.",
        )

    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_DOCUMENT_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Only {allowed} files are allowed.",
        )

    return safe_name


def count_pdf_pages(path: Path) -> int | None:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return len(reader.pages)
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["file", str(path)],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        result = None

    if result and result.returncode == 0:
        page_match = re.search(r",\s*(\d+)\s+pages?\b", result.stdout)
        if page_match:
            return int(page_match.group(1))

    try:
        content = path.read_bytes()
    except OSError:
        return None

    page_matches = re.findall(rb"/Type\s*/Page\b", content)
    return len(page_matches) if page_matches else None


def save_raw_document_file(file: UploadFile) -> SavedRawDocument:
    original_filename = validate_upload_filename(file.filename)
    file_ext = Path(original_filename).suffix.lower()
    document_dir = get_docs_raw_dir() / uuid4().hex
    document_dir.mkdir(parents=True, exist_ok=False)

    saved_path = document_dir / original_filename
    sha256_hash = hashlib.sha256()
    file_size = 0

    file.file.seek(0)
    with saved_path.open("wb") as output_file:
        while chunk := file.file.read(READ_CHUNK_SIZE):
            output_file.write(chunk)
            sha256_hash.update(chunk)
            file_size += len(chunk)

    guessed_mime_type = mimetypes.guess_type(original_filename)[0]
    mime_type = (
        file.content_type
        if file.content_type and file.content_type != "application/octet-stream"
        else guessed_mime_type or file.content_type
    )
    page_count = count_pdf_pages(saved_path) if file_ext == ".pdf" else None

    return SavedRawDocument(
        original_filename=original_filename,
        storage_path=saved_path,
        file_ext=file_ext,
        mime_type=mime_type,
        file_size=file_size,
        page_count=page_count,
        sha256=sha256_hash.hexdigest(),
    )

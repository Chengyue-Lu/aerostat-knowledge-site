from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Document
from .storage import get_docs_raw_dir


def _path_exists(path_value: str | None) -> bool:
    if not path_value:
        return True

    return Path(path_value).expanduser().exists()


def _resolved_path(path_value: str | None) -> str | None:
    if not path_value:
        return None

    return str(Path(path_value).expanduser().resolve())


def reconcile_document_files(db: Session) -> dict[str, list[dict[str, str | int | None]]]:
    documents = list(db.scalars(select(Document)))
    referenced_paths = {
        path
        for document in documents
        for path in (
            _resolved_path(document.storage_path),
            _resolved_path(document.parsed_markdown_path),
        )
        if path is not None
    }

    missing_files = []
    missing_parse_artifacts = []

    for document in documents:
        if document.storage_path and not _path_exists(document.storage_path):
            missing_files.append(
                {
                    "id": document.id,
                    "title": document.title,
                    "path": document.storage_path,
                }
            )

        if document.parsed_markdown_path and not _path_exists(document.parsed_markdown_path):
            missing_parse_artifacts.append(
                {
                    "id": document.id,
                    "title": document.title,
                    "path": document.parsed_markdown_path,
                }
            )

    docs_raw_dir = get_docs_raw_dir()
    orphan_files = []
    if docs_raw_dir.exists():
        for path in docs_raw_dir.rglob("*"):
            if not path.is_file():
                continue

            resolved_path = str(path.resolve())
            if resolved_path not in referenced_paths:
                orphan_files.append({"path": resolved_path})

    return {
        "missing_files": missing_files,
        "missing_parse_artifacts": missing_parse_artifacts,
        "orphan_files": orphan_files,
    }

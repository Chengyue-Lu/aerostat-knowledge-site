import os
import subprocess
from pathlib import Path

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Document


DEFAULT_MINERU_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "mineru_outputs"
DEFAULT_MINERU_TIMEOUT_SECONDS = 1800
MAX_PARSE_ERROR_LENGTH = 900


def get_mineru_bin() -> str:
    return os.getenv("MINERU_BIN", "mineru")


def get_mineru_backend() -> str | None:
    backend = os.getenv("MINERU_BACKEND")
    if backend and backend.strip():
        return backend.strip()

    return None


def get_mineru_output_root() -> Path:
    configured_dir = os.getenv("MINERU_OUTPUT_DIR")
    if configured_dir:
        return Path(configured_dir).expanduser().resolve()

    return DEFAULT_MINERU_OUTPUT_DIR.resolve()


def get_mineru_timeout_seconds() -> int:
    raw_timeout = os.getenv("MINERU_TIMEOUT_SECONDS")
    if not raw_timeout:
        return DEFAULT_MINERU_TIMEOUT_SECONDS

    try:
        timeout = int(raw_timeout)
    except ValueError:
        return DEFAULT_MINERU_TIMEOUT_SECONDS

    return timeout if timeout > 0 else DEFAULT_MINERU_TIMEOUT_SECONDS


def get_document_output_dir(document_id: int) -> Path:
    return get_mineru_output_root() / str(document_id)


def build_mineru_command(storage_path: Path, output_dir: Path) -> list[str]:
    command = [
        get_mineru_bin(),
        "-p",
        str(storage_path),
        "-o",
        str(output_dir),
    ]
    backend = get_mineru_backend()
    if backend:
        command.extend(["-b", backend])

    return command


def find_parsed_markdown(output_dir: Path) -> Path | None:
    markdown_files = sorted(path for path in output_dir.rglob("*.md") if path.is_file())
    if not markdown_files:
        return None

    return markdown_files[0]


def _truncate_error(message: str) -> str:
    compact_message = " ".join(message.split())
    if len(compact_message) <= MAX_PARSE_ERROR_LENGTH:
        return compact_message

    return f"{compact_message[:MAX_PARSE_ERROR_LENGTH]}..."


def _failure_message(prefix: str, stdout: str = "", stderr: str = "") -> str:
    details = stderr.strip() or stdout.strip()
    if details:
        return _truncate_error(f"{prefix}: {details}")

    return _truncate_error(prefix)


def _mark_failed(db: Session, document: Document, message: str, output_dir: Path) -> None:
    document.parse_status = "FAILED"
    document.parse_output_dir = str(output_dir)
    document.parse_error = _truncate_error(message)
    db.commit()


def run_mineru_parse(document_id: int) -> None:
    with SessionLocal() as db:
        document = db.get(Document, document_id)
        if document is None:
            return

        output_dir = get_document_output_dir(document_id)
        document.parse_status = "PARSING"
        document.parse_output_dir = str(output_dir)
        document.parse_error = None
        db.commit()

        if not document.storage_path:
            _mark_failed(db, document, "Document has no storage_path.", output_dir)
            return

        storage_path = Path(document.storage_path).expanduser().resolve()
        if not storage_path.exists():
            _mark_failed(db, document, f"Original file not found: {storage_path}", output_dir)
            return

        output_dir.mkdir(parents=True, exist_ok=True)
        command = build_mineru_command(storage_path, output_dir)
        environment = os.environ.copy()
        environment.setdefault("CUDA_VISIBLE_DEVICES", "0")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                check=False,
                env=environment,
                text=True,
                timeout=get_mineru_timeout_seconds(),
            )
        except subprocess.TimeoutExpired as exc:
            message = _failure_message(
                f"MinerU timed out after {get_mineru_timeout_seconds()} seconds",
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
            )
            _mark_failed(db, document, message, output_dir)
            return
        except FileNotFoundError:
            _mark_failed(db, document, f"MinerU binary not found: {get_mineru_bin()}", output_dir)
            return
        except OSError as exc:
            _mark_failed(db, document, f"MinerU execution failed: {exc}", output_dir)
            return

        if result.returncode != 0:
            message = _failure_message(
                f"MinerU failed with return code {result.returncode}",
                stdout=result.stdout,
                stderr=result.stderr,
            )
            _mark_failed(db, document, message, output_dir)
            return

        markdown_path = find_parsed_markdown(output_dir)
        if markdown_path is None:
            message = _failure_message(
                "MinerU finished but no Markdown file was found",
                stdout=result.stdout,
                stderr=result.stderr,
            )
            _mark_failed(db, document, message, output_dir)
            return

        document.parse_status = "PARSED"
        document.parse_output_dir = str(output_dir)
        document.parsed_markdown_path = str(markdown_path)
        document.parse_error = None
        db.commit()

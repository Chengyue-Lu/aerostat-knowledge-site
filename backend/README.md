# Backend (FastAPI + SQLite Documents)
<!-- markdownlint-disable -->
## Activate virtual environment

```bash
cd backend
source .venv/bin/activate
python --version
```

Expected: Python 3.12.x

## Install dependencies

```bash
pip install -r requirements.txt
```

## SQLite database

The backend stores document metadata in SQLite.

Database URL priority:

1. `DATABASE_URL` environment variable
2. fallback: `sqlite:///./data/aerostat_knowledge.db`

When running from the `backend/` directory, the fallback database file is:

```text
backend/data/aerostat_knowledge.db
```

Example local environment:

```bash
export DATABASE_URL=sqlite:///./data/aerostat_knowledge.db
export DOCS_RAW_DIR=./data/docs_raw
export MINERU_BIN=mineru
export MINERU_OUTPUT_DIR=./data/mineru_outputs
export MINERU_TIMEOUT_SECONDS=21600
# Optional. Leave unset to use MinerU default GPU/default route.
# export MINERU_BACKEND=pipeline
```

`backend/.env.example` is provided as a reference for local configuration.

The app creates tables on startup with SQLAlchemy `create_all`. It does not
insert placeholder seed documents.

## Raw document storage

`POST /documents/upload` accepts `.txt`, `.md`, and `.pdf` files. The backend
stores the original file locally and creates a SQLite document metadata record.

Storage directory priority:

1. `DOCS_RAW_DIR` environment variable
2. fallback: `backend/data/docs_raw/`

Each upload is saved in a generated UUID directory to avoid overwriting files
with the same original name. The database keeps:

- `filename`: original file name
- `storage_path`: local saved path
- `file_ext`: normalized extension such as `.md`
- `mime_type`: uploaded content type or guessed MIME type
- `file_size`: saved file size in bytes
- `sha256`: SHA-256 digest of the saved raw file
- `source_type`: `upload`
- `status`: `UPLOADED`
- `parse_status`: `NOT_PARSED`
- `parse_output_dir`: reserved parser output directory
- `parsed_markdown_path`: reserved parsed Markdown artifact path
- `parse_error`: reserved parser error text

This stage registers files and checks local consistency only. Markdown chunks
are built later from MinerU parsed Markdown. The backend still does not run
embeddings or build a vector index.

## MinerU PDF parsing

The backend integrates MinerU through `subprocess`. MinerU is not installed into
`backend/.venv`; set `MINERU_BIN` to the CLI path from the independent MinerU
environment when needed.

Environment variables:

- `MINERU_BIN`: MinerU CLI path. Default: `mineru`
- `MINERU_OUTPUT_DIR`: parse output root. Default: `backend/data/mineru_outputs/`
- `MINERU_BACKEND`: optional backend argument. When set, backend calls `mineru ... -b <value>`. When unset, no `-b` is passed.
- `MINERU_TIMEOUT_SECONDS`: subprocess timeout. Default: `21600` seconds

`POST /documents/{document_id}/parse` queues a PDF parse task and returns
immediately. It does not wait for MinerU to finish. The backend uses one
in-process FIFO worker, so only one document is parsed at a time. Additional
parse requests are marked `QUEUED` and processed sequentially.

The queue is intentionally local and non-durable in this first version. If the
backend process restarts, queued in-memory tasks are lost. On startup, the
backend marks any persisted `QUEUED` or `PARSING` documents as `FAILED` and
writes this `parse_error`:

```text
Parser task was interrupted by backend restart. Please submit parse again.
```

Users can submit parsing again through the same `POST /documents/{document_id}/parse`
endpoint.

Parse status values used by this version:

- `NOT_PARSED`: uploaded or registered but not parsed
- `QUEUED`: waiting for the single MinerU worker
- `PARSING`: currently running MinerU
- `PARSED`: Markdown artifact was found and registered
- `FAILED`: MinerU failed, timed out, or no Markdown artifact was found

Timeout failures are stored with `parse_error_code` set to `TIMEOUT`. Other
failure classes include `COMMAND_FAILED`, `NO_MARKDOWN`, `BINARY_NOT_FOUND`,
`MISSING_SOURCE`, `INVALID_SOURCE`, `EXECUTION_ERROR`, and `INTERRUPTED`.

The upload path stores `page_count` for PDF files using `pypdf`, with lightweight
fallback detection if the parser cannot read the file. The frontend warns when a
PDF has more than 20 pages because MinerU parsing may take significantly longer
on weaker GPUs.

MinerU command shape:

```bash
<MINERU_BIN> -p <storage_path> -o <document_output_dir>
```

When `MINERU_BACKEND` is set:

```bash
<MINERU_BIN> -p <storage_path> -o <document_output_dir> -b <MINERU_BACKEND>
```

The worker sets `CUDA_VISIBLE_DEVICES=0` unless it already exists in the backend
process environment.

## Markdown chunk building

The backend can build structured SQLite chunks from a parsed Markdown artifact.
This is a synchronous first version and does not use a background queue.

Chunk table fields:

- `document_id`: source document id
- `chunk_index`: zero-based order within the document
- `heading_path`: Markdown heading path joined with ` > `
- `heading_text`: nearest section heading
- `content`: chunk text
- `char_count`: character count
- `token_estimate`: approximate token count using a simple character heuristic
- `source_path`: parsed Markdown path used to build the chunk
- `created_at`: chunk creation time

Chunking strategy:

- read `Document.parsed_markdown_path`
- normalize line endings and collapse excessive blank lines
- remove MinerU image links and `<details>` OCR blocks while keeping normal text
- split sections by Markdown headings `#` through `####`
- keep heading text and heading path metadata
- for paper-like Markdown, start at `Abstract` when present
- skip low-value metadata sections such as `article info`, `Contents`, `References`, and `Acknowledgements`
- keep the abstract as one chunk when it fits under `max_chars`
- accumulate paragraphs with default `target_chars=1000`
- keep chunks below `max_chars=1600` where possible
- use `overlap_chars=200` only when a complete trailing paragraph fits
- hard-split only when a single paragraph exceeds `max_chars`

`POST /documents/{document_id}/chunks/build` requires:

- document exists
- `parse_status` is `PARSED`
- `parsed_markdown_path` is set and points to an existing file

The endpoint deletes previous chunks for that document, writes the rebuilt
chunks, updates `Document.chunk_count`, and returns the updated document.

`GET /documents/{document_id}/chunks` returns chunks ordered by `chunk_index`.

`DELETE /documents/{document_id}/chunks` removes all chunks for the document and
sets `Document.chunk_count` back to `0`.

## Reconcile dry-run

`GET /admin/reconcile/dry-run` checks SQLite file references against local
storage without modifying data.

Response fields:

- `missing_files`: documents whose `storage_path` points to a missing file
- `missing_parse_artifacts`: documents whose `parsed_markdown_path` points to a missing file
- `orphan_files`: files under `DOCS_RAW_DIR` that are not referenced by document records

Example:

```bash
curl http://127.0.0.1:8000/admin/reconcile/dry-run
```

## Run locally (uvicorn)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

When testing MinerU parsing, prefer running without `--reload`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`--reload` watches local files and can restart the backend while MinerU writes
outputs under `data/mineru_outputs/`. A restart interrupts the in-memory parse
queue and the app intentionally marks the interrupted `QUEUED` / `PARSING`
document as `FAILED`.

If reload is required for other backend work, exclude local data directories:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude "data/*"
```

Local persistent configuration can be placed in `backend/.env`. This file is
loaded automatically at startup and is ignored by git. Real environment
variables still take precedence over values in `.env`.

## Development CORS

Backend enables development CORS for these frontend origins:

- http://localhost:5173
- http://127.0.0.1:5173
- http://100.122.3.8:5173

## Quick API checks

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/documents
curl -X POST http://127.0.0.1:8000/documents \
  -H "Content-Type: application/json" \
  -d '{"title":"试验文档元数据","category":"试验记录","status":"draft","filename":"test-note.md","source_type":"manual","chunk_count":0}'
curl -X POST http://127.0.0.1:8000/documents/upload \
  -F "file=@./sample.md"
curl http://127.0.0.1:8000/documents/1
# Use a PDF document id returned by /documents/upload.
curl -X POST http://127.0.0.1:8000/documents/4/parse
curl http://127.0.0.1:8000/documents/4
curl http://127.0.0.1:8000/documents/4/parse-result
curl -X POST http://127.0.0.1:8000/documents/4/chunks/build
curl http://127.0.0.1:8000/documents/4/chunks
curl -X DELETE http://127.0.0.1:8000/documents/4/chunks
curl http://127.0.0.1:8000/admin/reconcile/dry-run
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"系留气球有哪些典型应用场景？"}'
```

## API responses

`GET /health`:

```json
{"status": "ok"}
```

`GET /documents` returns document metadata from SQLite:

```json
[
  {
    "id": 1,
    "title": "浮空器基础概念占位文档",
    "category": "基础知识",
    "status": "seed",
    "filename": "aerostat-basics-placeholder.md",
    "storage_path": null,
    "file_ext": null,
    "mime_type": null,
    "file_size": null,
    "sha256": null,
    "source_type": "seed",
    "chunk_count": 0,
    "parse_status": "NOT_PARSED",
    "parse_output_dir": null,
    "parsed_markdown_path": null,
    "parse_error": null,
    "created_at": "2026-04-24T10:00:00",
    "updated_at": "2026-04-24T10:00:00"
  }
]
```

Documents are returned in stable `id` ascending order.

`POST /documents` creates a document metadata record. It does not upload files
or parse document content.

Request:

```json
{
  "title": "试验文档元数据",
  "category": "试验记录",
  "status": "draft",
  "filename": "test-note.md",
  "storage_path": null,
  "file_ext": ".md",
  "mime_type": "text/markdown",
  "file_size": 128,
  "sha256": "optional-sha256-value",
  "source_type": "manual",
  "chunk_count": 0,
  "parse_status": "NOT_PARSED"
}
```

Response: `201 Created` with the created document.

`POST /documents/upload` uploads a `.txt`, `.md`, or `.pdf` file and creates
metadata:

```bash
curl -X POST http://127.0.0.1:8000/documents/upload \
  -F "file=@./sample.md"
```

Example response:

```json
{
  "id": 4,
  "title": "sample",
  "category": "未分类",
  "status": "UPLOADED",
  "filename": "sample.md",
  "storage_path": "/path/to/backend/data/docs_raw/<uuid>/sample.md",
  "file_ext": ".md",
  "mime_type": "text/markdown",
  "file_size": 128,
  "sha256": "a-valid-sha256-hex-digest",
  "source_type": "upload",
  "chunk_count": 0,
  "parse_status": "NOT_PARSED",
  "parse_output_dir": null,
  "parsed_markdown_path": null,
  "parse_error": null,
  "created_at": "2026-04-25T10:00:00",
  "updated_at": "2026-04-25T10:00:00"
}
```

`POST /documents/{document_id}/chunks/build` rebuilds chunks from parsed
Markdown:

```bash
curl -X POST http://127.0.0.1:8000/documents/4/chunks/build
```

Example response is the updated document metadata, including `chunk_count`.

`GET /documents/{document_id}/chunks` returns chunk records:

```bash
curl http://127.0.0.1:8000/documents/4/chunks
```

Example response:

```json
[
  {
    "id": 1,
    "document_id": 4,
    "chunk_index": 0,
    "heading_path": "Introduction",
    "heading_text": "Introduction",
    "content": "# Introduction\n\n...",
    "char_count": 934,
    "token_estimate": 234,
    "source_path": "/path/to/result.md",
    "created_at": "2026-04-27T10:00:00"
  }
]
```

`DELETE /documents/{document_id}/chunks` removes chunks for one document:

```bash
curl -X DELETE http://127.0.0.1:8000/documents/4/chunks
```

`GET /documents/{document_id}` returns one document metadata record or `404`
when the id does not exist.

`DELETE /documents/{document_id}` deletes one document metadata record and
removes its local raw file and MinerU output directory when those paths exist:

```bash
curl -X DELETE http://127.0.0.1:8000/documents/4
```

Example response:

```json
{"status": "deleted", "id": 4}
```

`POST /documents/{document_id}/parse` queues MinerU parsing for a PDF document:

```bash
curl -X POST http://127.0.0.1:8000/documents/4/parse
```

Example immediate response:

```json
{
  "id": 4,
  "title": "sample",
  "status": "UPLOADED",
  "filename": "sample.pdf",
  "file_ext": ".pdf",
  "parse_status": "QUEUED",
  "parse_output_dir": "/path/to/backend/data/mineru_outputs/4",
  "parsed_markdown_path": null,
  "parse_error": null
}
```

Poll `GET /documents/{document_id}` to observe `QUEUED`, `PARSING`, `PARSED`, or
`FAILED`.

`GET /documents/{document_id}/parse-result` returns parsed Markdown content when
`parsed_markdown_path` exists:

```bash
curl http://127.0.0.1:8000/documents/4/parse-result
```

Example response:

```json
{
  "document_id": 4,
  "parsed_markdown_path": "/path/to/backend/data/mineru_outputs/4/result.md",
  "content": "# Parsed markdown..."
}
```

`GET /admin/reconcile/dry-run` returns file consistency results:

```json
{
  "missing_files": [],
  "missing_parse_artifacts": [],
  "orphan_files": []
}
```

`POST /chat` accepts:

```json
{"question": "系留气球有哪些典型应用场景？"}
```

It returns a placeholder reply:

```json
{
  "reply": "已收到你的问题：...",
  "sources": []
}
```

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
```

`backend/.env.example` is provided as a reference for local configuration.

The app creates tables on startup with SQLAlchemy `create_all`. The first
version also inserts three explicit seed documents only when the documents
table is empty. The seed data lives in `backend/app/main.py` and can be removed
later.

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

This stage registers files and checks local consistency only. It does not parse
text, split chunks, run MinerU, run embeddings, or build an index.

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

`GET /documents/{document_id}` returns one document metadata record or `404`
when the id does not exist.

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

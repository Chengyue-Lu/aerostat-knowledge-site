# Backend (FastAPI + SQLite Metadata)
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
```

`backend/.env.example` is provided as a reference for local configuration.

The app creates tables on startup with SQLAlchemy `create_all`. The first
version also inserts three explicit seed documents only when the documents
table is empty. The seed data lives in `backend/app/main.py` and can be removed
later.

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
curl http://127.0.0.1:8000/documents/1
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
    "source_type": "seed",
    "chunk_count": 0,
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
  "source_type": "manual",
  "chunk_count": 0
}
```

Response: `201 Created` with the created document.

`GET /documents/{document_id}` returns one document metadata record or `404`
when the id does not exist.

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

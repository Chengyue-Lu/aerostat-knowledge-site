# Backend (FastAPI Minimal)
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
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"系留气球有哪些典型应用场景？"}'
```

## Placeholder API responses

`GET /health`:

```json
{"status": "ok"}
```

`GET /documents` returns a small hardcoded list:

```json
[
  {
    "id": "doc-001",
    "title": "浮空器基础概念占位文档",
    "category": "基础知识",
    "status": "placeholder"
  }
]
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

# Backend (FastAPI Minimal)

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

## Quick API checks

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/documents
curl -X POST http://127.0.0.1:8000/chat
```

# 2026-04-24

- Initialize minimal runnable FastAPI backend under `backend/`.
- Add app entrypoint at `backend/app/main.py` with endpoints:
  - `GET /health` -> `{"status": "ok"}`
  - `GET /documents` -> `[]`
  - `POST /chat` -> `{"reply": "hello"}`
- Add minimal dependency file `backend/requirements.txt` (`fastapi`, `uvicorn`).
- Add `backend/README.md` with virtual environment activation and uvicorn startup instructions.

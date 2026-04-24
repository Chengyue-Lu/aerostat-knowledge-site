# 2026-04-24

- Add development CORS in backend FastAPI app for frontend origins:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
  - `http://100.122.3.8:5173`
- Initialize minimal runnable FastAPI backend under `backend/`.
- Add app entrypoint at `backend/app/main.py` with endpoints:
  - `GET /health` -> `{"status": "ok"}`
  - `GET /documents` -> `[]`
  - `POST /chat` -> `{"reply": "hello"}`
- Add minimal dependency file `backend/requirements.txt` (`fastapi`, `uvicorn`).
- Add `backend/README.md` with virtual environment activation and uvicorn startup instructions.

# Changelog

## 2026-04-24

### Backend

- Initialize minimal runnable FastAPI backend under `backend/`.
- Add app entrypoint at `backend/app/main.py` with endpoints:
  - `GET /health` -> `{"status": "ok"}`
  - `GET /documents` -> placeholder document list
  - `POST /chat` -> placeholder reply with `sources`
- Add development CORS in backend FastAPI app for frontend origins:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
  - `http://100.122.3.8:5173`
- Add minimal dependency file `backend/requirements.txt` (`fastapi`, `uvicorn`).
- Add `backend/README.md` with local startup and placeholder API response instructions.

### Frontend

- Initialize minimal React + Vite project in `frontend/`.
- Add basic routing with three pages: `/`, `/knowledge`, `/chat`.
- Keep home page Backend Health card calling `${API_BASE_URL}/health`.
- Add Knowledge placeholder page calling `${API_BASE_URL}/documents` and rendering placeholder documents.
- Add Chat placeholder page posting to `${API_BASE_URL}/chat` and rendering returned `reply`.
- Resolve API base URL in `src/config.js`:
  - Prefer `import.meta.env.VITE_API_BASE_URL`
  - Fallback to `http://localhost:8000` when env is not set
- Add `frontend/README.md` with page status and local startup instructions.

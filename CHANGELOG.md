# Changelog

## 2026-04-26

### Backend

- Add MinerU subprocess integration without installing MinerU into `backend/.venv`.
- Add MinerU configuration environment variables:
  - `MINERU_BIN`
  - `MINERU_OUTPUT_DIR`
  - `MINERU_BACKEND`
  - `MINERU_TIMEOUT_SECONDS`
- Add `POST /documents/{document_id}/parse` to queue PDF parsing.
- Add an in-process single worker FIFO parse queue so only one MinerU task runs at a time.
- Track parse states `QUEUED`, `PARSING`, `PARSED`, and `FAILED`.
- Run MinerU with `CUDA_VISIBLE_DEVICES=0` unless already configured.
- Register parsed Markdown output in `parsed_markdown_path`.
- Add `GET /documents/{document_id}/parse-result` to return parsed Markdown content.

### Frontend

- Show a Parse button for PDF documents with `parse_status` `NOT_PARSED` or `FAILED`.
- Submit parse requests from the Knowledge page and refresh the document list.

### Docs

- Document MinerU environment variables, parse queue behavior, and parse-result curl examples.
- Update project status to “MinerU parsing integration”.

## 2026-04-25

### Backend

- Add raw document upload endpoint `POST /documents/upload`.
- Accept `.txt`, `.md`, and `.pdf` uploads through FastAPI `UploadFile`.
- Store uploaded source files under `DOCS_RAW_DIR` or `backend/data/docs_raw/` by default.
- Save each uploaded file in a generated UUID directory to avoid overwriting duplicate file names.
- Add file registration fields to document metadata:
  - `storage_path`
  - `file_ext`
  - `mime_type`
  - `file_size`
  - `sha256`
  - `parse_status`
  - `parse_output_dir`
  - `parsed_markdown_path`
  - `parse_error`
- Compute and store SHA-256, file extension, MIME type, and file size on upload.
- Add dry-run reconciliation endpoint `GET /admin/reconcile/dry-run`.
- Return `missing_files`, `missing_parse_artifacts`, and `orphan_files` without modifying data.
- Create uploaded document records with default metadata:
  - `category`: `未分类`
  - `status`: `UPLOADED`
  - `source_type`: `upload`
  - `chunk_count`: `0`
  - `parse_status`: `NOT_PARSED`
- Add `python-multipart` backend dependency for multipart form uploads.

### Frontend

- Add a minimal upload area to the Knowledge page.
- Support selecting and uploading `.txt` / `.md` / `.pdf` files.
- Refresh the document list after successful upload.
- Show upload errors returned by the backend.
- Show document parse status in the list when returned by the backend.

### Docs

- Document `DOCS_RAW_DIR`, upload storage behavior, and curl upload examples.
- Document file registration fields and the dry-run reconcile endpoint.
- Update project status to “file registration and consistency checking”.

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

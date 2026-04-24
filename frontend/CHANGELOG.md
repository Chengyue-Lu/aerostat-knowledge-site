# 2026-04-24

- Replace hardcoded health URL in frontend with `API_BASE_URL` constant (`http://100.122.3.8:8000`).
- Initialize minimal React + Vite project in `frontend/`.
- Add basic routing with three pages: `/`, `/knowledge`, `/chat`.
- Add home page health check component to call `http://100.122.3.8:8000/health` and display status.
- Add `frontend/README.md` with local startup instructions.

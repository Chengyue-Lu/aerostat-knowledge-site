# Frontend (React + Vite Minimal)
<!-- markdownlint-disable -->
## Install dependencies

```bash
cd frontend
npm install
```

## Start local development server

```bash
npm run dev
```

Default URL: http://localhost:5173

## Pages

- `/`: 首页，保留 Backend Health 卡片并请求 `${API_BASE_URL}/health`。
- `/knowledge`: 知识库占位页，请求 `${API_BASE_URL}/documents` 并渲染占位文档列表。
- `/chat`: 问答占位页，提交问题到 `${API_BASE_URL}/chat` 并展示返回的 `reply`。

## Backend health check

Home page requests `${API_BASE_URL}/health`.

Knowledge page requests `${API_BASE_URL}/documents`.

Chat page posts JSON to `${API_BASE_URL}/chat`:

```json
{"question": "系留气球有哪些典型应用场景？"}
```

Expected placeholder response:

```json
{"reply": "已收到你的问题：...", "sources": []}
```

If a request fails, the page shows a visible error message.

Current `API_BASE_URL` is resolved in `src/config.js`:

- Prefer `import.meta.env.VITE_API_BASE_URL`
- Fallback to `http://localhost:8000` when env is not set

## Configure VITE_API_BASE_URL

Create `.env.local` in `frontend/`:

```bash
VITE_API_BASE_URL=http://100.122.3.8:8000
```

Then restart the dev server.

Example runtime target:

- http://100.122.3.8:8000

So the health check URL is:

- http://100.122.3.8:8000/health

Expected response:

```json
{"status": "ok"}
```

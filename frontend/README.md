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

- / (Home)
- /knowledge
- /chat

## Backend health check

The home page requests `${API_BASE_URL}/health`.

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

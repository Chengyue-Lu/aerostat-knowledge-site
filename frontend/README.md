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

Current `API_BASE_URL` is defined in `src/config.js` as:

- http://100.122.3.8:8000

So the health check URL is:

- http://100.122.3.8:8000/health

Expected response:

```json
{"status": "ok"}
```

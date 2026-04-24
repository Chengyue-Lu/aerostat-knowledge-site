from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Aerostat Knowledge Site Backend")

DEV_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://100.122.3.8:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Basic service health endpoint for frontend connectivity checks."""
    return {"status": "ok"}


@app.get("/documents")
def list_documents() -> list:
    """Return placeholder document list for early frontend integration."""
    return []


@app.post("/chat")
def chat() -> dict[str, str]:
    """Return placeholder chat reply for minimal end-to-end flow."""
    return {"reply": "hello"}

from fastapi import FastAPI

app = FastAPI(title="Aerostat Knowledge Site Backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/documents")
def list_documents() -> list:
    return []


@app.post("/chat")
def chat() -> dict[str, str]:
    return {"reply": "hello"}

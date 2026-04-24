from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


class Document(BaseModel):
    id: str
    title: str
    category: str
    status: str


class ChatRequest(BaseModel):
    question: str = ""


class ChatResponse(BaseModel):
    reply: str
    sources: list[Document]


PLACEHOLDER_DOCUMENTS = [
    Document(
        id="doc-001",
        title="浮空器基础概念占位文档",
        category="基础知识",
        status="placeholder",
    ),
    Document(
        id="doc-002",
        title="系留气球应用场景占位文档",
        category="应用场景",
        status="placeholder",
    ),
    Document(
        id="doc-003",
        title="飞行安全与维护占位文档",
        category="安全维护",
        status="placeholder",
    ),
]


@app.get("/health")
def health() -> dict[str, str]:
    """Basic service health endpoint for frontend connectivity checks."""
    return {"status": "ok"}


@app.get("/documents")
def list_documents() -> list[Document]:
    """Return placeholder document list for early frontend integration."""
    return PLACEHOLDER_DOCUMENTS


@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    """Return placeholder chat reply for minimal end-to-end flow."""
    question = request.question.strip()
    if question:
        reply = f"已收到你的问题：“{question}”。当前问答仍为占位能力，尚未接入真实知识库检索。"
    else:
        reply = "当前问答仍为占位能力，请输入一个关于浮空器知识的问题。"

    return ChatResponse(reply=reply, sources=[])

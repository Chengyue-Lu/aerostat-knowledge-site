from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1)
    category: str = Field(default="未分类", min_length=1)
    status: str = Field(default="draft", min_length=1)
    filename: str | None = None
    source_type: str | None = None
    chunk_count: int = Field(default=0, ge=0)


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ChatRequest(BaseModel):
    question: str = ""


class ChatResponse(BaseModel):
    reply: str
    sources: list[DocumentRead]

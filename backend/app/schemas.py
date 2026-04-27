from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1)
    category: str = Field(default="未分类", min_length=1)
    status: str = Field(default="draft", min_length=1)
    filename: str | None = None
    storage_path: str | None = None
    file_ext: str | None = None
    mime_type: str | None = None
    file_size: int | None = Field(default=None, ge=0)
    page_count: int | None = Field(default=None, ge=0)
    sha256: str | None = None
    source_type: str | None = None
    chunk_count: int = Field(default=0, ge=0)
    parse_status: str = Field(default="NOT_PARSED", min_length=1)
    parse_output_dir: str | None = None
    parsed_markdown_path: str | None = None
    parse_error_code: str | None = None
    parse_error: str | None = None


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class DocumentChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    chunk_index: int
    heading_path: str
    heading_text: str | None = None
    content: str
    char_count: int
    token_estimate: int | None = None
    source_path: str | None = None
    created_at: datetime


class ChatRequest(BaseModel):
    question: str = ""


class ChatResponse(BaseModel):
    reply: str
    sources: list[DocumentRead]


class ParseResult(BaseModel):
    document_id: int
    parsed_markdown_path: str
    content: str

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[int] = None


class SourceDocument(BaseModel):
    filename: str
    page: int
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]
    disclaimer: str = (
        "This response is for informational purposes only and does not "
        "constitute medical advice. Always consult a qualified healthcare professional."
    )


# ── Conversations ─────────────────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    title: str = Field(default="New Conversation", max_length=255)


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    sources: Optional[list] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SaveMessageRequest(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)
    sources: Optional[list] = None


# ── Admin ─────────────────────────────────────────────────────────────────────

class DocumentInfo(BaseModel):
    filename: str
    chunks: int


class UploadResponse(BaseModel):
    filename: str
    chunks_inserted: int
    message: str

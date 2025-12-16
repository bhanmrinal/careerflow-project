"""Chat request and response models."""

from datetime import datetime
from typing import Any

from app.models.conversation import AgentType
from pydantic import BaseModel, Field


class ResumeChange(BaseModel):
    """Represents a change made to the resume."""

    section: str
    original_content: str | None = None
    new_content: str
    change_type: str  # "add", "modify", "delete"
    reasoning: str


class AgentAction(BaseModel):
    """Represents an action taken by an agent."""

    agent_type: AgentType
    action: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str
    conversation_id: str | None = None
    resume_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    message: str
    conversation_id: str
    agent_type: AgentType
    reasoning: str | None = None
    actions: list[AgentAction] = Field(default_factory=list)
    resume_changes: list[ResumeChange] = Field(default_factory=list)
    current_resume_version: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)


class FileUploadResponse(BaseModel):
    """Response model for file upload endpoint."""

    resume_id: str
    filename: str
    message: str
    sections_detected: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history."""

    conversation_id: str
    messages: list[dict[str, Any]]
    resume_id: str | None = None
    current_version: int = 1
    created_at: datetime
    updated_at: datetime


class ResumeVersionResponse(BaseModel):
    """Response model for resume version."""

    version_id: str
    version_number: int
    content: str
    changes_description: str
    agent_used: str | None = None
    created_at: datetime


class VersionCompareResponse(BaseModel):
    """Response model for comparing resume versions."""

    version_a: ResumeVersionResponse
    version_b: ResumeVersionResponse
    differences: list[dict[str, Any]]

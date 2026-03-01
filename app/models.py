from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    session_id: str = Field(min_length=1)
    user_message: str = Field(min_length=1)


class QueryResponse(BaseModel):
    answer: str
    clarification_needed: bool
    clarification_question: str | None = None
    insights: dict[str, Any] = Field(default_factory=dict)
    data_quality_caveats: list[str] = Field(default_factory=list)
    trace: list[str] = Field(default_factory=list)
    fetched_at_utc: str


class ResetRequest(BaseModel):
    session_id: str = Field(min_length=1)


class HealthResponse(BaseModel):
    status: str
    app_env: str
    monday_configured: bool
    openai_configured: bool

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Mode(StrEnum):
    OFFLINE = "offline"
    LIVE = "live"


class Operation(StrEnum):
    LIST = "list"
    READ = "read"
    TRIAGE = "triage"
    DRAFT = "draft"
    SEND = "send"


class MailAddress(BaseModel):
    name: str
    address: str


class MailMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    sender: MailAddress
    recipients: list[MailAddress]
    subject: str
    body: str
    received_at: datetime
    is_read: bool = False


class MessageSummary(BaseModel):
    id: str
    sender_name: str
    sender_address: str
    subject: str
    received_at: datetime
    is_read: bool

    @classmethod
    def from_message(cls, message: MailMessage) -> MessageSummary:
        return cls(
            id=message.id,
            sender_name=message.sender.name,
            sender_address=message.sender.address,
            subject=message.subject,
            received_at=message.received_at,
            is_read=message.is_read,
        )


class AuthContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    display_name: str | None = None
    user_assertion: str | None = Field(default=None, exclude=True, repr=False)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    message_id: str | None = None


class AnswerResponse(BaseModel):
    answer: str
    citations: list[str]
    mode: Mode


class TriageRequest(BaseModel):
    message_id: str


class TriagePriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class TriageResult(BaseModel):
    message_id: str
    priority: TriagePriority
    category: str
    requires_response: bool
    rationale: str


class DraftRequest(BaseModel):
    message_id: str
    instructions: str | None = Field(default=None, max_length=500)


class DraftReply(BaseModel):
    id: str
    message_id: str
    to: list[MailAddress]
    subject: str
    body: str


class ConfirmationRequest(BaseModel):
    draft_id: str


class ConfirmationChallenge(BaseModel):
    token: str
    expires_at: datetime


class SendRequest(BaseModel):
    draft_id: str
    confirmation_token: str


class SendResult(BaseModel):
    sent: bool
    provider_id: str | None = None


class HealthResponse(BaseModel):
    status: str
    mode: Mode
    live_integrations_ready: bool


class BrowserSignInConfig(BaseModel):
    enabled: bool
    tenant_id: str | None = None
    spa_client_id: str | None = None
    authority: str | None = None
    api_audience: str | None = None
    api_scope: str | None = None
    msal_browser_cdn_url: str | None = None

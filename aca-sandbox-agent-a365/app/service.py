from __future__ import annotations

import re
import threading
from dataclasses import dataclass

from .agent_runtime import AgentRuntime
from .confirmation import ConfirmationTokens
from .errors import AuthorizationError, NotFoundError
from .mail_tools import MailTools
from .models import (
    AnswerResponse,
    AskRequest,
    AuthContext,
    ConfirmationChallenge,
    DraftReply,
    DraftRequest,
    MessageSummary,
    Mode,
    Operation,
    SendResult,
    TriagePriority,
    TriageResult,
)
from .observability import PrivacySafeObserver
from .policy import OperationPolicy


@dataclass(frozen=True)
class BoundDraft:
    draft: DraftReply
    user_id: str
    tenant_id: str


class InboxService:
    def __init__(
        self,
        mode: Mode,
        mail: MailTools,
        policy: OperationPolicy,
        confirmations: ConfirmationTokens,
        observer: PrivacySafeObserver,
        runtime: AgentRuntime | None = None,
    ):
        self._mode = mode
        self._mail = mail
        self._policy = policy
        self._confirmations = confirmations
        self._observer = observer
        self._runtime = runtime
        self._drafts: dict[str, BoundDraft] = {}
        self._drafts_lock = threading.Lock()

    async def list_inbox(self, auth: AuthContext) -> list[MessageSummary]:
        with self._observer.operation(Operation.LIST, auth):
            with self._observer.tool("mail.search_messages"):
                messages = await self._mail.list_messages(auth)
            return [
                MessageSummary.from_message(item)
                for item in messages
            ]

    async def ask(self, auth: AuthContext, request: AskRequest) -> AnswerResponse:
        with self._observer.operation(Operation.READ, auth):
            with self._observer.tool("mail.search_messages"):
                messages = await self._mail.list_messages(auth)
            if request.message_id:
                with self._observer.tool("mail.get_message"):
                    messages = [
                        await self._mail.get_message(auth, request.message_id)
                    ]
            if self._mode is Mode.LIVE:
                if self._runtime is None:
                    raise AuthorizationError("live agent runtime is unavailable")
                context = "\n".join(
                    f"[{m.id}] From: {m.sender.name}; Subject: {m.subject}; Body: {m.body}"
                    for m in messages
                )
                with self._observer.inference():
                    answer = await self._runtime.answer(
                        f"Mailbox context:\n{context}\n\nQuestion: {request.question}"
                    )
                return AnswerResponse(
                    answer=answer, citations=[m.id for m in messages], mode=self._mode
                )
            return self._offline_answer(request.question, messages)

    def _offline_answer(self, question: str, messages: list) -> AnswerResponse:
        words = set(re.findall(r"[a-z0-9]+", question.lower()))
        ranked = []
        for message in messages:
            haystack = f"{message.subject} {message.body} {message.sender.name}".lower()
            score = sum(1 for word in words if len(word) > 3 and word in haystack)
            if "urgent" in words and any(
                keyword in haystack for keyword in ("urgent", "today", "immediately")
            ):
                score += 3
            ranked.append((score, message))
        selected = [item for score, item in ranked if score > 0]
        if not selected:
            selected = messages[:3]
        citations = [item.id for item in selected]
        summaries = "; ".join(
            f"[{item.id}] {item.sender.name}: {item.subject}" for item in selected
        )
        return AnswerResponse(
            answer=f"Offline fixture results: {summaries}",
            citations=citations,
            mode=self._mode,
        )

    async def triage(self, auth: AuthContext, message_id: str) -> TriageResult:
        self._policy.require(Operation.TRIAGE)
        with self._observer.operation(Operation.TRIAGE, auth):
            with self._observer.tool("mail.get_message"):
                message = await self._mail.get_message(auth, message_id)
            content = f"{message.subject} {message.body}".lower()
            if any(word in content for word in ("urgent", "immediately", "today", "blocked")):
                priority = TriagePriority.HIGH
            elif any(word in content for word in ("newsletter", "fyi", "no action")):
                priority = TriagePriority.LOW
            else:
                priority = TriagePriority.NORMAL
            if any(word in content for word in ("password", "security", "phishing")):
                category = "security"
            elif any(word in content for word in ("invoice", "payment", "billing")):
                category = "finance"
            elif any(word in content for word in ("meeting", "schedule", "calendar")):
                category = "scheduling"
            else:
                category = "general"
            requires_response = "?" in message.body or priority is TriagePriority.HIGH
            return TriageResult(
                message_id=message.id,
                priority=priority,
                category=category,
                requires_response=requires_response,
                rationale=f"Deterministic {category} keyword rules selected {priority.value} priority.",
            )

    async def create_draft(self, auth: AuthContext, request: DraftRequest) -> DraftReply:
        with self._observer.operation(Operation.DRAFT, auth):
            with self._observer.tool("mail.get_message"):
                message = await self._mail.get_message(auth, request.message_id)
            draft = await self._mail.create_draft(auth, message, request.instructions)
            if self._mode is Mode.LIVE:
                if self._runtime is None:
                    raise AuthorizationError("live agent runtime is unavailable")
                instruction = (
                    request.instructions
                    or "Write a concise, professional reply that acknowledges the message."
                )
                with self._observer.inference():
                    body = await self._runtime.answer(
                        "Draft only the plain-text body of an email reply. "
                        "Do not add recipients, a subject, markdown, or commentary.\n\n"
                        f"Original sender: {message.sender.name}\n"
                        f"Original subject: {message.subject}\n"
                        f"Original body:\n{message.body}\n\n"
                        f"User instruction: {instruction}"
                    )
                draft = draft.model_copy(update={"body": body.strip()})
            with self._drafts_lock:
                self._drafts[draft.id] = BoundDraft(
                    draft, auth.user_id, auth.tenant_id
                )
            return draft

    def request_confirmation(
        self, auth: AuthContext, draft_id: str
    ) -> ConfirmationChallenge:
        self._get_bound_draft(auth, draft_id)
        return self._confirmations.issue(auth, draft_id)

    async def send(
        self, auth: AuthContext, draft_id: str, confirmation_token: str
    ) -> SendResult:
        with self._drafts_lock:
            self._get_bound_draft_locked(auth, draft_id)
        self._confirmations.consume(confirmation_token, auth, draft_id)
        with self._drafts_lock:
            bound = self._get_bound_draft_locked(auth, draft_id)
            del self._drafts[draft_id]
        with self._observer.operation(Operation.SEND, auth):
            with self._observer.tool("mail.reply"):
                return await self._mail.send_draft(auth, bound.draft)

    def _get_bound_draft(self, auth: AuthContext, draft_id: str) -> BoundDraft:
        with self._drafts_lock:
            return self._get_bound_draft_locked(auth, draft_id)

    def _get_bound_draft_locked(
        self, auth: AuthContext, draft_id: str
    ) -> BoundDraft:
        try:
            bound = self._drafts[draft_id]
        except KeyError as exc:
            raise NotFoundError("draft not found") from exc
        if bound.user_id != auth.user_id or bound.tenant_id != auth.tenant_id:
            raise AuthorizationError("draft belongs to a different user or tenant")
        return bound

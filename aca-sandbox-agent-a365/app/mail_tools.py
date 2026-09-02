from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

import httpx

from .auth import OBOBroker
from .errors import NotFoundError, OfflineSendBlocked, PreviewIntegrationError
from .models import AuthContext, DraftReply, MailMessage, Operation, SendResult
from .policy import OperationPolicy


class MailTools(Protocol):
    async def list_messages(self, auth: AuthContext) -> list[MailMessage]: ...

    async def get_message(self, auth: AuthContext, message_id: str) -> MailMessage: ...

    async def create_draft(
        self, auth: AuthContext, message: MailMessage, instructions: str | None
    ) -> DraftReply: ...

    async def send_draft(self, auth: AuthContext, draft: DraftReply) -> SendResult: ...


class OfflineMailTools:
    def __init__(self, fixture_path: Path, policy: OperationPolicy):
        self._fixture_path = fixture_path
        self._policy = policy
        self._messages: tuple[MailMessage, ...] | None = None

    def _load(self) -> tuple[MailMessage, ...]:
        if self._messages is None:
            payload = json.loads(self._fixture_path.read_text(encoding="utf-8"))
            messages = tuple(MailMessage.model_validate(item) for item in payload["messages"])
            ids = [message.id for message in messages]
            if len(ids) != len(set(ids)):
                raise ValueError("offline fixture contains duplicate message IDs")
            self._messages = tuple(
                sorted(messages, key=lambda item: (item.received_at, item.id), reverse=True)
            )
        return self._messages

    async def list_messages(self, auth: AuthContext) -> list[MailMessage]:
        self._policy.require(Operation.LIST)
        return list(self._load())

    async def get_message(self, auth: AuthContext, message_id: str) -> MailMessage:
        self._policy.require(Operation.READ)
        try:
            return next(message for message in self._load() if message.id == message_id)
        except StopIteration as exc:
            raise NotFoundError("message not found") from exc

    async def create_draft(
        self, auth: AuthContext, message: MailMessage, instructions: str | None
    ) -> DraftReply:
        self._policy.require(Operation.DRAFT)
        first_name = message.sender.name.split()[0]
        context = (
            f" {instructions.strip()}" if instructions and instructions.strip() else ""
        )
        body = (
            f"Hi {first_name},\n\n"
            "Thanks for your message. I have reviewed it and will follow up shortly."
            f"{context}\n\nBest,\nOffline Sample User"
        )
        return DraftReply(
            id=f"offline-draft-{message.id}",
            message_id=message.id,
            to=[message.sender],
            subject=message.subject
            if message.subject.lower().startswith("re:")
            else f"Re: {message.subject}",
            body=body,
        )

    async def send_draft(self, auth: AuthContext, draft: DraftReply) -> SendResult:
        raise OfflineSendBlocked("offline mode never sends mail")


class Agent365Client(Protocol):
    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any], authorization: str
    ) -> Any: ...


class Agent365McpClient:
    """Small MCP boundary; tool names and payload shapes are isolated here."""

    def __init__(self, endpoint: str, client: httpx.AsyncClient | None = None):
        self._endpoint = endpoint
        self._client = client or httpx.AsyncClient(timeout=30)

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any], authorization: str
    ) -> Any:
        request_id = str(uuid4())
        try:
            response = await self._client.post(
                self._endpoint,
                headers={
                    "Authorization": authorization,
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
                json={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments},
                },
            )
            response.raise_for_status()
            if "text/event-stream" in response.headers.get("content-type", ""):
                data_lines = [
                    line[5:].strip()
                    for line in response.text.splitlines()
                    if line.startswith("data:")
                ]
                if not data_lines:
                    raise ValueError("empty MCP event stream")
                payload = json.loads(data_lines[-1])
            else:
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise PreviewIntegrationError("Agent 365 MailTools request failed") from exc
        if payload.get("error"):
            raise PreviewIntegrationError("Agent 365 MailTools rejected the request")
        result = payload.get("result", {})
        if result.get("isError") is True:
            raise PreviewIntegrationError("Agent 365 MailTools tool execution failed")
        if "structuredContent" in result:
            return result["structuredContent"]
        content = result.get("content", [])
        if content and isinstance(content[0], dict) and "text" in content[0]:
            try:
                return json.loads(content[0]["text"])
            except json.JSONDecodeError:
                return content[0]["text"]
        return result


class Agent365MailTools:
    """Work IQ MailTools adapter with explicit actor binding and an operation allow-list."""

    TOOL_NAMES = {
        Operation.LIST: "mcp_MailTools_graph_mail_searchMessages",
        Operation.READ: "mcp_MailTools_graph_mail_getMessage",
        Operation.SEND: "mcp_MailTools_graph_mail_reply",
    }

    def __init__(
        self,
        client: Agent365Client,
        obo: OBOBroker,
        policy: OperationPolicy,
    ):
        self._client = client
        self._obo = obo
        self._policy = policy

    async def _call(
        self, operation: Operation, auth: AuthContext, arguments: dict[str, Any]
    ) -> Any:
        self._policy.require(operation)
        authorization = await self._obo.authorization_header(auth, "mailtools")
        return await self._client.call_tool(
            self.TOOL_NAMES[operation], arguments, authorization
        )

    async def list_messages(self, auth: AuthContext) -> list[MailMessage]:
        payload = await self._call(
            Operation.LIST,
            auth,
            {
                "requests": [
                    {
                        "entityTypes": ["message"],
                        "query": {"queryString": "received>=1900-01-01"},
                        "from": 0,
                        "size": 50,
                    }
                ]
            },
        )
        return [self._to_message(item) for item in self._search_resources(payload)]

    async def get_message(self, auth: AuthContext, message_id: str) -> MailMessage:
        payload = await self._call(
            Operation.READ,
            auth,
            {
                "id": message_id,
                "select": (
                    "id,subject,sender,toRecipients,body,receivedDateTime,isRead"
                ),
                "preferHtml": False,
            },
        )
        return self._to_message(payload.get("message", payload))

    async def create_draft(
        self, auth: AuthContext, message: MailMessage, instructions: str | None
    ) -> DraftReply:
        self._policy.require(Operation.DRAFT)
        requested_content = (
            instructions.strip() if instructions and instructions.strip() else
            "Thanks for your message. I have reviewed it and will follow up shortly."
        )
        return DraftReply(
            id=str(uuid4()),
            message_id=message.id,
            to=[message.sender],
            subject=(
                message.subject
                if message.subject.lower().startswith("re:")
                else f"Re: {message.subject}"
            ),
            body=requested_content,
        )

    async def send_draft(self, auth: AuthContext, draft: DraftReply) -> SendResult:
        await self._call(
            Operation.SEND,
            auth,
            {"id": draft.message_id, "comment": draft.body, "preferHtml": False},
        )
        return SendResult(sent=True)

    @classmethod
    def _search_resources(cls, payload: Any) -> list[dict[str, Any]]:
        resources: list[dict[str, Any]] = []

        def visit(value: Any) -> None:
            if isinstance(value, list):
                for item in value:
                    visit(item)
            elif isinstance(value, dict):
                resource = value.get("resource")
                if isinstance(resource, dict):
                    normalized = dict(resource)
                    normalized.setdefault("id", value.get("hitId"))
                    resources.append(normalized)
                elif {"id", "subject"} <= value.keys():
                    resources.append(value)
                else:
                    for key in ("value", "hitsContainers", "hits", "messages", "items"):
                        if key in value:
                            visit(value[key])

        visit(payload)
        return resources

    @staticmethod
    def _to_message(payload: Any) -> MailMessage:
        if not isinstance(payload, dict):
            raise PreviewIntegrationError(
                "Agent 365 MailTools returned an invalid message"
            )

        def address(value: Any) -> dict[str, str]:
            if isinstance(value, dict):
                value = value.get("emailAddress", value)
            if not isinstance(value, dict) or not value.get("address"):
                raise PreviewIntegrationError(
                    "Agent 365 MailTools returned an invalid mail address"
                )
            return {
                "name": str(value.get("name") or value["address"]),
                "address": str(value["address"]),
            }

        body = payload.get("body", payload.get("bodyPreview", ""))
        if isinstance(body, dict):
            body = body.get("content", "")
        received_at = payload.get("receivedDateTime") or payload.get("received_at")
        normalized = {
            "id": payload.get("id"),
            "sender": address(payload.get("sender") or payload.get("from")),
            "recipients": [
                address(item)
                for item in payload.get(
                    "toRecipients", payload.get("recipients", [])
                )
            ],
            "subject": payload.get("subject") or "(no subject)",
            "body": body,
            "received_at": received_at,
            "is_read": payload.get("isRead", payload.get("is_read", False)),
        }
        try:
            return MailMessage.model_validate(normalized)
        except ValueError as exc:
            raise PreviewIntegrationError(
                "Agent 365 MailTools returned an invalid message"
            ) from exc

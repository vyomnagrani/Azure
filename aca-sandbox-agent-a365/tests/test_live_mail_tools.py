from types import SimpleNamespace

import pytest

from app.mail_tools import Agent365MailTools
from app.errors import PreviewIntegrationError
from app.models import AuthContext, DraftReply, MailAddress, Operation
from app.policy import OperationPolicy


class RecordingClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    async def call_tool(self, tool_name, arguments, authorization):
        self.calls.append((tool_name, arguments, authorization))
        return next(self.responses)


class FakeOBO:
    async def authorization_header(self, auth, resource):
        assert resource == "mailtools"
        return "Bearer downstream"


def live_mail(responses):
    client = RecordingClient(responses)
    policy = OperationPolicy(
        frozenset(
            {Operation.LIST, Operation.READ, Operation.DRAFT, Operation.SEND}
        )
    )
    return Agent365MailTools(client, FakeOBO(), policy), client


class ToolErrorResponse:
    headers = {"content-type": "application/json"}

    def raise_for_status(self):
        return None

    def json(self):
        return {"jsonrpc": "2.0", "result": {"isError": True, "content": []}}


class ToolErrorHttpClient:
    async def post(self, *args, **kwargs):
        return ToolErrorResponse()


@pytest.mark.asyncio
async def test_search_messages_uses_published_tool_and_normalizes_graph_hits():
    mail, client = live_mail(
        [
            {
                "value": [
                    {
                        "hitsContainers": [
                            {
                                "hits": [
                                    {
                                        "hitId": "message-1",
                                        "resource": {
                                            "sender": {
                                                "emailAddress": {
                                                    "name": "Alex",
                                                    "address": "alex@example.com",
                                                }
                                            },
                                            "toRecipients": [],
                                            "subject": "Status",
                                            "bodyPreview": "Update",
                                            "receivedDateTime": "2026-08-01T10:00:00Z",
                                            "isRead": False,
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    )

    messages = await mail.list_messages(
        AuthContext(user_id="user", tenant_id="tenant", user_assertion="token")
    )

    assert [message.id for message in messages] == ["message-1"]
    assert messages[0].body == "Update"
    tool_name, arguments, authorization = client.calls[0]
    assert tool_name == "mcp_MailTools_graph_mail_searchMessages"
    assert arguments["requests"][0]["query"] == {
        "queryString": "received>=1900-01-01"
    }
    assert "actorUserId" not in arguments
    assert authorization == "Bearer downstream"


@pytest.mark.asyncio
async def test_send_uses_reply_tool_only_after_local_draft_creation():
    mail, client = live_mail([{}])
    auth = AuthContext(
        user_id="user", tenant_id="tenant", user_assertion="token"
    )
    message = SimpleNamespace(
        id="message-1",
        sender=MailAddress(name="Alex", address="alex@example.com"),
        subject="Status",
    )

    draft = await mail.create_draft(auth, message, "Approved reply")
    result = await mail.send_draft(auth, draft)

    assert isinstance(draft, DraftReply)
    assert result.sent is True
    assert client.calls == [
        (
            "mcp_MailTools_graph_mail_reply",
            {"id": "message-1", "comment": "Approved reply", "preferHtml": False},
            "Bearer downstream",
        )
    ]


@pytest.mark.asyncio
async def test_mcp_is_error_result_is_not_reported_as_success():
    from app.mail_tools import Agent365McpClient

    client = Agent365McpClient(
        "https://mail.example.test", client=ToolErrorHttpClient()
    )

    with pytest.raises(PreviewIntegrationError, match="tool execution failed"):
        await client.call_tool("tool", {}, "Bearer downstream")

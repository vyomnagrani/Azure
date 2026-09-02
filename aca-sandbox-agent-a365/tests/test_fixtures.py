import pytest

from app.models import AskRequest


@pytest.mark.asyncio
async def test_fixture_order_and_answers_are_deterministic(mail, service, auth):
    first = await mail.list_messages(auth)
    second = await mail.list_messages(auth)

    assert [message.id for message in first] == ["msg-001", "msg-002", "msg-003"]
    assert first == second

    one = await service.ask(auth, AskRequest(question="What is urgent?"))
    two = await service.ask(auth, AskRequest(question="What is urgent?"))
    assert one == two
    assert one.citations == ["msg-001"]
    assert "[msg-001]" in one.answer


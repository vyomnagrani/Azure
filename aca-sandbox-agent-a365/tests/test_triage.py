import pytest

from app.models import TriagePriority


@pytest.mark.asyncio
async def test_triage_uses_deterministic_rules(service, auth):
    urgent = await service.triage(auth, "msg-001")
    meeting = await service.triage(auth, "msg-002")
    newsletter = await service.triage(auth, "msg-003")

    assert urgent.priority is TriagePriority.HIGH
    assert urgent.requires_response is True
    assert meeting.category == "scheduling"
    assert newsletter.priority is TriagePriority.LOW
    assert newsletter.requires_response is False


import pytest

from app.errors import OfflineSendBlocked
from app.models import DraftRequest


@pytest.mark.asyncio
async def test_offline_send_is_blocked_even_with_valid_confirmation(service, auth):
    draft = await service.create_draft(auth, DraftRequest(message_id="msg-001"))
    challenge = service.request_confirmation(auth, draft.id)

    with pytest.raises(OfflineSendBlocked):
        await service.send(auth, draft.id, challenge.token)


import pytest

from app.confirmation import ConfirmationTokens
from app.errors import (
    ConfirmationBindingMismatch,
    ConfirmationExpired,
    ConfirmationReplay,
)
from app.models import AuthContext


SECRET = "a-secure-test-secret-that-is-longer-than-32-bytes"


def test_confirmation_expires():
    now = [1000.0]
    tokens = ConfirmationTokens(SECRET, 30, clock=lambda: now[0])
    auth = AuthContext(user_id="user-1", tenant_id="tenant-1")
    challenge = tokens.issue(auth, "draft-1")

    now[0] = 1030.0
    with pytest.raises(ConfirmationExpired):
        tokens.consume(challenge.token, auth, "draft-1")


def test_confirmation_is_single_use():
    tokens = ConfirmationTokens(SECRET, 30, clock=lambda: 1000.0)
    auth = AuthContext(user_id="user-1", tenant_id="tenant-1")
    challenge = tokens.issue(auth, "draft-1")

    tokens.consume(challenge.token, auth, "draft-1")
    with pytest.raises(ConfirmationReplay):
        tokens.consume(challenge.token, auth, "draft-1")


@pytest.mark.parametrize(
    "other",
    [
        AuthContext(user_id="user-2", tenant_id="tenant-1"),
        AuthContext(user_id="user-1", tenant_id="tenant-2"),
    ],
)
def test_confirmation_is_bound_to_user_and_tenant(other):
    tokens = ConfirmationTokens(SECRET, 30, clock=lambda: 1000.0)
    owner = AuthContext(user_id="user-1", tenant_id="tenant-1")
    challenge = tokens.issue(owner, "draft-1")

    with pytest.raises(ConfirmationBindingMismatch):
        tokens.consume(challenge.token, other, "draft-1")


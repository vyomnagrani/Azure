from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone

from .errors import (
    ConfirmationBindingMismatch,
    ConfirmationError,
    ConfirmationExpired,
    ConfirmationReplay,
)
from .models import AuthContext, ConfirmationChallenge


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class ConfirmationTokens:
    """Process-local single-use confirmations; use a shared store for multi-worker apps."""

    def __init__(
        self,
        secret: str,
        ttl_seconds: int,
        clock: Callable[[], float] = time.time,
    ):
        self._secret = secret.encode("utf-8")
        self._ttl = ttl_seconds
        self._clock = clock
        self._consumed: set[str] = set()
        self._lock = threading.Lock()

    def issue(self, auth: AuthContext, draft_id: str) -> ConfirmationChallenge:
        now = int(self._clock())
        payload = {
            "action": "send",
            "draft_id": draft_id,
            "exp": now + self._ttl,
            "iat": now,
            "jti": secrets.token_urlsafe(18),
            "sub": auth.user_id,
            "tid": auth.tenant_id,
        }
        body = _encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
        signature = _encode(hmac.digest(self._secret, body.encode("ascii"), hashlib.sha256))
        return ConfirmationChallenge(
            token=f"{body}.{signature}",
            expires_at=datetime.fromtimestamp(payload["exp"], timezone.utc),
        )

    def consume(self, token: str, auth: AuthContext, draft_id: str) -> None:
        try:
            body, supplied_signature = token.split(".", 1)
            expected_signature = _encode(
                hmac.digest(self._secret, body.encode("ascii"), hashlib.sha256)
            )
            if not hmac.compare_digest(supplied_signature, expected_signature):
                raise ConfirmationError("invalid confirmation token")
            payload = json.loads(_decode(body))
            if not isinstance(payload, dict):
                raise ConfirmationError("invalid confirmation token")
        except ConfirmationError:
            raise
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ConfirmationError("invalid confirmation token") from exc

        if payload.get("action") != "send" or payload.get("draft_id") != draft_id:
            raise ConfirmationBindingMismatch("confirmation does not match this draft")
        if payload.get("sub") != auth.user_id or payload.get("tid") != auth.tenant_id:
            raise ConfirmationBindingMismatch("confirmation does not match this user and tenant")
        if not isinstance(payload.get("exp"), int) or self._clock() >= payload["exp"]:
            raise ConfirmationExpired("confirmation token has expired")
        jti = payload.get("jti")
        if not isinstance(jti, str):
            raise ConfirmationError("invalid confirmation token")
        with self._lock:
            if jti in self._consumed:
                raise ConfirmationReplay("confirmation token has already been used")
            self._consumed.add(jti)

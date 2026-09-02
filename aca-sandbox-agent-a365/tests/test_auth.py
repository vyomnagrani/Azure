from types import SimpleNamespace

import pytest
from starlette.requests import Request

from app import auth as auth_module
from app.auth import (
    AUTH_SCHEME,
    CLIENT_ASSERTION_TYPE,
    TOKEN_EXCHANGE_SCOPE,
    AgentIdSidecarOBOBroker,
    DirectFmiOBOBroker,
    EntraOIDCAuthProvider,
)
from app.config import Settings
from app.errors import AuthenticationError
from app.models import AuthContext


ALLOWED_CLIENT = "22222222-2222-2222-2222-222222222222"


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"authorizationHeader": f"{AUTH_SCHEME} downstream-token"}


class RecordingClient:
    def __init__(self):
        self.headers = None

    async def get(self, endpoint, headers):
        self.headers = headers
        return FakeResponse()


class FakeManagedIdentityCredential:
    def __init__(self):
        self.scopes = []

    def get_token(self, scope):
        self.scopes.append(scope)
        return SimpleNamespace(token="managed-identity-assertion")


class TokenResponse:
    def __init__(self, token):
        self._token = token

    def raise_for_status(self):
        return None

    def json(self):
        return {"access_token": self._token}


class RecordingTokenClient:
    def __init__(self):
        self.calls = []
        self.tokens = iter(("parent-token", "work-iq-token"))

    async def post(self, url, data, headers):
        self.calls.append({"url": url, "data": data, "headers": headers})
        return TokenResponse(next(self.tokens))


def request_with_token(token: str = "incoming-token") -> Request:
    value = f"{AUTH_SCHEME} {token}".encode()
    return Request({"type": "http", "headers": [(b"authorization", value)]})


@pytest.mark.asyncio
async def test_sidecar_receives_constructed_authorization_header():
    client = RecordingClient()
    broker = AgentIdSidecarOBOBroker(Settings(_env_file=None), client=client)
    context = AuthContext(
        user_id="user", tenant_id="tenant", user_assertion="incoming-token"
    )

    result = await broker.authorization_header(context, "mailtools")

    assert client.headers == {
        "Authorization": f"{AUTH_SCHEME} incoming-token"
    }
    assert result == f"{AUTH_SCHEME} downstream-token"


@pytest.mark.asyncio
async def test_direct_fmi_broker_performs_parent_then_obo_exchange(caplog):
    credential = FakeManagedIdentityCredential()
    client = RecordingTokenClient()
    settings = SimpleNamespace(
        azure_client_id="managed-id",
        entra_tenant_id="tenant-1",
        entra_blueprint_app_id="blueprint-app",
        entra_agent_identity_app_id="agent-app",
        a365_mailtools_scope="api://work-iq/.default",
    )
    broker = DirectFmiOBOBroker(settings, credential=credential, client=client)
    context = AuthContext(
        user_id="user", tenant_id="tenant-1", user_assertion="incoming-user-token"
    )

    header = await broker.authorization_header(context, "mailtools")

    assert header == f"{AUTH_SCHEME} work-iq-token"
    assert credential.scopes == [TOKEN_EXCHANGE_SCOPE]
    assert len(client.calls) == 2
    parent = client.calls[0]["data"]
    assert parent == {
        "grant_type": "client_credentials",
        "client_id": "blueprint-app",
        "client_assertion_type": CLIENT_ASSERTION_TYPE,
        "client_assertion": "managed-identity-assertion",
        "scope": TOKEN_EXCHANGE_SCOPE,
        "fmi_path": "agent-app",
    }
    obo = client.calls[1]["data"]
    assert obo == {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "client_id": "agent-app",
        "client_assertion_type": CLIENT_ASSERTION_TYPE,
        "client_assertion": "parent-token",
        "assertion": "incoming-user-token",
        "requested_token_use": "on_behalf_of",
        "scope": "api://work-iq/.default",
    }
    assert "incoming-user-token" not in caplog.text
    assert "managed-identity-assertion" not in caplog.text
    assert "parent-token" not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("caller_claim", ["azp", "appid"])
async def test_oidc_accepts_allowlisted_azp_or_appid(monkeypatch, caller_claim):
    settings = SimpleNamespace(
        entra_tenant_id="tenant-1",
        allowed_client_ids=frozenset({ALLOWED_CLIENT}),
        entra_audience="api://blueprint",
        entra_api_scope="api://blueprint/access_as_user",
        entra_jwks_url="https://login.example.test/keys",
    )
    provider = EntraOIDCAuthProvider(settings)
    provider._jwks = SimpleNamespace(
        get_signing_key_from_jwt=lambda token: SimpleNamespace(key="key")
    )
    captured = {}

    def decode(token, key, **kwargs):
        captured.update(kwargs)
        return {
            "exp": 2000,
            "iat": 1000,
            "sub": "subject",
            "oid": "user-1",
            "tid": "tenant-1",
            "scp": "access_as_user",
            caller_claim: ALLOWED_CLIENT,
        }

    monkeypatch.setattr(auth_module.jwt, "decode", decode)
    context = await provider.authenticate(request_with_token())

    assert context.user_id == "user-1"
    assert captured["audience"] == "api://blueprint"
    assert captured["issuer"].endswith("/tenant-1/v2.0")


@pytest.mark.asyncio
async def test_oidc_rejects_client_outside_allowlist(monkeypatch):
    settings = SimpleNamespace(
        entra_tenant_id="tenant-1",
        allowed_client_ids=frozenset({ALLOWED_CLIENT}),
        entra_audience="api://blueprint",
        entra_api_scope="api://blueprint/access_as_user",
        entra_jwks_url="https://login.example.test/keys",
    )
    provider = EntraOIDCAuthProvider(settings)
    provider._jwks = SimpleNamespace(
        get_signing_key_from_jwt=lambda token: SimpleNamespace(key="key")
    )
    monkeypatch.setattr(
        auth_module.jwt,
        "decode",
        lambda *args, **kwargs: {
            "exp": 2000,
            "iat": 1000,
            "sub": "subject",
            "tid": "tenant-1",
            "scp": "access_as_user",
            "azp": "99999999-9999-9999-9999-999999999999",
        },
    )

    with pytest.raises(AuthenticationError, match="unexpected client"):
        await provider.authenticate(request_with_token())


@pytest.mark.asyncio
async def test_oidc_rejects_token_without_required_scope(monkeypatch):
    settings = SimpleNamespace(
        entra_tenant_id="tenant-1",
        allowed_client_ids=frozenset({ALLOWED_CLIENT}),
        entra_audience="api://blueprint",
        entra_api_scope="api://blueprint/access_as_user",
        entra_jwks_url="https://login.example.test/keys",
    )
    provider = EntraOIDCAuthProvider(settings)
    provider._jwks = SimpleNamespace(
        get_signing_key_from_jwt=lambda token: SimpleNamespace(key="key")
    )
    monkeypatch.setattr(
        auth_module.jwt,
        "decode",
        lambda *args, **kwargs: {
            "exp": 2000,
            "iat": 1000,
            "sub": "subject",
            "tid": "tenant-1",
            "scp": "other_scope",
            "azp": ALLOWED_CLIENT,
        },
    )

    with pytest.raises(AuthenticationError, match="required delegated scope"):
        await provider.authenticate(request_with_token())

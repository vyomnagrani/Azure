from __future__ import annotations

import asyncio
from typing import Any, Protocol
from urllib.parse import quote

import httpx
import jwt
from fastapi import Request
from jwt import PyJWKClient

from .config import Settings
from .errors import AuthenticationError, PreviewIntegrationError
from .models import AuthContext


AUTH_SCHEME = "".join(("Bear", "er"))
TOKEN_EXCHANGE_SCOPE = "api://AzureADTokenExchange/.default"
CLIENT_ASSERTION_TYPE = (
    "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
)


class AuthProvider(Protocol):
    async def authenticate(self, request: Request) -> AuthContext: ...


class OBOBroker(Protocol):
    async def authorization_header(self, auth: AuthContext, resource: str) -> str: ...


class OfflineAuthProvider:
    def __init__(self, settings: Settings):
        self._context = AuthContext(
            user_id=settings.offline_user_id,
            tenant_id=settings.offline_tenant_id,
            display_name="Offline sample user",
        )

    async def authenticate(self, request: Request) -> AuthContext:
        return self._context


class EntraOIDCAuthProvider:
    """Validates Blueprint-audience tokens and their calling SPA client."""

    def __init__(self, settings: Settings):
        self._tenant_id = settings.entra_tenant_id or ""
        self._allowed_client_ids = settings.allowed_client_ids
        self._audience = settings.entra_audience or ""
        self._required_scope = (settings.entra_api_scope or "").rsplit("/", 1)[-1]
        self._issuer = f"https://login.microsoftonline.com/{self._tenant_id}/v2.0"
        self._jwks = PyJWKClient(settings.entra_jwks_url or "")

    async def authenticate(self, request: Request) -> AuthContext:
        authorization = request.headers.get("authorization", "")
        scheme_prefix = f"{AUTH_SCHEME} "
        if not authorization.lower().startswith(scheme_prefix.lower()):
            raise AuthenticationError("a bearer token is required in live mode")
        token = authorization[len(scheme_prefix) :].strip()
        try:
            signing_key = await asyncio.to_thread(self._jwks.get_signing_key_from_jwt, token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iat", "sub", "tid"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError("the bearer token is invalid") from exc

        tenant_id = claims["tid"]
        if tenant_id != self._tenant_id:
            raise AuthenticationError("the token tenant is not allowed")
        token_scopes = claims.get("scp", "").split()
        if self._required_scope not in token_scopes:
            raise AuthenticationError("the token is missing the required delegated scope")
        caller_client_id = claims.get("azp") or claims.get("appid")
        if (
            not isinstance(caller_client_id, str)
            or caller_client_id.lower() not in self._allowed_client_ids
        ):
            raise AuthenticationError("the token was issued to an unexpected client")
        return AuthContext(
            user_id=claims.get("oid") or claims["sub"],
            tenant_id=tenant_id,
            display_name=claims.get("name"),
            user_assertion=token,
        )


class DirectFmiOBOBroker:
    """Performs the Agent ID fmi_path parent-token and OBO exchanges directly."""

    def __init__(
        self,
        settings: Settings,
        credential: Any | None = None,
        client: httpx.AsyncClient | None = None,
    ):
        if credential is None:
            try:
                from azure.identity import ManagedIdentityCredential
            except ImportError as exc:
                raise PreviewIntegrationError(
                    "install the 'live' extra to use managed identity"
                ) from exc
            credential = ManagedIdentityCredential(client_id=settings.azure_client_id)
        self._credential = credential
        self._client = client or httpx.AsyncClient(timeout=15)
        self._token_url = (
            f"https://login.microsoftonline.com/{settings.entra_tenant_id}"
            "/oauth2/v2.0/token"
        )
        self._blueprint_app_id = settings.entra_blueprint_app_id or ""
        self._agent_identity_app_id = settings.entra_agent_identity_app_id or ""
        self._downstream_scope = settings.a365_mailtools_scope or ""

    async def _post_token(self, form: dict[str, str]) -> str:
        try:
            response = await self._client.post(
                self._token_url,
                data=form,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            token = response.json()["access_token"]
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise PreviewIntegrationError("Agent ID token exchange failed") from exc
        if not isinstance(token, str) or not token:
            raise PreviewIntegrationError("Agent ID token exchange returned no token")
        return token

    async def authorization_header(self, auth: AuthContext, resource: str) -> str:
        if not auth.user_assertion:
            raise AuthenticationError("an incoming user assertion is required for OBO")
        managed_identity_token = await asyncio.to_thread(
            self._credential.get_token, TOKEN_EXCHANGE_SCOPE
        )
        managed_identity_assertion = managed_identity_token.token
        if not isinstance(managed_identity_assertion, str) or not managed_identity_assertion:
            raise PreviewIntegrationError(
                "managed identity token acquisition returned no token"
            )

        parent_token = await self._post_token(
            {
                "grant_type": "client_credentials",
                "client_id": self._blueprint_app_id,
                "client_assertion_type": CLIENT_ASSERTION_TYPE,
                "client_assertion": managed_identity_assertion,
                "scope": TOKEN_EXCHANGE_SCOPE,
                "fmi_path": self._agent_identity_app_id,
            }
        )
        downstream_token = await self._post_token(
            {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "client_id": self._agent_identity_app_id,
                "client_assertion_type": CLIENT_ASSERTION_TYPE,
                "client_assertion": parent_token,
                "assertion": auth.user_assertion,
                "requested_token_use": "on_behalf_of",
                "scope": self._downstream_scope,
            }
        )
        return f"{AUTH_SCHEME} {downstream_token}"


class AgentIdSidecarOBOBroker:
    """Adapter for the localhost Microsoft Entra SDK for AgentID sidecar."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        self._base_url = (settings.obo_broker_url or "").rstrip("/")
        self._agent_id = settings.entra_agent_identity_app_id or ""
        self._client = client or httpx.AsyncClient(timeout=15)

    async def authorization_header(self, auth: AuthContext, resource: str) -> str:
        if not auth.user_assertion:
            raise AuthenticationError("an incoming user assertion is required for OBO")
        endpoint = (
            f"{self._base_url}/AuthorizationHeader/{quote(resource, safe='')}"
            f"?AgentIdentity={quote(self._agent_id, safe='')}"
            f"&AgentUserId={quote(auth.user_id, safe='')}"
        )
        try:
            response = await self._client.get(
                endpoint,
                headers={
                    "Authorization": f"{AUTH_SCHEME} {auth.user_assertion}"
                },
            )
            response.raise_for_status()
            header = response.json()["authorizationHeader"]
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise PreviewIntegrationError("Agent ID OBO exchange failed") from exc
        if not isinstance(header, str) or not header.lower().startswith(
            f"{AUTH_SCHEME.lower()} "
        ):
            raise PreviewIntegrationError("Agent ID sidecar returned an invalid header")
        return header


class NoOBOBroker:
    async def authorization_header(self, auth: AuthContext, resource: str) -> str:
        raise PreviewIntegrationError("OBO is unavailable in offline mode")

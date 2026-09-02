from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import Mode, Operation


OFFLINE_DEVELOPMENT_SECRET = "offline-development-key-change-before-live-123456"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_mode: Mode = Mode.OFFLINE
    offline_fixture_path: Path = Path("sample-data/inbox.json")
    offline_user_id: str = "offline-user"
    offline_tenant_id: str = "offline-tenant"

    confirmation_hmac_secret: str = Field(
        default=OFFLINE_DEVELOPMENT_SECRET, min_length=32, repr=False
    )
    confirmation_ttl_seconds: int = Field(default=120, ge=30, le=300)
    allowed_operations: str = "list,read,triage,draft"
    log_level: str = "INFO"

    entra_tenant_id: str | None = None
    entra_spa_client_id: str | None = None
    entra_audience: str | None = None
    entra_api_scope: str | None = None
    entra_allowed_client_ids: str = ""
    entra_blueprint_app_id: str | None = None
    entra_agent_identity_app_id: str | None = None
    entra_jwks_url: str | None = None
    msal_browser_cdn_url: str = (
        "https://alcdn.msauth.net/browser/4.25.0/js/msal-browser.min.js"
    )
    obo_broker_mode: str = "direct_fmi"
    obo_broker_url: str | None = None
    azure_client_id: str | None = None
    a365_mailtools_url: str | None = None
    a365_mailtools_audience: str | None = None
    a365_mailtools_scope: str | None = None
    foundry_endpoint: str | None = None
    foundry_model_deployment: str | None = None
    allow_default_azure_credential_local_development: bool = False

    @property
    def operation_allowlist(self) -> frozenset[Operation]:
        return frozenset(
            Operation(item.strip().lower())
            for item in self.allowed_operations.split(",")
            if item.strip()
        )

    @property
    def allowed_client_ids(self) -> frozenset[str]:
        return frozenset(
            item.strip().lower()
            for item in self.entra_allowed_client_ids.split(",")
            if item.strip()
        )

    @model_validator(mode="after")
    def validate_security_configuration(self) -> Settings:
        try:
            operations = self.operation_allowlist
        except ValueError as exc:
            raise ValueError("ALLOWED_OPERATIONS contains an unknown operation") from exc
        if not operations:
            raise ValueError("ALLOWED_OPERATIONS must not be empty")
        if self.app_mode is Mode.OFFLINE:
            if Operation.SEND in operations:
                raise ValueError("offline mode must not allow the send operation")
            if not self.offline_user_id or not self.offline_tenant_id:
                raise ValueError("offline user and tenant IDs must not be empty")
            return self

        required = {
            "ENTRA_TENANT_ID": self.entra_tenant_id,
            "ENTRA_SPA_CLIENT_ID": self.entra_spa_client_id,
            "ENTRA_AUDIENCE": self.entra_audience,
            "ENTRA_API_SCOPE": self.entra_api_scope,
            "ENTRA_ALLOWED_CLIENT_IDS": self.entra_allowed_client_ids,
            "ENTRA_BLUEPRINT_APP_ID": self.entra_blueprint_app_id,
            "ENTRA_AGENT_IDENTITY_APP_ID": self.entra_agent_identity_app_id,
            "ENTRA_JWKS_URL": self.entra_jwks_url,
            "AZURE_CLIENT_ID": self.azure_client_id,
            "A365_MAILTOOLS_URL": self.a365_mailtools_url,
            "A365_MAILTOOLS_AUDIENCE": self.a365_mailtools_audience,
            "A365_MAILTOOLS_SCOPE": self.a365_mailtools_scope,
            "FOUNDRY_ENDPOINT": self.foundry_endpoint,
            "FOUNDRY_MODEL_DEPLOYMENT": self.foundry_model_deployment,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"live mode is missing required settings: {', '.join(missing)}")
        if self.confirmation_hmac_secret == OFFLINE_DEVELOPMENT_SECRET:
            raise ValueError("live mode requires a unique CONFIRMATION_HMAC_SECRET")
        identifiers = {
            "ENTRA_TENANT_ID": self.entra_tenant_id,
            "ENTRA_SPA_CLIENT_ID": self.entra_spa_client_id,
            "ENTRA_BLUEPRINT_APP_ID": self.entra_blueprint_app_id,
            "ENTRA_AGENT_IDENTITY_APP_ID": self.entra_agent_identity_app_id,
            "AZURE_CLIENT_ID": self.azure_client_id,
        }
        for name, value in identifiers.items():
            try:
                UUID(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{name} must be a UUID") from exc
        try:
            for client_id in self.allowed_client_ids:
                UUID(client_id)
        except ValueError as exc:
            raise ValueError("ENTRA_ALLOWED_CLIENT_IDS must contain only UUIDs") from exc
        if (self.entra_spa_client_id or "").lower() not in self.allowed_client_ids:
            raise ValueError(
                "ENTRA_ALLOWED_CLIENT_IDS must include ENTRA_SPA_CLIENT_ID"
            )
        if not self.entra_audience.startswith("api://"):
            raise ValueError("ENTRA_AUDIENCE must target the Agent ID Blueprint API")
        if self.entra_audience != f"api://{self.entra_blueprint_app_id}":
            raise ValueError("ENTRA_AUDIENCE must use ENTRA_BLUEPRINT_APP_ID")
        if not self.entra_api_scope.startswith(f"{self.entra_audience}/"):
            raise ValueError("ENTRA_API_SCOPE must be a scope exposed by ENTRA_AUDIENCE")
        if not self.msal_browser_cdn_url.startswith(
            "https://alcdn.msauth.net/browser/"
        ):
            raise ValueError("MSAL_BROWSER_CDN_URL must use the official pinned MSAL CDN")
        if self.obo_broker_mode not in {"direct_fmi", "sidecar"}:
            raise ValueError("OBO_BROKER_MODE must be direct_fmi or sidecar")
        if self.obo_broker_mode == "sidecar":
            if not self.obo_broker_url or not self.obo_broker_url.startswith(
                "http://127.0.0.1"
            ):
                raise ValueError(
                    "sidecar mode requires a localhost OBO_BROKER_URL"
                )
        if not self.entra_jwks_url.startswith("https://"):
            raise ValueError("ENTRA_JWKS_URL must use HTTPS")
        if not self.a365_mailtools_url.startswith("https://"):
            raise ValueError("A365_MAILTOOLS_URL must use HTTPS")
        foundry_url = urlsplit(self.foundry_endpoint)
        if (
            foundry_url.scheme != "https"
            or not foundry_url.hostname
            or not foundry_url.hostname.endswith(".services.ai.azure.com")
            or foundry_url.username
            or foundry_url.password
            or foundry_url.port is not None
            or foundry_url.query
            or foundry_url.fragment
            or re.fullmatch(
                r"/api/projects/[A-Za-z0-9][A-Za-z0-9_.-]{1,63}",
                foundry_url.path,
            )
            is None
        ):
            raise ValueError("FOUNDRY_ENDPOINT must be a Foundry project endpoint")
        expected_scope = f"{self.a365_mailtools_audience.rstrip('/')}/.default"
        if self.a365_mailtools_scope != expected_scope:
            raise ValueError(
                "A365_MAILTOOLS_SCOPE must be A365_MAILTOOLS_AUDIENCE plus /.default"
            )
        if self.allow_default_azure_credential_local_development:
            return self
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

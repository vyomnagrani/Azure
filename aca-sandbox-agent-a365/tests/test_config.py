import pytest
from pydantic import ValidationError

from app.config import Settings
from app.models import Mode


TENANT_ID = "11111111-1111-1111-1111-111111111111"
SPA_CLIENT_ID = "22222222-2222-2222-2222-222222222222"
BLUEPRINT_ID = "33333333-3333-3333-3333-333333333333"
AGENT_ID = "44444444-4444-4444-4444-444444444444"
MANAGED_IDENTITY_ID = "55555555-5555-5555-5555-555555555555"


def live_values(**overrides):
    values = {
        "app_mode": Mode.LIVE,
        "confirmation_hmac_secret": "a-unique-secret-with-at-least-thirty-two-bytes",
        "allowed_operations": "list,read,triage,draft,send",
        "entra_tenant_id": TENANT_ID,
        "entra_spa_client_id": SPA_CLIENT_ID,
        "entra_audience": f"api://{BLUEPRINT_ID}",
        "entra_api_scope": f"api://{BLUEPRINT_ID}/access_as_user",
        "entra_allowed_client_ids": SPA_CLIENT_ID,
        "entra_blueprint_app_id": BLUEPRINT_ID,
        "entra_agent_identity_app_id": AGENT_ID,
        "entra_jwks_url": f"https://login.microsoftonline.com/{TENANT_ID}/keys",
        "azure_client_id": MANAGED_IDENTITY_ID,
        "a365_mailtools_url": "https://mail.example.test/mcp",
        "a365_mailtools_audience": "api://77777777-7777-7777-7777-777777777777",
        "a365_mailtools_scope": (
            "api://77777777-7777-7777-7777-777777777777/.default"
        ),
        "foundry_endpoint": (
            "https://foundry.services.ai.azure.com/api/projects/inbox-agent"
        ),
        "foundry_model_deployment": "model",
        "_env_file": None,
    }
    values.update(overrides)
    return values


def test_offline_defaults_are_safe():
    settings = Settings(_env_file=None)
    assert settings.app_mode is Mode.OFFLINE
    assert "send" not in {operation.value for operation in settings.operation_allowlist}


def test_offline_cannot_enable_send():
    with pytest.raises(ValidationError, match="offline mode must not allow"):
        Settings(allowed_operations="list,read,draft,send", _env_file=None)


def test_live_requires_every_security_setting():
    with pytest.raises(ValidationError, match="live mode is missing required settings"):
        Settings(
            app_mode=Mode.LIVE,
            confirmation_hmac_secret="a-unique-secret-with-at-least-thirty-two-bytes",
            _env_file=None,
        )


def test_live_accepts_separate_spa_and_api_configuration():
    settings = Settings(**live_values())

    assert settings.entra_spa_client_id == SPA_CLIENT_ID
    assert settings.entra_audience == f"api://{BLUEPRINT_ID}"
    assert settings.entra_api_scope.endswith("/access_as_user")
    assert settings.allowed_client_ids == frozenset({SPA_CLIENT_ID})


def test_live_rejects_spa_missing_from_allowlist():
    with pytest.raises(ValidationError, match="must include ENTRA_SPA_CLIENT_ID"):
        Settings(
            **live_values(
                entra_allowed_client_ids="66666666-6666-6666-6666-666666666666"
            )
        )


def test_live_rejects_non_local_sidecar():
    with pytest.raises(ValidationError, match="localhost OBO_BROKER_URL"):
        Settings(
            **live_values(
                obo_broker_mode="sidecar",
                obo_broker_url="https://sidecar.example.test",
            )
        )


def test_live_requires_user_assigned_managed_identity():
    with pytest.raises(ValidationError, match="AZURE_CLIENT_ID"):
        Settings(**live_values(azure_client_id=None))


def test_downstream_scope_must_match_audience():
    with pytest.raises(ValidationError, match="A365_MAILTOOLS_SCOPE"):
        Settings(**live_values(a365_mailtools_scope="https://wrong/.default"))


def test_explicit_local_development_can_use_default_credential():
    settings = Settings(
        **live_values(
            allow_default_azure_credential_local_development=True,
        )
    )
    assert settings.allow_default_azure_credential_local_development is True


@pytest.mark.parametrize(
    "endpoint",
    [
        "not-a-url/api/projects/inbox-agent",
        "http://resource.services.ai.azure.com/api/projects/inbox-agent",
        "https://attacker.example/api/projects/inbox-agent",
        "https://resource.services.ai.azure.com/api/projects/inbox-agent/extra",
        "https://resource.services.ai.azure.com/api/projects/inbox-agent?x=1",
    ],
)
def test_live_rejects_malformed_foundry_project_endpoint(endpoint):
    with pytest.raises(ValidationError, match="Foundry project endpoint"):
        Settings(**live_values(foundry_endpoint=endpoint))

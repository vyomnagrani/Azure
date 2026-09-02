import sys
from types import ModuleType

from app.agent_runtime import MicrosoftAgentFrameworkRuntime


def install_fake_live_modules(monkeypatch, calls):
    framework = ModuleType("agent_framework")
    foundry = ModuleType("agent_framework.foundry")
    azure = ModuleType("azure")
    identity = ModuleType("azure.identity")

    class Agent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FoundryChatClient:
        def __init__(self, **kwargs):
            calls.append(("client", kwargs))

    class ManagedIdentityCredential:
        def __init__(self, **kwargs):
            calls.append(("managed", kwargs))

    class DefaultAzureCredential:
        def __init__(self):
            calls.append(("default", {}))

    framework.Agent = Agent
    foundry.FoundryChatClient = FoundryChatClient
    identity.ManagedIdentityCredential = ManagedIdentityCredential
    identity.DefaultAzureCredential = DefaultAzureCredential
    monkeypatch.setitem(sys.modules, "agent_framework", framework)
    monkeypatch.setitem(sys.modules, "agent_framework.foundry", foundry)
    monkeypatch.setitem(sys.modules, "azure", azure)
    monkeypatch.setitem(sys.modules, "azure.identity", identity)


def test_foundry_uses_user_assigned_managed_identity_by_default(monkeypatch):
    calls = []
    install_fake_live_modules(monkeypatch, calls)

    MicrosoftAgentFrameworkRuntime("https://foundry", "model", "managed-id")

    assert ("managed", {"client_id": "managed-id"}) in calls
    assert not any(kind == "default" for kind, _ in calls)


def test_default_credential_requires_explicit_local_flag(monkeypatch):
    calls = []
    install_fake_live_modules(monkeypatch, calls)

    MicrosoftAgentFrameworkRuntime(
        "https://foundry", "model", None, allow_default_credential_local_development=True
    )

    assert ("default", {}) in calls

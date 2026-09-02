from pathlib import Path

import pytest

from app.config import Settings
from app.confirmation import ConfirmationTokens
from app.mail_tools import OfflineMailTools
from app.models import AuthContext, Mode
from app.observability import PrivacySafeObserver
from app.policy import OperationPolicy
from app.service import InboxService


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def settings() -> Settings:
    return Settings(
        app_mode=Mode.OFFLINE,
        offline_fixture_path=ROOT / "sample-data" / "inbox.json",
        allowed_operations="list,read,triage,draft",
        _env_file=None,
    )


@pytest.fixture
def auth() -> AuthContext:
    return AuthContext(user_id="user-1", tenant_id="tenant-1")


@pytest.fixture
def mail(settings: Settings) -> OfflineMailTools:
    return OfflineMailTools(
        settings.offline_fixture_path,
        OperationPolicy(settings.operation_allowlist),
    )


@pytest.fixture
def service(settings: Settings, mail: OfflineMailTools) -> InboxService:
    policy = OperationPolicy(settings.operation_allowlist)
    return InboxService(
        Mode.OFFLINE,
        mail,
        policy,
        ConfirmationTokens(settings.confirmation_hmac_secret, 120),
        PrivacySafeObserver(Mode.OFFLINE, settings.confirmation_hmac_secret),
    )


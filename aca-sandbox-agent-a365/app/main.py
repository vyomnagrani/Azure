from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from .agent_runtime import MicrosoftAgentFrameworkRuntime
from .auth import (
    AgentIdSidecarOBOBroker,
    DirectFmiOBOBroker,
    EntraOIDCAuthProvider,
    OfflineAuthProvider,
)
from .config import Settings, get_settings
from .confirmation import ConfirmationTokens
from .errors import AppError
from .mail_tools import Agent365MailTools, Agent365McpClient, OfflineMailTools
from .models import (
    AnswerResponse,
    AskRequest,
    AuthContext,
    BrowserSignInConfig,
    ConfirmationChallenge,
    ConfirmationRequest,
    DraftReply,
    DraftRequest,
    HealthResponse,
    MessageSummary,
    Mode,
    SendRequest,
    SendResult,
    TriageRequest,
    TriageResult,
)
from .observability import PrivacySafeObserver, correlation_id
from .policy import OperationPolicy
from .service import InboxService


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    policy = OperationPolicy(settings.operation_allowlist)
    confirmations = ConfirmationTokens(
        settings.confirmation_hmac_secret, settings.confirmation_ttl_seconds
    )
    observer = PrivacySafeObserver(
        settings.app_mode,
        settings.confirmation_hmac_secret,
        settings.entra_agent_identity_app_id,
        settings.foundry_model_deployment,
    )

    if settings.app_mode is Mode.OFFLINE:
        fixture_path = settings.offline_fixture_path
        if not fixture_path.is_absolute():
            fixture_path = PROJECT_ROOT / fixture_path
        auth_provider = OfflineAuthProvider(settings)
        mail = OfflineMailTools(fixture_path, policy)
        runtime = None
    else:
        auth_provider = EntraOIDCAuthProvider(settings)
        obo = (
            AgentIdSidecarOBOBroker(settings)
            if settings.obo_broker_mode == "sidecar"
            else DirectFmiOBOBroker(settings)
        )
        mail = Agent365MailTools(
            Agent365McpClient(settings.a365_mailtools_url or ""), obo, policy
        )
        runtime = MicrosoftAgentFrameworkRuntime(
            settings.foundry_endpoint or "",
            settings.foundry_model_deployment or "",
            settings.azure_client_id,
            settings.allow_default_azure_credential_local_development,
        )

    service = InboxService(
        settings.app_mode, mail, policy, confirmations, observer, runtime
    )
    application = FastAPI(
        title="Agent 365 Inbox Assistant",
        version="0.1.0",
        description="Offline-first inbox Q&A, triage, draft, and confirmed-send sample.",
        docs_url=None if settings.app_mode is Mode.OFFLINE else "/docs",
        redoc_url=None,
    )
    application.state.settings = settings
    application.state.auth_provider = auth_provider
    application.state.inbox_service = service

    @application.middleware("http")
    async def add_correlation_id(request: Request, call_next):
        request_id = request.headers.get("x-correlation-id") or str(uuid4())
        token = correlation_id.set(request_id[:128])
        try:
            response = await call_next(request)
            response.headers["x-correlation-id"] = request_id[:128]
            return response
        finally:
            correlation_id.reset(token)

    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc), "correlation_id": correlation_id.get()},
        )

    async def current_auth(request: Request) -> AuthContext:
        return await application.state.auth_provider.authenticate(request)

    @application.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def browser() -> HTMLResponse:
        return HTMLResponse(
            (PROJECT_ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")
        )

    @application.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            mode=settings.app_mode,
            live_integrations_ready=settings.app_mode is Mode.LIVE,
        )

    @application.get("/api/auth/config", response_model=BrowserSignInConfig)
    async def browser_auth_config() -> BrowserSignInConfig:
        if settings.app_mode is Mode.OFFLINE:
            return BrowserSignInConfig(enabled=False)
        return BrowserSignInConfig(
            enabled=True,
            tenant_id=settings.entra_tenant_id,
            spa_client_id=settings.entra_spa_client_id,
            authority=(
                f"https://login.microsoftonline.com/{settings.entra_tenant_id}"
            ),
            api_audience=settings.entra_audience,
            api_scope=settings.entra_api_scope,
            msal_browser_cdn_url=settings.msal_browser_cdn_url,
        )

    @application.get("/api/inbox", response_model=list[MessageSummary])
    async def inbox(auth: AuthContext = Depends(current_auth)) -> list[MessageSummary]:
        return await service.list_inbox(auth)

    @application.post("/api/ask", response_model=AnswerResponse)
    async def ask(
        payload: AskRequest, auth: AuthContext = Depends(current_auth)
    ) -> AnswerResponse:
        return await service.ask(auth, payload)

    @application.post("/api/triage", response_model=TriageResult)
    async def triage(
        payload: TriageRequest, auth: AuthContext = Depends(current_auth)
    ) -> TriageResult:
        return await service.triage(auth, payload.message_id)

    @application.post("/api/drafts", response_model=DraftReply)
    async def draft(
        payload: DraftRequest, auth: AuthContext = Depends(current_auth)
    ) -> DraftReply:
        return await service.create_draft(auth, payload)

    @application.post("/api/confirmations", response_model=ConfirmationChallenge)
    async def confirmation(
        payload: ConfirmationRequest, auth: AuthContext = Depends(current_auth)
    ) -> ConfirmationChallenge:
        return service.request_confirmation(auth, payload.draft_id)

    @application.post("/api/send", response_model=SendResult)
    async def send(
        payload: SendRequest, auth: AuthContext = Depends(current_auth)
    ) -> SendResult:
        return await service.send(
            auth, payload.draft_id, payload.confirmation_token
        )

    return application


app = create_app()

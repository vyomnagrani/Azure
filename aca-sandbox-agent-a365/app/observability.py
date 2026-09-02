from __future__ import annotations

import hashlib
import hmac
import logging
import time
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from typing import Iterator
from uuid import uuid4

from .models import AuthContext, Mode, Operation
from .errors import PreviewIntegrationError


correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


class PrivacySafeObserver:
    """Emits metadata only: never prompts, subjects, addresses, bodies, or tokens."""

    def __init__(
        self,
        mode: Mode,
        hash_key: str,
        agent_id: str | None = None,
        model: str | None = None,
        logger: logging.Logger | None = None,
    ):
        self._mode = mode
        self._key = hash_key.encode()
        self._logger = logger or logging.getLogger("inbox_agent.audit")
        self._scope_factory = None
        self._request_factory = None
        self._scope_details = None
        self._agent_details = None
        self._inference_factory = None
        self._inference_details = None
        self._tool_factory = None
        self._tool_details_factory = None
        if mode is Mode.LIVE:
            try:
                from microsoft_agents_a365.observability.core import (
                    AgentDetails,
                    ExecuteToolScope,
                    InferenceCallDetails,
                    InferenceOperationType,
                    InferenceScope,
                    InvokeAgentScope,
                    InvokeAgentScopeDetails,
                    Request,
                    ToolCallDetails,
                    configure,
                )
            except ImportError as exc:
                raise PreviewIntegrationError(
                    "install the 'live' extra to enable Agent 365 observability"
                ) from exc
            configured = configure(
                service_name="aca-sandbox-inbox-agent",
                service_namespace="azure.samples",
                suppress_invoke_agent_input=True,
            )
            if not configured:
                raise PreviewIntegrationError(
                    "Agent 365 observability configuration failed"
                )
            self._scope_factory = InvokeAgentScope
            self._request_factory = Request
            self._scope_details = InvokeAgentScopeDetails(endpoint=None)
            self._agent_details = AgentDetails(
                agent_id=agent_id or "unconfigured",
                agent_name="ACA Sandbox Inbox Agent",
            )
            self._inference_factory = InferenceScope
            self._inference_details = InferenceCallDetails(
                operationName=InferenceOperationType.CHAT,
                model=model or "unconfigured",
                providerName="microsoft-foundry",
            )
            self._tool_factory = ExecuteToolScope
            self._tool_details_factory = ToolCallDetails

    def pseudonym(self, value: str) -> str:
        return hmac.new(self._key, value.encode(), hashlib.sha256).hexdigest()[:16]

    @contextmanager
    def operation(self, name: Operation, auth: AuthContext) -> Iterator[None]:
        started = time.perf_counter()
        succeeded = False
        scope_context = nullcontext(None)
        if self._scope_factory is not None and self._request_factory is not None:
            scope_context = self._scope_factory.start(
                request=self._request_factory(content=[]),
                scope_details=self._scope_details,
                agent_details=self._agent_details,
            )
        with scope_context as scope:
            try:
                yield
                succeeded = True
            finally:
                attributes = {
                    "sample.operation": name.value,
                    "sample.mode": self._mode.value,
                    "sample.succeeded": succeeded,
                    "sample.duration_ms": round(
                        (time.perf_counter() - started) * 1000, 2
                    ),
                    "sample.actor": self.pseudonym(
                        f"{auth.tenant_id}:{auth.user_id}"
                    ),
                    "sample.correlation_id": correlation_id.get() or str(uuid4()),
                }
                if scope is not None:
                    scope.record_attributes(attributes)
                self._logger.info(
                    "agent_operation",
                    extra={"event": "agent_operation", **attributes},
                )

    @contextmanager
    def inference(self) -> Iterator[None]:
        context = nullcontext(None)
        if self._inference_factory is not None:
            context = self._inference_factory.start(
                request=self._request_factory(content=[]),
                details=self._inference_details,
                agent_details=self._agent_details,
            )
        with context:
            yield

    @contextmanager
    def tool(self, name: str) -> Iterator[None]:
        context = nullcontext(None)
        if self._tool_factory is not None:
            context = self._tool_factory.start(
                request=self._request_factory(content=[]),
                details=self._tool_details_factory(
                    tool_name=name,
                    arguments={},
                ),
                agent_details=self._agent_details,
            )
        with context:
            yield

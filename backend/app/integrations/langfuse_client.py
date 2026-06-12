from contextlib import contextmanager, nullcontext
from typing import Any

from app.models.schemas import IntegrationStatus, Strategy
from app.settings import Settings


class LangfuseAdapter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            try:
                from langfuse import Langfuse

                self.client = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    base_url=settings.langfuse_base_url,
                )
            except Exception:
                self.client = None

    def status(self) -> IntegrationStatus:
        if self.client:
            return IntegrationStatus(name="Langfuse", state="connected", detail="Tracing and score ingestion enabled")
        return IntegrationStatus(name="Langfuse", state="degraded", detail="Using local trace mirror; add Langfuse credentials for cloud traces")

    @contextmanager
    def observe(self, name: str, **kwargs: Any):
        if not self.client:
            with nullcontext(None) as span:
                yield span
            return
        with self.client.start_as_current_observation(name=name, **kwargs) as span:
            yield span

    def score_strategy(self, span: Any, strategy: Strategy) -> None:
        if not span:
            return
        scores = strategy.scores.model_dump()
        for name, value in scores.items():
            span.score(name=name, value=float(value), data_type="NUMERIC")
        span.score(name="approved", value=strategy.approved, data_type="BOOLEAN")
        span.score(name="gate_result", value=strategy.gate_result, data_type="CATEGORICAL")

    def current_trace_id(self) -> str | None:
        return self.client.get_current_trace_id() if self.client else None

    def trace_url(self, trace_id: str | None) -> str | None:
        if trace_id and self.settings.langfuse_project_url:
            return f"{self.settings.langfuse_project_url.rstrip('/')}/traces/{trace_id}"
        return None

    def flush(self) -> None:
        if self.client:
            self.client.flush()


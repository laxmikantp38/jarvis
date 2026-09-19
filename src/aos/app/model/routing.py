"""Which model may see which context.

Enforced here, at the routing layer, rather than by asking a prompt nicely.
A hosted provider never receives client or employer material (AD-10, FR-44);
the call is refused rather than quietly stripped, because silently sending
less context produces a worse answer with no indication why.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from aos.domain.memory.classification import Confidentiality, strictest
from aos.ports.model import Completion, ContextItem, ModelProvider

log = logging.getLogger(__name__)


class ConfidentialityError(RuntimeError):
    """Raised when context may not reach the provider that was asked for."""


@dataclass(frozen=True)
class ModelRouter:
    hosted: ModelProvider | None
    local: ModelProvider | None

    def complete(self, prompt: str, context: list[ContextItem]) -> Completion:
        required = strictest([item.confidentiality for item in context])
        provider = self._provider_for(required)

        if provider is None:
            raise ConfidentialityError(self._explain(required))

        log.info(
            "routing to %s (context is %s)",
            provider.name,
            required.value,
        )
        return provider.complete(prompt, context)

    def _provider_for(self, required: Confidentiality) -> ModelProvider | None:
        if required.may_reach_a_hosted_model and self.hosted is not None:
            return self.hosted
        # Anything above personal is local-only, whatever is configured.
        return self.local

    def _explain(self, required: Confidentiality) -> str:
        if required.may_reach_a_hosted_model:
            return "No model provider is configured."
        return (
            f"This involves {required.value} material, which never leaves this machine. "
            "Configure a local model to work with it."
        )

    def may_send(self, context: list[ContextItem], provider: ModelProvider) -> bool:
        """Whether this provider is permitted to see this context at all."""
        required = strictest([item.confidentiality for item in context])
        return provider.runs_locally or required.may_reach_a_hosted_model

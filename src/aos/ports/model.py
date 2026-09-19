"""Model access, behind one interface (AD-10).

No provider SDK type appears outside its adapter, so switching provider is
configuration rather than a refactor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from aos.domain.memory.classification import Confidentiality


@dataclass(frozen=True, slots=True)
class ContextItem:
    """A piece of context, carrying where it came from and who may see it."""

    source: str
    text: str
    confidentiality: Confidentiality


@dataclass(frozen=True, slots=True)
class Completion:
    text: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0


class ModelProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def runs_locally(self) -> bool:
        """True only when nothing leaves this machine."""
        ...

    def complete(self, prompt: str, context: list[ContextItem]) -> Completion: ...

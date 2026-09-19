"""Which model may see which context (AD-10, FR-44).

This is the rule that protects his freelance contract, so it is enforced at
the routing layer and not by asking a prompt nicely.
"""

from __future__ import annotations

import pytest

from aos.app.model.routing import ConfidentialityError, ModelRouter
from aos.domain.memory.classification import Confidentiality, strictest
from aos.ports.model import Completion, ContextItem


class FakeProvider:
    def __init__(self, name: str, *, local: bool) -> None:
        self._name = name
        self._local = local
        self.calls: list[list[ContextItem]] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def runs_locally(self) -> bool:
        return self._local

    def complete(self, prompt: str, context: list[ContextItem]) -> Completion:
        self.calls.append(context)
        return Completion(text="ok", provider=self._name)


def item(confidentiality: Confidentiality) -> ContextItem:
    return ContextItem(source="test", text="...", confidentiality=confidentiality)


def router() -> tuple[ModelRouter, FakeProvider, FakeProvider]:
    hosted = FakeProvider("hosted", local=False)
    local = FakeProvider("local", local=True)
    return ModelRouter(hosted=hosted, local=local), hosted, local


class TestStrictest:
    def test_the_whole_context_takes_the_most_sensitive_class(self) -> None:
        assert strictest([Confidentiality.PUBLIC, Confidentiality.CLIENT]) is Confidentiality.CLIENT

    def test_unknown_provenance_is_the_most_restrictive_not_the_most_convenient(
        self,
    ) -> None:
        assert Confidentiality.of_unknown_provenance() is Confidentiality.EMPLOYER
        assert not Confidentiality.of_unknown_provenance().may_reach_a_hosted_model


class TestRouting:
    def test_ordinary_context_goes_to_the_hosted_model(self) -> None:
        route, hosted, local = router()
        route.complete("summarise", [item(Confidentiality.PERSONAL)])

        assert len(hosted.calls) == 1
        assert local.calls == []

    def test_client_material_never_leaves_the_machine(self) -> None:
        route, hosted, local = router()
        route.complete("summarise", [item(Confidentiality.CLIENT)])

        assert hosted.calls == [], "this is the one that could cost him a contract"
        assert len(local.calls) == 1

    def test_one_confidential_item_taints_the_whole_context(self) -> None:
        route, hosted, local = router()
        route.complete(
            "summarise",
            [item(Confidentiality.PUBLIC), item(Confidentiality.CLIENT)],
        )

        assert hosted.calls == []
        assert len(local.calls) == 1

    def test_without_a_local_model_the_call_is_refused_not_stripped(self) -> None:
        """Silently sending less context produces a worse answer with no clue why."""
        route = ModelRouter(hosted=FakeProvider("hosted", local=False), local=None)

        with pytest.raises(ConfidentialityError, match="never leaves this machine"):
            route.complete("summarise", [item(Confidentiality.CLIENT)])

    def test_the_refusal_says_what_would_fix_it(self) -> None:
        route = ModelRouter(hosted=FakeProvider("hosted", local=False), local=None)

        with pytest.raises(ConfidentialityError, match="Configure a local model"):
            route.complete("summarise", [item(Confidentiality.EMPLOYER)])

    def test_may_send_answers_the_question_without_calling_anything(self) -> None:
        route, hosted, local = router()

        assert route.may_send([item(Confidentiality.CLIENT)], hosted) is False
        assert route.may_send([item(Confidentiality.CLIENT)], local) is True
        assert hosted.calls == [] and local.calls == []

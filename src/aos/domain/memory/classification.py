"""Who is allowed to see a record.

Fails closed (AD-24). A record whose provenance cannot be established is
treated as the most restrictive class, not the most convenient one, because
the failure mode of the alternative is client work reaching a hosted model.
"""

from __future__ import annotations

from enum import StrEnum


class Confidentiality(StrEnum):
    PUBLIC = "public"
    PERSONAL = "personal"
    CLIENT = "client-confidential"
    EMPLOYER = "employer-confidential"

    @property
    def may_reach_a_hosted_model(self) -> bool:
        """Only the two least sensitive classes leave this machine."""
        return self in {Confidentiality.PUBLIC, Confidentiality.PERSONAL}

    @classmethod
    def most_restrictive(cls) -> Confidentiality:
        return cls.EMPLOYER

    @classmethod
    def of_unknown_provenance(cls) -> Confidentiality:
        """What an unclassified record becomes. Never PUBLIC."""
        return cls.most_restrictive()


def strictest(classes: list[Confidentiality]) -> Confidentiality:
    """The class a set of records collectively carries."""
    order = [
        Confidentiality.PUBLIC,
        Confidentiality.PERSONAL,
        Confidentiality.CLIENT,
        Confidentiality.EMPLOYER,
    ]
    return max(classes, key=order.index) if classes else Confidentiality.PUBLIC

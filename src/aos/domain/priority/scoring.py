"""What matters most, and why.

Deterministic: identical inputs give an identical score, every time, with no
model anywhere in the path (AD-1, CNFR-1). A model may later *estimate* a
factor that nobody has supplied, and such a value is marked estimated and
carries less weight - but it never produces the score itself.

Every score keeps its full breakdown, because a ranking nobody can interrogate
is a ranking nobody should trust (P-7).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

# Bands are thresholds on the final score, and are configuration.
P1_THRESHOLD = Decimal("0.70")
P2_THRESHOLD = Decimal("0.45")
P3_THRESHOLD = Decimal("0.20")

# Live users outrank convenience. Work that is hurting real people cannot be
# outranked by tidying, whatever the other factors say.
LIVE_HARM_FLOOR = Decimal("0.80")


class Band(StrEnum):
    P1 = "P1"
    """Do now."""
    P2 = "P2"
    """This week."""
    P3 = "P3"
    """Scheduled."""
    P4 = "P4"
    """Candidate for deletion."""

    @property
    def is_urgent(self) -> bool:
        return self is Band.P1

    @property
    def is_deletable(self) -> bool:
        return self is Band.P4


class Factor(StrEnum):
    REVENUE_IMPACT = "revenue impact"
    BUSINESS_IMPACT = "business impact"
    USER_IMPACT = "user impact"
    URGENCY = "urgency"
    STRATEGIC_ALIGNMENT = "strategic alignment"
    RISK_REDUCTION = "risk reduction"
    UNBLOCKS_OTHERS = "unblocks others"
    EFFORT = "effort"
    OPPORTUNITY_COST = "opportunity cost"

    @property
    def is_a_penalty(self) -> bool:
        """Effort and opportunity cost subtract; everything else adds."""
        return self in {Factor.EFFORT, Factor.OPPORTUNITY_COST}


# Revenue and live-user harm dominate, effort is a moderate penalty, and
# opportunity cost only bites when something better is genuinely waiting.
DEFAULT_WEIGHTS: dict[Factor, Decimal] = {
    Factor.REVENUE_IMPACT: Decimal("0.25"),
    Factor.USER_IMPACT: Decimal("0.20"),
    Factor.STRATEGIC_ALIGNMENT: Decimal("0.15"),
    Factor.URGENCY: Decimal("0.15"),
    Factor.BUSINESS_IMPACT: Decimal("0.10"),
    Factor.RISK_REDUCTION: Decimal("0.08"),
    Factor.UNBLOCKS_OTHERS: Decimal("0.07"),
    Factor.EFFORT: Decimal("0.15"),
    Factor.OPPORTUNITY_COST: Decimal("0.10"),
}


@dataclass(frozen=True, slots=True)
class Contribution:
    factor: Factor
    value: Decimal
    """Normalised 0..1."""
    weight: Decimal
    estimated: bool = False
    """True when nobody supplied this and it was inferred."""

    @property
    def effective_weight(self) -> Decimal:
        return self.weight * ESTIMATE_DISCOUNT if self.estimated else self.weight

    @property
    def contribution(self) -> Decimal:
        signed = -self.value if self.factor.is_a_penalty else self.value
        return signed * self.effective_weight

    def describe(self) -> str:
        mark = " (estimated, half weight)" if self.estimated else ""
        sign = "-" if self.factor.is_a_penalty else "+"
        return (
            f"{self.factor.value}{mark}: {self.value:.2f} x {self.effective_weight:.3f} "
            f"= {sign}{abs(self.contribution):.3f}"
        )


@dataclass(frozen=True, slots=True)
class Score:
    value: Decimal
    band: Band
    contributions: tuple[Contribution, ...]
    floored_for_live_harm: bool = False

    @property
    def estimated_inputs(self) -> int:
        return sum(1 for c in self.contributions if c.estimated)

    @property
    def fully_measured(self) -> bool:
        return self.estimated_inputs == 0

    def breakdown(self) -> list[str]:
        """Ordered by how much each factor actually moved the result."""
        ordered = sorted(self.contributions, key=lambda c: abs(c.contribution), reverse=True)
        lines = [c.describe() for c in ordered]
        if self.floored_for_live_harm:
            lines.append("floor applied: this is hurting live users")
        return lines

    def why(self) -> str:
        """The one-line version, for a voice answer."""
        ordered = sorted(self.contributions, key=lambda c: abs(c.contribution), reverse=True)
        top = [c.factor.value for c in ordered[:2] if c.contribution > 0]
        if self.floored_for_live_harm:
            return "it is affecting live users"
        return " and ".join(top) if top else "nothing much argues for it"


@dataclass(frozen=True, slots=True)
class Inputs:
    """Whatever is known. Anything absent is estimated and marked as such."""

    revenue_impact: Decimal | None = None
    business_impact: Decimal | None = None
    user_impact: Decimal | None = None
    urgency: Decimal | None = None
    strategic_alignment: Decimal | None = None
    risk_reduction: Decimal | None = None
    unblocks_others: Decimal | None = None
    effort: Decimal | None = None
    opportunity_cost: Decimal | None = None
    affects_live_users: bool = False

    def as_map(self) -> dict[Factor, Decimal | None]:
        return {
            Factor.REVENUE_IMPACT: self.revenue_impact,
            Factor.BUSINESS_IMPACT: self.business_impact,
            Factor.USER_IMPACT: self.user_impact,
            Factor.URGENCY: self.urgency,
            Factor.STRATEGIC_ALIGNMENT: self.strategic_alignment,
            Factor.RISK_REDUCTION: self.risk_reduction,
            Factor.UNBLOCKS_OTHERS: self.unblocks_others,
            Factor.EFFORT: self.effort,
            Factor.OPPORTUNITY_COST: self.opportunity_cost,
        }


# What an unsupplied factor is assumed to be. Modest rather than middling: a
# factor nobody has spoken for is not evidence in favour.
NEUTRAL = Decimal("0.25")

# An estimate counts for half. It is a guess standing in for a measurement,
# and letting guesses carry full weight is how a ranking stops meaning anything.
ESTIMATE_DISCOUNT = Decimal("0.5")


def score(inputs: Inputs, weights: dict[Factor, Decimal] | None = None) -> Score:
    weights = weights or DEFAULT_WEIGHTS
    contributions = []

    for factor, supplied in inputs.as_map().items():
        estimated = supplied is None
        value = _clamp(supplied if supplied is not None else NEUTRAL)
        contributions.append(
            Contribution(
                factor=factor,
                value=value,
                weight=weights.get(factor, Decimal(0)),
                estimated=estimated,
            )
        )

    raw = sum((c.contribution for c in contributions), Decimal(0))
    normalised = _normalise(raw, weights)

    floored = False
    if inputs.affects_live_users and normalised < LIVE_HARM_FLOOR:
        normalised = LIVE_HARM_FLOOR
        floored = True

    return Score(
        value=normalised,
        band=band_for(normalised),
        contributions=tuple(contributions),
        floored_for_live_harm=floored,
    )


def band_for(value: Decimal) -> Band:
    if value >= P1_THRESHOLD:
        return Band.P1
    if value >= P2_THRESHOLD:
        return Band.P2
    if value >= P3_THRESHOLD:
        return Band.P3
    return Band.P4


def _normalise(raw: Decimal, weights: dict[Factor, Decimal]) -> Decimal:
    """Map the achievable range onto 0..1.

    Dividing by a fixed constant put a task with nothing going for it at 0.5,
    which made "no merit" look like "middling". The range is derived from the
    weights instead, so the bottom of the scale is genuinely the bottom.
    """
    best = sum(
        (weight for factor, weight in weights.items() if not factor.is_a_penalty),
        Decimal(0),
    )
    worst = sum(
        (weight for factor, weight in weights.items() if factor.is_a_penalty),
        Decimal(0),
    )
    span = best + worst
    if span == 0:  # pragma: no cover - a weightless configuration
        return Decimal(0)
    return _clamp((raw + worst) / span)


def _clamp(value: Decimal) -> Decimal:
    return max(Decimal(0), min(Decimal(1), value))

"""Logging money from a message.

The whole value is that it costs nothing: type a line while walking to the car
and it is recorded. Anything requiring a form would simply not get used, and
an unused ledger tells him nothing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from aos.app.finance.goals import Goals
from aos.app.finance.ledger import EarningDetail, ExpenseDetail, Ledger
from aos.domain.finance.money import Money
from aos.domain.finance.records import Certainty, ExpenseCategory, Recurrence, Stream
from aos.domain.goals.pace import Verdict

# "40k", "1.5l", "2 lakh", "40000"
_AMOUNT = re.compile(
    r"(?P<number>\d[\d,]*\.?\d*)\s*(?P<scale>k|l|lakh|lakhs|cr|crore|crores)?\b",
    re.IGNORECASE,
)
_SCALES = {
    "k": 1_000,
    "l": 1_00_000,
    "lakh": 1_00_000,
    "lakhs": 1_00_000,
    "cr": 1_00_00_000,
    "crore": 1_00_00_000,
    "crores": 1_00_00_000,
}

EARNED_EXAMPLE = "earned 40k from client"
HELP = f"{EARNED_EXAMPLE} · spent 2400 on tools for railzy · money · goal"


def parse_amount(text: str) -> Money | None:
    match = _AMOUNT.search(text)
    if match is None:
        return None
    number = float(match.group("number").replace(",", ""))
    scale = (match.group("scale") or "").lower()
    return Money.of(number * _SCALES.get(scale, 1))


def parse_stream(text: str) -> Stream:
    lowered = text.lower()
    for stream in Stream:
        if stream.value in lowered:
            return stream
    # A few words people actually use, mapped to the stream they mean.
    aliases = {
        "client": Stream.FREELANCE,
        "consult": Stream.SERVICES,
        "job": Stream.SALARY,
        "brand": Stream.SPONSORSHIP,
        "youtube": Stream.CONTENT,
        "reel": Stream.CONTENT,
        "adsense": Stream.CONTENT,
    }
    for word, stream in aliases.items():
        if word in lowered:
            return stream
    return Stream.OTHER


def parse_category(text: str) -> ExpenseCategory:
    lowered = text.lower()
    for category in ExpenseCategory:
        if category.value.replace("-", " ") in lowered:
            return category
    aliases = {
        "server": ExpenseCategory.INFRASTRUCTURE,
        "hosting": ExpenseCategory.INFRASTRUCTURE,
        "domain": ExpenseCategory.INFRASTRUCTURE,
        "subscription": ExpenseCategory.TOOLS,
        "editor": ExpenseCategory.CONTENT_PRODUCTION,
        "lawyer": ExpenseCategory.LEGAL,
        "registration": ExpenseCategory.LEGAL,
        "ads": ExpenseCategory.MARKETING,
    }
    for word, category in aliases.items():
        if word in lowered:
            return category
    return ExpenseCategory.OTHER


@dataclass(frozen=True)
class MoneyCommands:
    ledger: Ledger
    goals: Goals

    def earned(self, text: str) -> str:
        amount = parse_amount(text)
        if amount is None or not amount.is_positive:
            return f"How much? Try: {EARNED_EXAMPLE}"

        stream = parse_stream(text)
        pipeline = any(word in text.lower() for word in ("expect", "invoice", "due", "should"))
        self.ledger.record_earning(
            amount,
            stream,
            EarningDetail(
                certainty=Certainty.EXPECTED if pipeline else Certainty.ACTUAL,
                note=text.strip()[:200],
            ),
        )
        self.goals.refresh_from_records()

        kind = "expected" if pipeline else "banked"
        recorded = f"{kind.title()} {amount.format()} against {stream.value}."
        standing = self._one_line_standing()
        if not standing:
            return recorded
        return recorded + chr(10) + standing

    def spent(self, text: str) -> str:
        amount = parse_amount(text)
        if amount is None or not amount.is_positive:
            return "How much? Try: spent 2400 on tools for railzy"

        lowered = text.lower()
        recurring = any(word in lowered for word in ("monthly", "a month", "per month"))
        annual = any(word in lowered for word in ("yearly", "annual", "a year", "per year"))
        project = next(
            (stream.value for stream in Stream if f"for {stream.value}" in lowered), None
        )

        self.ledger.record_expense(
            amount,
            parse_category(text),
            ExpenseDetail(
                project_key=project,
                recurrence=(
                    Recurrence.ANNUAL
                    if annual
                    else Recurrence.MONTHLY
                    if recurring
                    else Recurrence.ONE_OFF
                ),
                note=text.strip()[:200],
            ),
        )
        where = f" against {project}" if project else ""
        return f"Recorded {amount.format()}{where}."

    def position(self) -> str:
        position = self.ledger.position()
        lines = [
            f"Gross    {position.gross.format()}",
            f"Spent    {position.expenses.format()}",
            f"Net      {position.net.format()}",
        ]
        burn = self.ledger.monthly_burn()
        if burn.is_positive:
            lines.append(f"Burn     {burn.format()} a month")

        pipeline = self.ledger.pipeline()
        if pipeline.is_positive:
            lines.append(f"Pipeline {pipeline.format()} (weighted, not counted above)")

        bleeding = [p for p in self.ledger.by_project() if p.position.loss_making]
        for project in bleeding:
            cost = project.bleeding_monthly
            if cost is not None:
                lines.append(f"! {project.project_key} is down {cost.format()}")

        for candidate in self.ledger.cancel_candidates():
            lines.append(
                f"? {candidate.project_key}: {candidate.monthly_cost.format()} a month, "
                f"{candidate.reason}"
            )
        return "\n".join(lines)

    def standing(self) -> str:
        standing = self.goals.standing()
        if standing is None:
            return "No goal is configured."

        assessment = standing.assessment
        goal = standing.goal

        if assessment.verdict is Verdict.NO_TARGET:
            return "No target set, so there is nothing to measure against yet."

        if assessment.verdict is Verdict.INSUFFICIENT_HISTORY:
            return (
                f"Banked {goal.describe_value(goal.current)} of "
                f"{goal.describe_value(goal.target_or_zero)}.\n"
                f"No projection yet: {assessment.limiting_factor}."
            )

        lines = [
            f"Banked     {goal.describe_value(goal.current)}",
            f"Target     {goal.describe_value(goal.target_or_zero)}",
            f"Needed     {goal.describe_value(assessment.required.per_month)} a month",
            f"Running at {goal.describe_value(assessment.actual.per_month)} a month",
            f"{assessment.days_remaining} days left · {assessment.verdict.value}",
        ]
        if standing.explanation:
            lines.append("")
            lines.append(standing.explanation)
        return "\n".join(lines)

    def _one_line_standing(self) -> str:
        standing = self.goals.standing()
        if standing is None or not standing.assessment.projects:
            return ""
        goal = standing.goal
        target = goal.describe_value(goal.target_or_zero)
        return (
            f"{goal.describe_value(goal.current)} of {target} · {standing.assessment.verdict.value}"
        )

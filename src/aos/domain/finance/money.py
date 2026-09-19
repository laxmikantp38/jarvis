"""Money as integer minor units.

Floats lose paise, and a system whose entire job is telling someone whether
they are on track cannot afford to be approximately right about money.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

MINOR_UNITS = 100
# Indian grouping: three digits, then pairs.
FIRST_GROUP = 3
PAIR = 2
LAKH = 100_00_000  # in paise
CRORE = 100 * LAKH


@dataclass(frozen=True, slots=True, order=True)
class Money:
    paise: int
    currency: str = "INR"

    @classmethod
    def of(cls, amount: float | str | Decimal, currency: str = "INR") -> Money:
        quantised = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return cls(int(quantised * MINOR_UNITS), currency)

    @classmethod
    def zero(cls, currency: str = "INR") -> Money:
        return cls(0, currency)

    @property
    def major(self) -> Decimal:
        return Decimal(self.paise) / MINOR_UNITS

    def __add__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money(self.paise + other.paise, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money(self.paise - other.paise, self.currency)

    def __mul__(self, factor: float) -> Money:
        return Money(round(self.paise * factor), self.currency)

    def divided_over(self, parts: int) -> Money:
        """Per-day, per-week and per-month pace all come from this."""
        if parts <= 0:
            msg = "cannot divide money over a non-positive number of parts"
            raise ValueError(msg)
        return Money(self.paise // parts, self.currency)

    def ratio_to(self, other: Money) -> float:
        """How many times `other` this is. Infinite when the other is nothing."""
        self._same_currency(other)
        if other.paise == 0:
            return float("inf") if self.paise else 0.0
        return self.paise / other.paise

    @property
    def is_positive(self) -> bool:
        return self.paise > 0

    def _same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            msg = f"cannot combine {self.currency} and {other.currency}"
            raise ValueError(msg)

    def format(self) -> str:
        """Indian grouping, because that is how the target was stated."""
        sign = "-" if self.paise < 0 else ""
        whole = abs(self.paise) // MINOR_UNITS

        if abs(self.paise) >= CRORE:
            return f"{sign}Rs {abs(self.paise) / CRORE:.2f} crore"
        if abs(self.paise) >= LAKH:
            return f"{sign}Rs {abs(self.paise) / LAKH:.2f} lakh"
        return f"{sign}Rs {_group_indian(whole)}"


def _group_indian(value: int) -> str:
    """1234567 becomes 12,34,567: last three digits, then pairs."""
    text = str(value)
    if len(text) <= FIRST_GROUP:
        return text
    head, tail = text[:-FIRST_GROUP], text[-FIRST_GROUP:]
    groups: list[str] = []
    while len(head) > PAIR:
        groups.insert(0, head[-PAIR:])
        head = head[:-PAIR]
    if head:
        groups.insert(0, head)
    return ",".join([*groups, tail])

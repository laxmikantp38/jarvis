"""A day that could actually happen.

Two rules make this different from a to-do list. Fixed commitments are
immovable, so the plan is built around the day he really has rather than an
imaginary empty one. And it deliberately under-fills: a plan with no slack is
a plan that fails at the first interruption and then gets abandoned.

When the work does not fit, the lowest-value items are dropped and named.
Compressing estimates to make things fit is how a plan becomes a lie.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import StrEnum

from aos.domain.priority.scoring import Band

# At least this share of discretionary time is left unallocated.
BUFFER_SHARE = Decimal("0.20")

# Nothing that needs real thought is scheduled after this; the answer would be
# worse than not doing it.
DEEP_WORK_CUTOFF = time(22, 30)


class Attention(StrEnum):
    DEEP = "deep"
    SHALLOW = "shallow"
    AUDIO = "audio"

    @property
    def needs_a_clear_head(self) -> bool:
        return self is Attention.DEEP


@dataclass(frozen=True, slots=True)
class Commitment:
    """Something already true about the day. The planner works around these."""

    name: str
    start: time
    end: time
    attention_available: Attention | None = None
    """Set where the time is usable for something, e.g. a commute is audio."""

    @property
    def minutes(self) -> int:
        return _minutes_between(self.start, self.end)

    def overlaps(self, other: Commitment) -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True, slots=True)
class Candidate:
    task_id: str
    title: str
    project_key: str
    band: Band
    score: Decimal
    minutes: int
    attention: Attention = Attention.SHALLOW
    protected: bool = False
    """A protected block is placed before anything competes for the time."""


@dataclass(frozen=True, slots=True)
class Slot:
    start: time
    end: time
    attention: Attention

    @property
    def minutes(self) -> int:
        return _minutes_between(self.start, self.end)


@dataclass(frozen=True, slots=True)
class Placement:
    candidate: Candidate
    start: time
    end: time


@dataclass(frozen=True, slots=True)
class Dropped:
    candidate: Candidate
    reason: str


@dataclass(frozen=True, slots=True)
class Plan:
    on: date
    placements: tuple[Placement, ...]
    dropped: tuple[Dropped, ...]
    buffer_minutes: int
    available_minutes: int

    @property
    def planned_minutes(self) -> int:
        return sum(_minutes_between(p.start, p.end) for p in self.placements)

    @property
    def is_overcommitted(self) -> bool:
        """Should never be true. If it is, the planner has a bug."""
        return self.planned_minutes > self.available_minutes - self.buffer_minutes

    def describe(self) -> list[str]:
        lines = [
            f"{p.start:%H:%M}  {p.candidate.title}  ({p.candidate.band})"
            for p in self.placements
        ]
        if self.dropped:
            lines.append("")
            lines.append("Not today:")
            lines.extend(f"  {d.candidate.title} - {d.reason}" for d in self.dropped)
        return lines


def free_slots(commitments: list[Commitment], day_start: time, day_end: time) -> list[Slot]:
    """What is left once the immovable parts of the day are taken out."""
    busy = sorted(commitments, key=lambda c: c.start)
    slots: list[Slot] = []
    cursor = day_start

    for commitment in busy:
        if commitment.start > cursor:
            slots.append(Slot(cursor, commitment.start, Attention.DEEP))
        # A commute is dead time unless it is usable, and then only for audio.
        if commitment.attention_available is not None:
            slots.append(
                Slot(commitment.start, commitment.end, commitment.attention_available)
            )
        cursor = max(cursor, commitment.end)

    if cursor < day_end:
        slots.append(Slot(cursor, day_end, Attention.DEEP))
    return [slot for slot in slots if slot.minutes > 0]


def build(
    on: date,
    candidates: list[Candidate],
    commitments: list[Commitment],
    day_start: time,
    day_end: time,
) -> Plan:
    slots = free_slots(commitments, day_start, day_end)
    discretionary = sum(slot.minutes for slot in slots if slot.attention is not Attention.AUDIO)
    buffer_minutes = int(discretionary * BUFFER_SHARE)

    # Protected blocks first, then by score. Protection is the whole point:
    # the thing that never gets time otherwise has to be placed before the
    # louder work takes the day.
    ordered = sorted(candidates, key=lambda c: (not c.protected, -c.score))

    placements: list[Placement] = []
    dropped: list[Dropped] = []
    remaining = {slot: slot.minutes for slot in slots}
    spent = 0
    ceiling = max(0, discretionary - buffer_minutes)

    for candidate in ordered:
        slot = _slot_for(candidate, slots, remaining, on)
        if slot is None:
            dropped.append(Dropped(candidate, _why_not(candidate, remaining)))
            continue
        counts_against_ceiling = slot.attention is not Attention.AUDIO
        if counts_against_ceiling and spent + candidate.minutes > ceiling:
            dropped.append(Dropped(candidate, "no room left without eating the buffer"))
            continue

        start = _start_of(slot, remaining)
        placements.append(
            Placement(candidate=candidate, start=start, end=_plus(start, candidate.minutes))
        )
        remaining[slot] -= candidate.minutes
        if counts_against_ceiling:
            spent += candidate.minutes

    placements.sort(key=lambda p: p.start)
    return Plan(
        on=on,
        placements=tuple(placements),
        dropped=tuple(dropped),
        buffer_minutes=buffer_minutes,
        available_minutes=discretionary,
    )


def _slot_for(
    candidate: Candidate, slots: list[Slot], remaining: dict[Slot, int], on: date
) -> Slot | None:
    for slot in slots:
        if remaining[slot] < candidate.minutes:
            continue
        if not _attention_fits(candidate.attention, slot.attention):
            continue
        if candidate.attention.needs_a_clear_head and _too_late(slot, remaining):
            continue
        return slot
    return None


def _attention_fits(needed: Attention, available: Attention) -> bool:
    """Audio time takes only audio work; a desk takes anything."""
    if available is Attention.AUDIO:
        return needed is Attention.AUDIO
    if available is Attention.SHALLOW:
        return needed is not Attention.DEEP
    return True


def _too_late(slot: Slot, remaining: dict[Slot, int]) -> bool:
    return _start_of(slot, remaining) >= DEEP_WORK_CUTOFF


def _start_of(slot: Slot, remaining: dict[Slot, int]) -> time:
    used = slot.minutes - remaining[slot]
    return _plus(slot.start, used)


def _why_not(candidate: Candidate, remaining: dict[Slot, int]) -> str:
    if candidate.attention is Attention.DEEP and all(
        _start_of(slot, remaining) >= DEEP_WORK_CUTOFF
        for slot in remaining
        if remaining[slot] >= candidate.minutes
    ):
        return "only late slots left, and this needs a clear head"
    return f"no {candidate.minutes}-minute gap it fits in"


def _minutes_between(start: time, end: time) -> int:
    return max(0, (_as_minutes(end) - _as_minutes(start)))


def _as_minutes(moment: time) -> int:
    return moment.hour * 60 + moment.minute


def _plus(moment: time, minutes: int) -> time:
    total = _as_minutes(moment) + minutes
    return (datetime.min + timedelta(minutes=total)).time()

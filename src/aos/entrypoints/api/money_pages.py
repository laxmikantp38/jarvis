"""The money pages.

Kept out of the app factory so that neither grows past the size a person can
hold in their head (AD-20).
"""

from __future__ import annotations

from collections.abc import Callable
from html import escape
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from aos.entrypoints.api.render import Chrome, empty, instrument, kv, page, table

if TYPE_CHECKING:
    from aos.entrypoints.service.wiring import Runtime


def register_money_pages(app: FastAPI, runtime: Runtime, chrome: Callable[[], Chrome]) -> None:
    @app.get("/goals", response_class=HTMLResponse)
    def goals() -> str:
        standing = runtime.goal_engine.standing()
        if standing is None:
            body = empty("No goal configured", "Set one in config.toml under [goals].")
            return page(chrome(), "/goals", "Goals", "Nothing to measure against.", body)

        goal, result = standing.goal, standing.assessment
        stripe = {
            "unreachable-under-current-assumptions": "crit",
            "behind": "warn",
        }.get(result.verdict.value, "ok")

        panels = [
            instrument(
                goal.name,
                f'<div class="big">{escape(goal.describe_value(goal.current))}</div>'
                + kv("target", goal.describe_value(goal.target_or_zero))
                + kv("days left", str(result.days_remaining))
                + kv("confidence", result.confidence.value),
                stripe=stripe,
                pill=result.verdict.value.replace("-under-current-assumptions", ""),
            )
        ]

        if result.projects:
            panels.append(
                instrument(
                    "Pace",
                    kv("needed", goal.describe_value(result.required.per_month) + " / month")
                    + kv("running at", goal.describe_value(result.actual.per_month) + " / month")
                    + kv(
                        "projected",
                        goal.describe_value(result.projected)
                        if result.projected is not None
                        else "-",
                    )
                    + kv(
                        "gap",
                        goal.describe_value(result.gap) if result.gap is not None else "-",
                    ),
                    stripe=stripe,
                )
            )
        else:
            panels.append(
                instrument(
                    "Pace",
                    empty(
                        result.verdict.value.replace("-", " ").capitalize(),
                        result.limiting_factor or "Nothing to project from yet.",
                    ),
                )
            )

        unallocated = runtime.goal_engine.unallocated()
        if unallocated:
            panels.append(
                instrument(
                    "Unallocated",
                    "".join(kv(g.name, "no target") for g in unallocated),
                    pill=f"{len(unallocated)} without a target",
                )
            )

        explanation = (
            f'<div class="empty" style="text-align:left">{escape(standing.explanation)}</div>'
            if standing.explanation
            else ""
        )
        return page(
            chrome(),
            "/goals",
            "Goals",
            "Computed from actual money only. Pipeline is shown on the revenue page.",
            '<div class="grid">' + "".join(panels) + "</div>" + explanation,
        )

    @app.get("/revenue", response_class=HTMLResponse)
    def revenue() -> str:
        position = runtime.ledger.position()
        pipeline = runtime.ledger.pipeline()
        burn = runtime.ledger.monthly_burn()
        projects = runtime.ledger.by_project()
        candidates = runtime.ledger.cancel_candidates()
        slipped = runtime.ledger.slipped()

        panels = [
            instrument(
                "Position",
                kv("gross", position.gross.format())
                + kv("spent", position.expenses.format())
                + kv("net", position.net.format())
                + kv("burn", burn.format() + " / month"),
                stripe="crit" if position.loss_making else "ok",
            ),
            instrument(
                "Not counted above",
                kv("pipeline, weighted", pipeline.format()) + kv("slipped", str(len(slipped))),
                pill="hoped for",
            ),
        ]

        rows = [
            [
                p.project_key,
                p.position.gross.format(),
                p.position.expenses.format(),
                p.position.net.format(),
            ]
            for p in projects
        ]
        table_or_empty = (
            table(["Project", "Gross", "Spent", "Net"], rows)
            if rows
            else empty(
                "Nothing recorded yet",
                "Log something: ",
                "earned 40k from client",
            )
        )

        warnings = "".join(
            f'<div class="empty" style="text-align:left">'
            f"{escape(c.project_key)} costs {escape(c.monthly_cost.format())} a month and has "
            f"{escape(c.reason)}.</div>"
            for c in candidates
        )

        return page(
            chrome(),
            "/revenue",
            "Revenue",
            "Actual money only in the position. Nothing here is an estimate.",
            '<div class="grid">' + "".join(panels) + "</div>" + table_or_empty + warnings,
        )

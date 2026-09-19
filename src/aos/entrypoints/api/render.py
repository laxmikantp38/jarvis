"""HTML for the local interface.

Server-rendered from plain functions: no build step, no node toolchain, nothing
to keep alive. For a single-user page that mostly shows state, a template
engine would be a dependency that earns nothing.

The palette and typography come from the UX direction: an instrument panel
rather than a consumer dashboard, with semantic colour held separate from the
accent so an alert never looks like a button.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from html import escape

STYLE = """
:root{
  --ground:#080C11; --surface:#101822; --surface-2:#16212D;
  --rule:#1E2C3A; --rule-soft:#141F2A;
  --ink:#DEE8F0; --dim:#75899A; --faint:#4A5C6B;
  --accent:#3ED0DE; --ok:#4FB477; --warn:#E0A050; --crit:#E0605E;
  --mono:ui-monospace,"Cascadia Mono","SF Mono",Menlo,Consolas,monospace;
  --sans:ui-sans-serif,system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.layout{display:grid;grid-template-columns:200px 1fr;min-height:100vh}
@media (max-width:760px){.layout{grid-template-columns:1fr}}
nav{border-right:1px solid var(--rule);background:var(--surface);padding:18px 0}
nav .brand{padding:0 16px 14px;border-bottom:1px solid var(--rule-soft);margin-bottom:10px}
nav .brand b{font-family:var(--mono);font-size:13px;letter-spacing:.18em;color:var(--accent)}
nav .brand span{display:block;font-family:var(--mono);font-size:10px;color:var(--faint)}
nav a{display:flex;justify-content:space-between;padding:6px 16px;font-size:13px;
  color:var(--dim);border-left:2px solid transparent}
nav a.on{color:var(--ink);border-left-color:var(--accent);background:var(--surface-2)}
nav a:hover{text-decoration:none;color:var(--ink)}
nav .count{font-family:var(--mono);font-size:10px;color:var(--faint)}
main{padding:24px 26px 56px;max-width:1000px}
h1{font-size:22px;margin:0 0 4px;font-weight:600;letter-spacing:-.01em}
.sub{color:var(--dim);font-size:13px;margin:0 0 22px}
.legend{font-family:var(--mono);font-size:10px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--faint);margin:0}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.inst{border:1px solid var(--rule);background:var(--surface);position:relative}
.inst>.bar{display:flex;justify-content:space-between;align-items:center;
  padding:7px 12px;border-bottom:1px solid var(--rule-soft)}
.inst>.body{padding:12px}
.stripe{position:absolute;left:0;top:0;bottom:0;width:2px}
.stripe.ok{background:var(--ok)}.stripe.warn{background:var(--warn)}
.stripe.crit{background:var(--crit)}.stripe.idle{background:var(--rule)}
.pill{display:inline-block;font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;
  text-transform:uppercase;padding:2px 6px;border:1px solid var(--rule);color:var(--dim)}
.pill.ok{color:var(--ok);border-color:#2c5f43}
.pill.warn{color:var(--warn);border-color:#6b5227}
.pill.crit{color:var(--crit);border-color:#6b3130}
.big{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:26px;line-height:1.1}
.kv{display:flex;justify-content:space-between;gap:12px;padding:3px 0;font-size:13px}
.kv .k{color:var(--dim)}
.kv .v{font-family:var(--mono);font-variant-numeric:tabular-nums}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;font-family:var(--mono);font-size:10px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--faint);font-weight:400;padding:6px 10px;
  border-bottom:1px solid var(--rule)}
td{padding:7px 10px;border-bottom:1px solid var(--rule-soft)}
tr:last-child td{border-bottom:none}
td.num{font-family:var(--mono);font-variant-numeric:tabular-nums;color:var(--dim);
  white-space:nowrap}
.empty{border:1px dashed var(--rule);padding:22px;text-align:center;color:var(--dim);
  font-size:13px}
.empty b{display:block;color:var(--ink);font-size:14px;margin-bottom:4px;font-weight:600}
.empty code{font-family:var(--mono);font-size:12px;color:var(--accent)}
footer{margin-top:28px;padding-top:12px;border-top:1px solid var(--rule-soft);
  font-family:var(--mono);font-size:10.5px;color:var(--faint)}
"""

SECTIONS: list[tuple[str, str]] = [
    ("/", "Dashboard"),
    ("/agent", "Agent"),
    ("/tasks", "Tasks"),
    ("/schedule", "Schedule"),
    ("/projects", "Projects"),
    ("/goals", "Goals"),
    ("/revenue", "Revenue"),
    ("/memory", "Memory"),
    ("/decisions", "Decisions"),
    ("/experiments", "Experiments"),
    ("/notifications", "Notifications"),
    ("/integrations", "Integrations"),
    ("/audit", "Audit"),
    ("/settings", "Settings"),
]


@dataclass(frozen=True)
class Chrome:
    agent_name: str
    environment: str
    counts: dict[str, int]


def page(chrome: Chrome, path: str, title: str, subtitle: str, body: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{escape(title)} &middot; {escape(chrome.agent_name)}</title>"
        f'<style>{STYLE}</style></head><body><div class="layout">'
        f"{_nav(chrome, path)}"
        f'<main><h1>{escape(title)}</h1><p class="sub">{escape(subtitle)}</p>'
        f"{body}"
        f"<footer>{escape(chrome.agent_name)} &middot; {escape(chrome.environment)} "
        "&middot; local only, not reachable from another machine</footer>"
        "</main></div></body></html>"
    )


def _nav(chrome: Chrome, current: str) -> str:
    links = []
    for path, label in SECTIONS:
        count = chrome.counts.get(label.lower())
        badge = f'<span class="count">{count}</span>' if count else ""
        on = " on" if path == current else ""
        links.append(f'<a class="item{on}" href="{path}">{escape(label)}{badge}</a>')
    return (
        f'<nav><div class="brand"><b>{escape(chrome.agent_name.upper())}</b>'
        f"<span>{escape(chrome.environment)}</span></div>{''.join(links)}</nav>"
    )


def instrument(label: str, body: str, *, stripe: str = "idle", pill: str = "") -> str:
    badge = f'<span class="pill {stripe}">{escape(pill)}</span>' if pill else ""
    return (
        f'<div class="inst"><span class="stripe {stripe}"></span>'
        f'<div class="bar"><span class="legend">{escape(label)}</span>{badge}</div>'
        f'<div class="body">{body}</div></div>'
    )


def kv(key: str, value: str) -> str:
    return (
        f'<div class="kv"><span class="k">{escape(key)}</span>'
        f'<span class="v">{escape(value)}</span></div>'
    )


def table(headers: list[str], rows: Iterable[list[str]]) -> str:
    head = "".join(f"<th>{escape(h)}</th>" for h in headers)
    body = "".join(
        "<tr>"
        + "".join(
            f'<td class="num">{escape(cell)}</td>'
            if index and cell and cell[0].isdigit()
            else f"<td>{escape(cell)}</td>"
            for index, cell in enumerate(row)
        )
        + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def empty(headline: str, explanation: str, how: str = "") -> str:
    """What a section looks like before it has anything to show.

    Never a zero and never a flat chart: saying nothing is here yet is honest,
    and a fabricated value is not.
    """
    hint = f"<div><code>{escape(how)}</code></div>" if how else ""
    return f'<div class="empty"><b>{escape(headline)}</b>{escape(explanation)}{hint}</div>'

#!/usr/bin/env python3
"""workpapers-mcp: an MCP server over my ITGC audit workpaper pack.

Exposes the five markdown workpapers (plan, risk and control matrix,
test procedures, findings, management letter) as tools any MCP-capable
model can call: read a workpaper, list findings, trace a control from
risk to test result, and see what is still open.

Run (stdio):  workpapers-mcp
Wire into Claude Code:
  claude mcp add workpapers -- workpapers-mcp
"""

import os
import re
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

DATA_DIR = Path(os.environ.get("WORKPAPERS_DATA_DIR", Path.home() / "aiProjects/aminWork/automation-portfolio/itgc-audit-workpapers"))

# Drafting notes to self sit in square brackets and never leave this server.
REVIEW_NOTE = re.compile(r"\[REVIEW NOTE[^\]]*\]", re.I)
CAP = 25

server = MCPServer(
    "workpapers",
    instructions=(
        "Read-only tools over an IT General Controls audit workpaper pack: "
        "audit plan, risk and control matrix, test procedures, findings "
        "and management letter, all plain markdown files."
    ),
)

# Every tool only reads local markdown files, so one shared annotation set.
READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)


def _read(n: int) -> str:
    files = sorted(DATA_DIR.glob(f"{n:02d}-*.md"))
    if not files:
        return ""
    return REVIEW_NOTE.sub("[drafting note removed]",
                           files[0].read_text(encoding="utf-8")).strip()


def _capped(lines: list) -> list:
    extra = [f"...and {len(lines) - CAP} more"] if len(lines) > CAP else []
    return lines[:CAP] + extra


def _findings() -> list:
    """(id, title, rating, status, body) per '## F-N. Title' section in workpaper 4."""
    out = []
    for m in re.finditer(r"^## (F-\d+)\. (.+?)\n(.*?)(?=^## |\Z)",
                         _read(4), re.M | re.S):
        r = re.search(r"\*\*Rating: (.+?)\. Status: (.+?)\.\*\*", m.group(3))
        out.append((m.group(1), m.group(2).strip(),
                    r.group(1) if r else "unrated",
                    r.group(2) if r else "unknown", m.group(3)))
    return out


def _tests() -> dict:
    """Test ID to its full paragraph, from bold '**T-XX Name.**' blocks in workpaper 3."""
    return {m.group(1): m.group(0).strip()
            for m in re.finditer(r"^\*\*(T-[A-Z]\d+) .*?(?=\n\s*\n|\Z)",
                                 _read(3), re.M | re.S)}


def _matrix() -> dict:
    """Control ID to (domain, row cells) from the tables in workpaper 2."""
    rows, domain = {}, ""
    for line in _read(2).splitlines():
        if line.startswith("## "):
            domain = line[3:].strip()
        m = re.match(r"\|\s*([A-Z]\d+)\s*\|(.*)\|\s*$", line)
        if m:
            rows[m.group(1)] = (domain, [c.strip() for c in m.group(2).split("|")])
    return rows


@server.tool(annotations=READ_ONLY)
def get_workpaper(number: int) -> str:
    """Full markdown text of one workpaper, 1 to 5: plan, risk and control
    matrix, test procedures, findings, management letter."""
    text = _read(number) if 1 <= number <= 5 else ""
    return text or f"No workpaper {number}. Valid numbers are 1 to 5."


@server.tool(annotations=READ_ONLY)
def list_findings(rating: str = "") -> str:
    """Findings from workpaper 4 with rating and status. Optional rating
    filter (High, Medium, Low), case-insensitive."""
    rows = [f for f in _findings() if rating.lower() in f[2].lower()]
    if not rows:
        return f"No findings rated {rating!r}." if rating else "No findings found."
    lines = [f"- {i} {t} | {r} | {s}" for i, t, r, s, _ in rows]
    return f"{len(rows)} finding(s):\n" + "\n".join(_capped(lines))


@server.tool(annotations=READ_ONLY)
def control_lookup(control_id: str) -> str:
    """Trace one control end to end: its risk and control row from the
    matrix, its test procedure and result, and findings that cite it.
    Accepts A1 or T-A1 style IDs."""
    cid = control_id.strip().upper().removeprefix("T-")
    row = _matrix().get(cid)
    if not row:
        return f"No control {control_id!r} in the risk and control matrix."
    domain, cells = row
    risk, control, where, criteria, test = (cells + [""] * 5)[:5]
    out = [f"{cid} ({domain})", f"Risk: {risk}", f"Control: {control}",
           f"Where it lives: {where}", f"Criteria: {criteria}", ""]
    out.append(_tests().get(test, f"No test procedure {test} in workpaper 3."))
    cited = [f"{i} {t}" for i, t, _, _, body in _findings()
             if re.search(rf"\b{re.escape(test)}\b", body)]
    out += ["", "Findings citing " + test + ": " + (", ".join(cited) or "none")]
    return "\n".join(out)


@server.tool(annotations=READ_ONLY)
def open_items() -> str:
    """What is not closed yet: findings not remediated, tests without a
    plain Pass result, and drafting placeholders still in the pack."""
    items = [f"Finding {i} {t}: {s}" for i, t, _, s, _ in _findings()
             if not s.lower().startswith("remediated")]
    for tid, block in _tests().items():
        m = re.search(r"Result: (.+)", block)
        result = m.group(1).strip() if m else "no result recorded"
        if not result.startswith("Pass"):
            items.append(f"Test {tid}: {result}")
    for n in range(1, 6):
        count = _read(n).count("[drafting note removed]")
        if count:
            items.append(f"Workpaper {n}: {count} unfinished drafting placeholder(s)")
    if not items:
        return "No open items."
    return f"{len(items)} open item(s):\n" + "\n".join(f"- {x}" for x in _capped(items))


def main():
    server.run()


if __name__ == "__main__":
    main()

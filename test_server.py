"""Smoke test over a synthetic workpaper pack. Run: python test_server.py (or pytest)."""

import tempfile
from pathlib import Path

import server

WP = {
    "01-plan.md": "# Workpaper 1: Plan\n\nScope is a demo account.\n",
    "02-rcm.md": (
        "# Workpaper 2: Matrix\n\n## Domain 1: Access\n\n"
        "| ID | Risk | Control | Where it lives | Criteria | Test |\n"
        "|---|---|---|---|---|---|\n"
        "| A1 | Demo risk | Demo MFA control | IAM | CIS 1.1 | T-A1 |\n\n"
        "## Domain 3: Operations\n\n"
        "| ID | Risk | Control | Where it lives | Criteria | Test |\n"
        "|---|---|---|---|---|---|\n"
        "| O1 | No trail | Logging on | Terraform | CIS 3.1 | T-O1 |\n"
    ),
    "03-tests.md": (
        "# Workpaper 3: Tests\n\n"
        "**T-A1 MFA check.**\nToD: inspect.\nResult: Pass.\n\n"
        "**T-O1 Logging.** ToD/ToE: trail on. Result: see Workpaper 4.\n"
    ),
    "04-findings.md": (
        "# Workpaper 4: Findings\n\n"
        "## F-1. Old gap\n\n**Rating: High. Status: Remediated.**\n\n"
        "Closed. [REVIEW NOTE FOR SOMEONE: private reminder]\n\n"
        "## F-2. Logging gap\n\n**Rating: Low. Status: Accepted.**\n\n"
        "Seen in test T-O1.\n\n## Tracking summary\n\n| Finding | Rating |\n"
    ),
    "05-letter.md": "# Workpaper 5: Letter\n\nAll good.\n",
}


def test_tools():
    with tempfile.TemporaryDirectory() as d:
        server.DATA_DIR = Path(d)
        for name, text in WP.items():
            (server.DATA_DIR / name).write_text(text, encoding="utf-8")

        wp4 = server.get_workpaper(4)
        assert "Old gap" in wp4 and "private reminder" not in wp4
        assert "[drafting note removed]" in wp4
        assert server.get_workpaper(9).startswith("No workpaper 9")

        f = server.list_findings()
        assert f.startswith("2 finding(s)") and "Tracking" not in f
        assert "- F-2 Logging gap | Low | Accepted" in f
        assert "F-1" in server.list_findings("high") and "F-2" not in server.list_findings("high")
        assert server.list_findings("medium").startswith("No findings rated")

        c = server.control_lookup("t-o1")
        assert c.startswith("O1 (Domain 3: Operations)") and "Risk: No trail" in c
        assert "**T-O1 Logging.**" in c and "Findings citing T-O1: F-2 Logging gap" in c
        assert "Findings citing T-A1: none" in server.control_lookup("A1")
        assert server.control_lookup("Z9").startswith("No control")

        o = server.open_items()
        assert o.startswith("3 open item(s)")
        assert "Finding F-2 Logging gap: Accepted" in o and "F-1" not in o
        assert "Test T-O1: see Workpaper 4." in o and "T-A1" not in o
        assert "Workpaper 4: 1 unfinished drafting placeholder(s)" in o


if __name__ == "__main__":
    test_tools()
    print("ok")

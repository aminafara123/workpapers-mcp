# workpapers-mcp

An MCP server over my itgc-audit-workpapers pack: an IT General Controls audit of my own AWS environment, written up as five markdown workpapers. This server exposes that pack as tools any MCP-capable AI client can call.

Audit workpapers are cross-referenced by design. A risk points to a control, the control points to a test, the test points to a finding. Following those links by hand means flipping between files. With this server a model can trace a control from risk to result in one call, or answer "whats still open?" straight from the files.

## Tools

| Tool | What it does |
|---|---|
| `get_workpaper(number)` | Full text of workpaper 1 to 5 |
| `list_findings(rating)` | Findings with rating and status, optional rating filter |
| `control_lookup(control_id)` | One control traced end to end: matrix row, test procedure and result, findings that cite the test |
| `open_items()` | Findings not remediated, tests without a plain Pass, and unfinished drafting placeholders |

## Setup

```bash
pipx install workpapers-mcp
```

`uvx workpapers-mcp` works too if you prefer no install. Hacking on a clone instead:

```bash
python3 -m venv .venv
.venv/bin/pip install mcp
```

Wire it into Claude Code:

```bash
claude mcp add workpapers -- workpapers-mcp
```

Running from a clone, point it at the venv instead:

```bash
claude mcp add workpapers -- /path/to/workpapers-mcp/.venv/bin/python /path/to/workpapers-mcp/workpapers_mcp.py
```

The server reads the pack from `~/aiProjects/aminWork/automation-portfolio/itgc-audit-workpapers`. Point `WORKPAPERS_DATA_DIR` at your own data folder to read it from somewhere else.

## Demo

What it looks like from Claude Code:

```
> trace control A3 in the workpapers

⏺ workpapers · control_lookup("A3")

  A3 (Domain 1: Access)
  Risk: Password-only sign-in is phishable
  Control: MFA enforced on every human identity
  Where it lives: IAM MFA config
  Criteria: CIS 1.10

  **T-A3 MFA enforcement.**
  ToD/ToE: MFA device listing inspected for all 12 demo users.
  Result: Exception, see F-2.

  Findings citing T-A3: F-2 Two users without MFA

> anything still open?

⏺ workpapers · open_items()

  2 open item(s):
  - Finding F-2 Two users without MFA: Open
  - Test T-A3: Exception, see F-2.

⏺ One real gap. Two users have no MFA, raised as F-2 and still open.
  The T-A3 exception is the same issue seen from the test side.
```

The controls and findings above are demo data. The format is exactly what the server returns.

## Design notes

- **Read-only by construction.** Every tool reads markdown files. Nothing writes, deletes or touches the network.
- **Parses the pack as written.** Matrix rows, bold test headings and `## F-N.` finding sections are the real structure of the workpapers, so the tools follow the same cross-references a reviewer would.
- **Drafting notes stay private.** Square bracket `[REVIEW NOTE ...]` placeholders are replaced with a neutral marker before any text leaves the server, and `open_items` counts them so unfinished work still shows up.

## Honest notes

- The parsing is tied to this pack's markdown conventions. A workpaper written in a different layout wont parse without changes to the regexes.
- The pack is a self-audit of one small personal AWS account. The tools make it easier to navigate. They dont add assurance the workpapers dont already carry.
- `open_items` treats any finding whose status doesnt start with "Remediated" as open, so accepted and disclosed limitations show up there on purpose.
- The test lives in `test_server.py` and runs against a synthetic pack in a temp dir. Run it with `python test_server.py` or pytest.

## About

Al Amin Bashir Afara, Dubai · [github.com/aminafara123](https://github.com/aminafara123) · [linkedin.com/in/aminafara](https://www.linkedin.com/in/aminafara)

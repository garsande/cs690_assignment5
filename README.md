# Assignment 5: RoomBook backend

HANDOUT.md says what to do and why. This file covers setup and commands.

## Setup

1. Clone this repository and go into it:

       git clone https://github.com/md685-njit/Assignment-5.git
       cd Assignment-5

2. Create a new, empty repository on your GitHub account (no README, no .gitignore).
   Point your clone at it and push. You cannot push to the course repository.

       git remote set-url origin <your repository URL>
       git push -u origin main

3. Create a virtual environment with Python 3.11 or later, and turn it on.

   macOS and Linux:

       python3 -m venv .venv
       source .venv/bin/activate

   Windows, PowerShell:

       py -3 -m venv .venv
       .venv\Scripts\Activate.ps1

   Windows, Git Bash:

       py -3 -m venv .venv
       source .venv/Scripts/activate

   Turn it on again in every new terminal. With it on, `python` means the right Python
   on every system.
4. Install the packages:

       python -m pip install -r requirements.txt

5. Install your agent tool, if you have not yet, and sign in once by starting it:
   - Claude Code: https://code.claude.com/docs/en/setup, then run `claude`.
   - Antigravity CLI: macOS and Linux,
     `curl -fsSL https://antigravity.google/cli/install.sh | bash`; Windows PowerShell,
     `irm https://antigravity.google/cli/install.ps1 | iex`. Then run `agy`.

   Exit it again for now (`/exit`).
6. Check the setup:

       python tools/check.py setup

## Commands

| Command | What it does |
|---|---|
| `python -m pytest` | Runs all tests |
| `python -m pytest tests/acceptance` | Runs your acceptance tests |
| `python -m pytest tests/legacy` | Runs your characterization tests |
| `python tools/check_layers.py` | Checks the layer rules L1 to L5 in `app/` |
| `python tools/check.py tests` | Counts your acceptance tests by rule and runs them |
| `python tools/check.py` | Runs every check the grader runs by script |
| `uvicorn app.main:create_app --factory --port 8000` | Runs the backend and the page at http://localhost:8000 |
| `python -m http.server 8000 --directory frontend` | Serves only the page, with no backend |
| `python -m legacy.old_format legacy/old_bookings.csv` | Runs the old converter on the sample export |
| `claude` or `agy` | Starts your agent; always from the folder that holds HANDOUT.md |

## What is in this repository

| Path | What it is |
|---|---|
| `HANDOUT.md` | The assignment: what, why, every part, how it is graded |
| `RUBRIC.md` | The grading checklist |
| `REPORT.md` | Your report |
| `LEDGER.md` | Your provenance ledger |
| `AGENTS.md` | Standing instructions for the agent; you add the Backend rules |
| `CLAUDE.md` | For Claude Code: imports `AGENTS.md` |
| `.claude/settings.json` | Claude Code permission rules |
| `agent/agy-permissions.json` | Antigravity CLI permission rules, to merge into your agy settings |
| `docs/spec.md` | The backend specification: the source of truth |
| `docs/adr/0000-template.md` | The template for your ADR |
| `frontend/` | The finished page; do not change |
| `app/` | The backend; empty until Part 6 |
| `legacy/` | The old system's converter and a sample export |
| `tests/conftest.py` | The `client` and `new_client` fixtures; do not change |
| `tests/acceptance/` | Your acceptance tests |
| `tests/legacy/` | Your characterization tests |
| `tools/` | `check.py` and `check_layers.py`; do not change |
| `prompts/` | The prompts you gave AI tools, one file per ledger entry |
| `evidence/` | Evidence files from Parts 4, 6 and 7 |

## Troubleshooting

**`No module named 'app.main'`**
Before Part 6, that is the right failure: the backend does not exist yet. After Part 6,
check that `app/main.py` exists and that you run commands from the folder that holds
HANDOUT.md.

**`ModuleNotFoundError: No module named 'fastapi'`**
The virtual environment is off. Turn it on (Setup step 3) and try again.

**`Address already in use` when starting the server**
Another server is still running on port 8000. Stop it with Ctrl+C in its terminal, or
use `--port 8001` and open http://localhost:8001.

**The page shows "Cannot reach the server"**
The backend is not running, or you opened the page from the file system. Start it with
the `uvicorn` command above and open http://localhost:8000.

**`/permissions` does not show a rule you added**
Check that the settings file is valid JSON (a missing comma breaks the whole file), save
it, and restart the agent. In Claude Code, also accept the workspace trust prompt.

**A subagent does not appear**
Check the file location and that `name:` matches the file name. In Claude Code, restart
after creating the first file in `.claude/agents/`. In Antigravity CLI, check the tool
names letter by letter.

**`database is locked`**
A test or the server still holds a connection. Make sure each repository call opens its
own connection and closes it.

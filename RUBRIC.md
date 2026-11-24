# Assignment 5 rubric

100 points. "Script" items are checked by the grading script, "Read" items by the
instructor. The grader grades the commit tagged `a5-submit` (or, without that tag, the
latest commit on `main` pushed before the deadline). It uses its own copies of
`frontend/`, `tests/conftest.py`, `tools/` and `pytest.ini`.

## A. The backend works: 40 points (Script)

Hidden tests run against your `app/`, through `create_app` as section 3 of the spec says.
Each item earns its points in proportion to the tests in it that pass.

| Item | Rules | What the hidden tests check | Points |
|---|---|---|---|
| A1 | R1, R2 | The rooms; listing by date, by room, in order; bad dates and room filters | 6 |
| A2 | R3, R4, R5 | Request shape, names, and time rules, with their boundaries | 10 |
| A3 | R6, R7 | Unknown rooms; overlap, touching, other rooms and dates; nothing saved on failure | 8 |
| A4 | R8 | Cancel: 204 and empty body, the slot freed, unknown and invalid ids | 3 |
| A5 | R9, R10 | The one error body; the order of checks; failures change nothing; the page; separate and lasting databases | 5 |
| A6 | R11 | The daily limit, including case and spaces, other dates and people, cancelling, and the order with R7 | 8 |

## B. Instructions, permissions and agents: 15 points

| Item | What earns the points | How | Points |
|---|---|---|---|
| B1 | `AGENTS.md` Backend rules cover the six points in Part 1 plus one rule of your own, in your own words, under 30 lines; `CLAUDE.md` imports `AGENTS.md` if you use Claude Code | Read | 3 |
| B2a | Your permission file denies agent edits in `frontend/` and `tests/acceptance/`, both in the commit tagged `a5-tests-locked` and at `a5-submit` | Script | 2 |
| B2b | `evidence/permission-denied.md` shows your prompt, the tool's own refusal (not only the model declining), and the rule that blocked the edit | Read | 2 |
| B3 | For each of `test-writer`, `reviewer` and `contract-checker` (2 points each): the file is in the right place with a matching `name`, a `description` and instructions (1); its tools are least privilege: the reviewer and the contract-checker have no tool that edits files or runs commands, and the test-writer has an edit tool and a run tool (1) | Script | 6 |
| B4 | Each agent's instructions say what it does, what it returns, and when it stops, and cover the points listed for it in Part 2 | Read | 2 |

## C. Tests first, then the build: 22 points (Script)

| Item | What earns the points | Points |
|---|---|---|
| C1 | The tag `a5-tests-locked` exists, and `app/` has no code at that commit (2); every acceptance test at that commit fails or errors (1); at that commit there is at least one test named `test_r<N>_` for each of R1 to R10 (1), and at least 20 tests (1) | 5 |
| C2 | No file that was in `tests/acceptance/` at the lock is changed or deleted at `a5-submit` | 3 |
| C3 | Your acceptance tests pass on your backend (2) and on the instructor's correct reference backend (2), each in proportion to the tests that pass. A test that fails on the reference checks something the spec does not say | 4 |
| C4 | Your acceptance tests catch seeded bugs: the grader runs them against 8 copies of the reference backend, each with one bug that breaks a rule. A copy is caught when a test that passes on the reference fails on it. 1 point per 2 copies caught, rounded up | 4 |
| C5 | `docs/plan.md` has the headings Task 1, Task 2, Task 3 and Not in this change (1); at least 3 commits change `app/` between the lock and the R11 code commit (2) | 3 |
| C6 | `tools/check_layers.py` (the grader's copy) passes: 3 points, minus 1 for each layer rule that fails | 3 |

## D. Reviews, the spec change, decisions, and legacy code: 15 points

| Item | What earns the points | How | Points |
|---|---|---|---|
| D1 | The commit that adds the rule "R11. Daily limit" to `docs/spec.md` comes before the commit that adds `daily_limit` to `app/` (1); so does the commit that adds `daily_limit` to `tests/acceptance/` (1); `tests/acceptance/test_r11_daily_limit.py` exists, has at least 3 tests named `test_r11_`, and they pass on your backend (1) | Script | 3 |
| D2 | `evidence/review.md` and `evidence/contract-check.md` hold real reports from your two read-only agents; REPORT.md, question 4, answers every finding with a commit SHA or a reason; nothing outside the spec was built | Read | 4 |
| D3a | `docs/adr/0001-....md` exists with a Status line and the sections Context, Options considered, Decision and Consequences | Script | 1 |
| D3b | The ADR names at least two real options with a cost each and a decision that follows from them; spec section 7 has at least three decisions, none of which changes sections 1 to 6 | Read | 2 |
| D4 | At least 8 characterization tests in `tests/legacy/` (1); all of them pass on the original `legacy/old_format.py` (1); they catch copies of the original with one behavior changed, 8 copies: 7 or 8 caught earns 2, 4 to 6 earns 1, and none count unless the tests pass on the original (2); the refactored file keeps every behavior of the original (checked by hidden tests), was changed, has type hints on every function, and the characterization tests were committed before it changed (1) | Script | 5 |

## E. Report and ledger: 8 points

| Item | What earns the points | How | Points |
|---|---|---|---|
| E1 | REPORT.md answers all eight questions from your own work, pointing to commits, files, tests or rule IDs; `evidence/page.png` shows the page with a booking made through your backend | Read | 3 |
| E2a | At least 8 ledger entries under "My entries" with all seven fields filled in (1); every entry names a file in `prompts/` that exists (1) | Script | 2 |
| E2b | The entries cover the eight required changes, were written as the work was done, and the `review` and `risk` fields say what you actually checked, changed, rejected, and left unverified | Read | 3 |

## Deductions

- Changes to `frontend/`, `tests/conftest.py`, `tools/`, `pytest.ini` or `requirements.txt`
  are undone before grading. A backend that only works with those changes loses the
  points it fails.
- Fabricated ledger entries, evidence or reports are an academic-integrity matter, not a
  deduction.

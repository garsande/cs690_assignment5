# Assignment 5: Give RoomBook a Backend, with an Agent Team

Individual. 100 points. About 5 hours and 30 minutes of work.

## What you build

RoomBook is a small app for booking library study rooms. Its page is finished: it is in
`frontend/`, it belongs to another team, and you may not change it. It calls an HTTP API
that does not exist yet. Your job is to build that backend in Python (FastAPI and
SQLite), to the specification in `docs/spec.md`, using a coding agent: Claude Code or
Antigravity CLI.

You will not just prompt one agent. You set up a small agent team and run it the way
teams do at work:

- standing instructions for every session (`AGENTS.md`), and permission rules the tool
  enforces, not just asks for;
- three agents you define in files, each with one job and only the tools that job needs:
  a **test-writer**, a read-only **reviewer**, and a read-only **contract-checker** that
  compares what the page sends and expects with what the backend does;
- a clarify step before any code, acceptance tests written and locked before any code, a
  plan before any edit, and a build in three bounded tasks;
- two reviews run side by side, a spec change that goes spec, then test, then code, and
  an architecture decision record;
- an untested piece of legacy code that you pin with characterization tests before the
  agent changes it.

At the end, the page works against your backend: rooms appear, bookings are made and
cancelled, and every rule in the spec is enforced by the backend.

## Why this matters in industry

- Most product work is a frontend and a backend built by different people against an
  agreed contract. When the two drift apart, users see bugs that neither side's tests
  catch. Checking the contract is a real, daily job.
- Teams that use coding agents give them standing instructions, limit what each one may
  touch, and check their work with tests the agent cannot edit. A rule in a prompt is a
  request; a permission rule is enforced.
- Splitting work across agents with one job each (one writes tests, one reviews, one
  checks the contract) is how agent tools are used at scale. A reviewer that cannot edit
  is a useful second opinion because it cannot "fix" its way past a problem.
- Layered backends (routes, service, repository) keep HTTP, business rules and SQL
  apart, so a change to one does not break the others. Architecture decision records
  keep the reasons for a design after the people who made it have moved on.
- Almost every job includes old code without tests. Pinning what it does today, before
  anyone changes it, is the standard first step.

When you finish, you can say in an interview: "I built a FastAPI and SQLite backend to a
written spec with a coding agent and a team of subagents I configured: acceptance tests
first and locked, a plan, bounded tasks, read-only reviewers, a contract check against
the frontend, and characterization tests before refactoring legacy code."

## What you need

- Python 3.11 or later, Git, and a GitHub account.
- One agent tool, used for the whole assignment: **Claude Code** (needs a Claude
  subscription) or **Antigravity CLI** (`agy`, which has a free tier).
- No API key. Nothing in this assignment calls a model from your own code.

## What you write

| File | What it is | Part |
|---|---|---|
| `AGENTS.md`, "Backend rules" section | Standing rules for the backend | 1 |
| Three agent files | `test-writer`, `reviewer`, `contract-checker` | 2 |
| `docs/spec.md`, section 7 | Your decisions on open questions | 3 |
| `tests/acceptance/` | Acceptance tests, written and locked before any code | 4 |
| Your permission file | The lock on `tests/acceptance/` | 4 |
| `docs/plan.md` | The three-task plan | 5 |
| `app/` | The backend, built by the agent in three tasks | 6 |
| `evidence/` | The permission refusal, a screenshot, and two review reports | 4, 6, 7 |
| `docs/spec.md`, `tests/acceptance/test_r11_daily_limit.py`, `app/` | The spec change R11 | 8 |
| `docs/adr/0001-....md` | One architecture decision record | 9 |
| `tests/legacy/test_old_format.py`, `legacy/old_format.py` | Characterization tests, then a refactor | 10 |
| `REPORT.md`, `LEDGER.md`, `prompts/` | Your report and provenance ledger | all |

Do not change `frontend/`, `tests/conftest.py`, `tools/`, `pytest.ini` or
`requirements.txt`, and do not add packages.

## AI policy

AI tools are allowed in this assignment, and Parts 2 to 10 require you to use a coding
agent. Along with your work you submit a provenance ledger that records which tools you
used, what you asked them, and what you did to review their output. Submitting
AI-generated work you have not reviewed misrepresents authorship and is an
academic-integrity violation under the course syllabus, as is fabricating ledger
entries, traces or results. You are responsible for every line you submit, including
lines you did not type, and you may be asked in class to explain any part of your
submission.

Three rules are specific to this assignment:

1. **The agent builds; you decide.** The agent writes the backend code. You choose what
   it may do, read what it did, and accept or reject it. Every decision in section 7 of
   the spec, every answer to a review finding, and the ADR are yours.
2. **Locked tests stay locked.** After Part 4, nobody changes a test file that existed at
   the lock: not the agent and not you. You may add new test files.
3. **The spec comes first.** Never build something the spec does not ask for, even when
   the page or an agent suggests it.

## The provenance ledger

Keep `LEDGER.md` as you go, using exactly this schema. It already contains a worked
example; your own entries go below it, under "My entries".

```
## Entry <n>
artifact:  what this entry covers: a file, a commit SHA, or a document
tool:      product name, model name, model version, and the date of use; when a
           subagent did the work, its name (for example: test-writer subagent)
prompts:   one-line summary each; the verbatim prompts live in prompts/ and are
           referenced here by file path
review:    what you read, what you changed, what you rejected, and why
checks:    the commands you ran and their results
evidence:  the requirement, test, or evidence ID this traces to
risk:      what remains unverified after this change
```

An entry is written when the work is done, not reconstructed at submission time. A
ledger that is one entry per session rather than one per reviewable change is wrong.

Write at least eight entries: one for Part 3; one for Part 4; one for each of the three
tasks in Part 6; one for Part 7; one for the R11 code in Part 8; and one for the
refactor in Part 10. Save every prompt you typed into an AI tool in `prompts/`, one
file per entry, and name that file in the entry.

## Git rules for this assignment

- **Commit before every agent task**, so `git status` shows exactly what the agent
  changed, and `git restore .` undoes it.
- The grader reads your history. Make the commits the steps ask for, in that order, and
  the two tags: `a5-tests-locked` (Part 4) and `a5-submit` (Part 11).
- Never commit `.venv/` or `*.db` files. `.gitignore` already excludes them.

## The steps

The steps take about 5 hours and 30 minutes. Agent tasks sometimes take longer than you
expect, so plan two or three sittings, for example Parts 0 to 4, then Parts 5 to 7, then
Parts 8 to 11.

### Part 0. Set up, and see the gap (20 minutes)

1. Follow README.md, "Setup", steps 1 to 6.
2. Run `python -m pytest`. It reports that no tests ran. Tests come before code here.
3. Serve the page on its own:

       python -m http.server 8000 --directory frontend

   Open http://localhost:8000. The page loads and says the server answered 404 for
   `/api/rooms`: the page is finished, and the API is missing. Press Ctrl+C.
4. Run the old system's converter on its sample export:

       python -m legacy.old_format legacy/old_bookings.csv

   Some of its output is wrong. Leave it alone until Part 10.
5. Start your agent in the folder that holds HANDOUT.md (`claude` or `agy`), never in
   your home folder: it can read and edit everything under the folder you start it in.
   Ask it which instruction files it loaded. It should name `AGENTS.md` (Claude Code
   loads `CLAUDE.md`, which imports `AGENTS.md`). In Claude Code, accept the workspace
   trust prompt: the allow rules in `.claude/settings.json` apply only after you do.

Done when: `python tools/check.py setup` passes, and the agent names `AGENTS.md`.

### Part 1. Standing instructions and permission rules (20 minutes)

`AGENTS.md` is sent to the agent at the start of every session. Its rules shape what the
agent tries, but they are requests: the model can ignore them. Permission rules are
different: the tool itself refuses a denied action. You need both.

1. Read `AGENTS.md`. Under "Backend rules", write the backend rules in your own words.
   Cover at least these, then add at least one rule of your own:
   - `app/routes.py` handles HTTP only; `app/service.py` enforces every rule in
     section 5 of the spec; `app/repository.py` is the only file with SQL;
     `app/models.py` holds the request shapes.
   - `app/main.py` defines `create_app(db_path)` exactly as section 3 of the spec says.
   - Every error response uses the one error body in R9.
   - Use `sqlite3` from the standard library: no ORM, no new packages.
   - Open a new database connection for each request or repository call, never one
     shared connection: FastAPI runs requests on several threads.
   - After every task, run `python tools/check_layers.py` and `python -m pytest`.

   Keep the section short, under 30 lines. Everything in this file is sent with every
   request.
2. Read the permission rules you start with. They allow the test and layer-check
   commands without a prompt, and deny edits in `frontend/`, `git push` and `rm -rf`.
   - **Claude Code:** they are in `.claude/settings.json`, and `CLAUDE.md` imports
     `AGENTS.md` with the line `@AGENTS.md`.
   - **Antigravity CLI:** permission rules live in your own
     `~/.gemini/antigravity-cli/settings.json`, not in the repository. Merge the
     `permissions` block from `agent/agy-permissions.json` into that file, keeping
     anything already there. Keep `agent/agy-permissions.json` as an exact copy of your
     rules, because the grader reads that copy. These rules apply to every project you
     open with agy; remove them when you finish the assignment if you want.
3. Restart the agent and run `/permissions`. Check that the rules are listed.
4. Commit: `Backend rules`.

Done when: `/permissions` lists the rules, and `AGENTS.md` has your Backend rules.

### Part 2. Three agents of your own (30 minutes)

A subagent is a helper the main agent hands a job to. It starts with a fresh context,
its own instructions, and only the tools its file lists, and it returns a report to the
main agent. You define each one in a file. Write the instructions yourself.

**test-writer** writes acceptance tests in `tests/acceptance/` from `docs/spec.md`.
Tools: read, search, edit and create files, and run commands. Its instructions must say:
- expected values come from the spec, never from running the code;
- every test's name starts with `test_r<N>_`, where N is the rule it checks, for example
  `test_r7_touching_bookings_allowed`;
- tests use the `client` and `new_client` fixtures in `tests/conftest.py`, and never
  import `app` at the top of a test file;
- for every error case, check the status code, the `error` code, and that the failed
  request saved nothing; never check the `message` text;
- it only creates and edits files in `tests/acceptance/`;
- what to return (the tests, listed by rule) and when to stop.

**reviewer** reviews the code in `app/` against `docs/spec.md` and the Backend rules in
`AGENTS.md`. Read-only tools. Each finding gives the file, the line, the rule ID (R1 to
R11, or a layer rule L1 to L5 from `tools/check_layers.py`), the severity (`blocking` or
`minor`), and the problem. It never edits, and stops after one pass.

**contract-checker** checks that the page and the backend agree. Read-only tools. It
lists every request `frontend/app.js` makes (method, path, query and body fields), every
response field the page reads, and every error code the page handles. It compares each
item with sections 4 to 6 of `docs/spec.md` and with `app/routes.py`, and returns a
table: item, what the page does, what the spec says, what the backend does, and match or
mismatch. It never edits.

Each file needs a name that matches the file name, a description that tells the main
agent when to use it, a tools list, and instructions that say what to return and when to
stop. The examples below show the file format only, for a different job.

**Claude Code:** `.claude/agents/<name>.md`. Read-only tools are `Read`, `Grep` and
`Glob`; the test-writer also needs `Edit`, `Write` and `Bash`.

    ---
    name: docs-checker
    description: Checks that README commands match the project. Use after setup changes.
    tools: Read, Grep, Glob
    ---
    You check README.md against the project files.
    For each command in README.md, check that the file or script it uses exists.
    Return one line per command: the command, OK or MISSING, and the file you checked.
    Never edit files. Stop after one pass over README.md.

In current versions `/agents` does not create the file, so write it yourself, or ask the
main agent to write it and then review it. After creating the first file in
`.claude/agents/`, restart Claude Code. To check, type `@` and look for your three agents
in the list.

**Antigravity CLI:** `.agents/agents/<name>.md`. Read-only tools are `view_file` and
`grep_search`; the test-writer also needs `replace_file_content`, `write_to_file` and
`run_command`. Copy tool names exactly: a misspelled tool name can make a subagent hang.

    ---
    name: docs-checker
    description: Checks that README commands match the project. Use after setup changes.
    tools:
      - view_file
      - grep_search
    subagent: true
    ---
    (the same instructions as above)

To check, open the `/agents` panel and look for your three agents.

Commit: `Agent team`.

Done when: the three files are committed, and your tool lists all three agents.

### Part 3. Clarify the spec before any code (20 minutes)

A spec always leaves questions open. If nobody answers them, the agent answers them
silently while it builds. This step makes those choices visible and yours.

1. Ask the main agent:

       Read docs/spec.md and frontend/app.js. Do not write code and do not edit files.
       List every question you would have to guess the answer to in order to build this
       backend: anything unclear, missing, or in conflict between the spec and the page.
       Number them Q1, Q2, and so on, and for each one name the rule it touches.

2. Read the list. Some questions are already answered by the spec; note where. For the
   others, write a decision in section 7 of `docs/spec.md`: `D1.`, `D2.`, and so on, one
   line each. Section 7 says what a decision may not do: it may not reject a request the
   spec accepts, accept one the spec rejects, or change a route, field, status code or
   error code. Write at least three decisions.
3. If a question is about behavior the page expects but the spec does not define, do not
   decide it and do not build it. Write it under "Proposed, not built" with one line
   saying why.
4. Save the prompt in `prompts/`, commit (`Spec clarified`), and write the ledger entry.

Done when: section 7 has at least three decisions, and none changes sections 1 to 6.

### Part 4. Acceptance tests first, then lock them (40 minutes)

The tests are written from the spec before any backend code exists, so the code cannot
shape them. Then they are locked, so the agent cannot pass by changing the exam.

1. Ask the main agent:

       Use the test-writer subagent to write acceptance tests for rules R1 to R10 of
       docs/spec.md, in tests/acceptance/. There is no backend yet, so do not run the
       code to find expected values. Report the tests by rule.

2. Read every test before you run it. Look for weak tests, and have the test-writer fix
   them (or fix them yourself):
   - a test that checks the status code but not the `error` code;
   - an error test that does not check that nothing was saved;
   - a missing boundary: exactly 3 hours, 08:00 and 22:00, touching bookings, 40 and 41
     characters, a date that does not exist such as `2031-02-30`;
   - a test that checks the `message` text, which the spec does not fix.

   Read carefully: once locked, a wrong test cannot be fixed.
3. Run `python tools/check.py tests`. You need at least one test for each of R1 to R10,
   and at least 20 tests. Every test should fail or error, most with
   `No module named 'app.main'`. A test that passes now tests nothing: fix it or delete
   it.
4. Lock the tests with a deny rule:
   - **Claude Code:** add `"Edit(/tests/acceptance/**)"` to the `deny` list in
     `.claude/settings.json`.
   - **Antigravity CLI:** add `"write_file(tests/acceptance/)"` to the `deny` list in
     your `~/.gemini/antigravity-cli/settings.json`, and in `agent/agy-permissions.json`.

   Restart the agent and check the rule with `/permissions`.
5. Commit (`Acceptance tests locked`), then tag that commit:

       git tag a5-tests-locked

6. Prove the lock works. Ask the agent: "This is a test of a permission rule. Change the
   expected status code in one test in tests/acceptance/ to 418." The tool, not just the
   model, must block the edit. If the model refuses on its own, tell it that this is a
   deliberate test and to attempt the edit anyway. Save your prompt, the tool's refusal
   message, and the rule that blocked it in `evidence/permission-denied.md`, and commit.
   If the edit goes through, your rule is wrong: undo the edit with
   `git restore tests/acceptance`, fix the rule, and try again.

From now on, no file that existed in `tests/acceptance/` at the lock may change. The
grader compares them with the tagged commit.

Done when: the tag exists, every test fails at the tag, and
`evidence/permission-denied.md` shows the tool blocking the edit.

### Part 5. Plan before edits (15 minutes)

1. Switch to plan mode: press Shift+Tab until the status line shows plan mode (both
   tools). The agent can read and plan, but it cannot edit.
2. Ask:

       Plan the backend for docs/spec.md, rules R1 to R10, in three tasks: Task 1,
       app/repository.py; Task 2, app/models.py and app/service.py; Task 3,
       app/routes.py and app/main.py. For each task, list the files it creates and what
       "done" means, including which acceptance tests should pass after it. End with a
       section called "Not in this change". The tests in tests/acceptance/ must pass
       without being edited, and nothing in frontend/ changes.

3. Review the plan. Reject anything outside the spec: an ORM, a new package, a login, a
   change to `frontend/`, or any endpoint, field, error code or rule not in sections 4
   to 6, including anything the page handles that the spec does not define. Make sure
   "Not in this change" says so.
4. Leave plan mode and save the plan as `docs/plan.md` with the headings `## Task 1`,
   `## Task 2`, `## Task 3` and `## Not in this change`. You can ask the agent to write
   the file. Commit: `Plan`.

Done when: `docs/plan.md` has the three tasks and "Not in this change".

### Part 6. Build in three bounded tasks (60 minutes)

Do Tasks 1, 2 and 3 one at a time. For each task:

1. Check that `git status` is clean.
2. Ask:

       Do Task <n> of docs/plan.md and nothing else. Follow AGENTS.md. When you finish,
       run python tools/check_layers.py and python -m pytest tests/acceptance, and
       report the results. Do not edit any test.

3. Read the changes (`git diff`) before you accept them. Run the two checks yourself.
4. Commit (`Task <n>: ...`) and write the ledger entry.

After Task 3, every acceptance test passes and the layer check passes. If a test fails,
decide which side is wrong. If the code is wrong, ask the agent to fix the code. If a
locked test is wrong (it checks something the spec does not say), do not edit it: leave
it failing, and explain it in REPORT.md, question 2. Never bend the code away from the
spec to satisfy a wrong test.

Then see the whole app work:

    uvicorn app.main:create_app --factory --port 8000

Open http://localhost:8000. Book a room. Try to book the same room for an overlapping
time, and check that the page shows the overlap message. Cancel a booking. Take a
screenshot that shows at least one booking, and save it as `evidence/page.png`. Press
Ctrl+C, and commit.

Done when: all acceptance tests and the layer check pass, there are three task commits,
and `evidence/page.png` is committed.

### Part 7. Two read-only reviews, side by side (25 minutes)

1. Ask:

       Run the reviewer subagent on the files in app/ and the contract-checker subagent,
       at the same time. Then save each report, exactly as it was returned, in
       evidence/review.md and evidence/contract-check.md. Do not fix anything yet.

   Read-only agents cannot write files, so the main agent saves their reports. If your
   tool runs them one after the other instead, that is fine.
2. In REPORT.md, question 4, answer every finding in both reports: fixed (with the
   commit SHA) or rejected (with a one-line reason). Some findings will be wrong, and
   rejecting a wrong finding with a reason is the right call. A finding about something
   the spec does not define yet is rejected for now, with the reason "not in the spec":
   never build ahead of the spec.
3. Fix the findings you accepted one at a time ("Fix finding 3 from evidence/review.md
   and nothing else"), run the tests and the layer check, and commit each fix.

Done when: both reports are committed, and every finding has an answer in REPORT.md.

### Part 8. A spec change: the daily limit (30 minutes)

The product owner has decided one more rule. A change goes in this order, as three
commits: the spec, then a failing test, then the code.

1. **The spec.** In `docs/spec.md`:
   - add this rule at the end of section 5:

         **R11. Daily limit.** One person may hold at most two bookings on the same date,
         across all rooms. Two bookings belong to the same person when their `booked_by`
         values are equal after removing leading and trailing whitespace and ignoring
         upper and lower case. A third booking for that person on that date is rejected
         with `409 daily_limit`. Cancelling a booking frees its place.

   - add the row `| 409 | daily_limit | R11 |` to the table in section 6;
   - change the order of checks in R9 to: R3, R4, R5, R6, R7, R11;
   - in the line at the top, change "R1 to R10" to "R1 to R11", and add
     `- Version 2: R11 added.` to the change log in section 8.

   Commit: `Spec: R11 daily limit`.
2. **The test.** Create `tests/acceptance/test_r11_daily_limit.py`. The agent cannot
   write in `tests/acceptance/` any more, so you put this file there yourself: the lock
   binds the agent, not you. An AI tool may draft the tests in the chat; you check every
   expected value against R11. Write at least three tests named `test_r11_...`: a third
   booking on one date is rejected with `409 daily_limit` and is not saved; the same
   name with different case and spaces counts as the same person; cancelling one of two
   bookings allows a new one. Run it: it fails for the right reason (it expected 409 and
   got 201). Commit: `Test: R11`.
3. **The code.** Ask:

       docs/spec.md now has rule R11 (daily limit), and
       tests/acceptance/test_r11_daily_limit.py tests it. Implement R11 and nothing
       else, following AGENTS.md. Run python tools/check_layers.py and
       python -m pytest, and report the results.

   Check that every test passes, then commit: `R11: daily limit`.
4. Restart the server, and on the page book three times with one name on one day. The
   page shows the daily-limit message it already knew.

Done when: all tests pass, and the three commits are in the order spec, test, code.

### Part 9. Record a decision (15 minutes)

Two people click Book for the same room and time at the same moment. Each request runs
on its own thread: both check for an overlap, both find none, and both insert. R7 is
broken, and no test in this assignment would show it.

1. Ask:

       Look at how app/service.py and app/repository.py check for an overlap and then
       insert a booking. Can two requests that arrive at the same moment both pass the
       check? List the ways to prevent it with SQLite, with one advantage and one cost
       each. Do not edit files.

2. Copy `docs/adr/0000-template.md` to `docs/adr/0001-<short-title>.md` and write the
   ADR: Status, Context, Options considered (at least two), Decision, Consequences. The
   decision is yours. If it needs a code change, have the agent make it as its own task,
   with the tests and the layer check passing, and commit it separately.
3. Commit: `ADR 0001`.

Done when: the ADR is committed with every section filled in.

### Part 10. Legacy code: pin it, then change it (35 minutes)

`legacy/old_format.py` converts rows from the old booking system. It has no tests, and
some of its output is wrong. Before anyone changes it, you pin what it does today with
**characterization tests**: their expected values come from running the current code,
right or wrong. That is the opposite of acceptance tests, whose values come from the
spec.

1. Read `legacy/old_format.py` and run it on the sample again (Part 0, step 4).
2. Write `tests/legacy/test_old_format.py`, with at least eight tests of `to_24h` and
   `parse_old_row`, each named `test_legacy_...`. Pin everything you can find: the normal
   cases, every odd output, and every exception it raises (use `pytest.raises` with the
   exact exception class). Put the comment `# BUG: pinned, not fixed` above each test
   that pins a wrong result. The main agent may help, but not the test-writer: its rules
   say never to take expected values from running code, which is exactly what
   characterization tests do. Check every expected value by running the current code
   yourself.
3. Run `python -m pytest tests/legacy`: all pass. Commit:
   `Characterization tests for old_format`.
4. Ask:

       Refactor legacy/old_format.py for readability without changing what it does: add
       type hints to every function, give each function a docstring, remove the
       repeated split calls, and give the magic values names. Keep the function names
       to_24h and parse_old_row, and the same result or exception for every input,
       including the odd ones. Do not edit any test. Run python -m pytest tests/legacy
       and report the result.

5. If a characterization test fails, the agent changed behavior, often by "fixing" a
   bug. Undo with `git restore legacy`, tell it which behavior it changed, and try
   again. Note what happened for REPORT.md, question 7.
6. When every characterization test passes, unchanged, commit: `Refactor old_format`.

Done when: the characterization tests were committed before the refactor, still pass
unchanged, and every function in `legacy/old_format.py` has type hints.

### Part 11. Report, ledger, and submit (20 minutes)

1. Fill in REPORT.md and finish LEDGER.md.
2. Run `python tools/check.py` and fix what it reports.
3. Commit everything, tag the final commit, and push the commits and both tags:

       git tag a5-submit
       git push origin main
       git push origin --tags

4. On GitHub, check that your files and both tags are there.
5. Submit your repository's URL on Canvas.

## What to submit

Your GitHub repository, with the commit tagged `a5-submit` containing:

- `AGENTS.md` with your Backend rules, and `CLAUDE.md` if you use Claude Code;
- your permission file (`.claude/settings.json` or `agent/agy-permissions.json`) with
  the lock;
- your three agent files;
- `docs/spec.md` with your decisions and R11, `docs/plan.md`, and `docs/adr/0001-....md`;
- `app/`, `tests/acceptance/`, `tests/legacy/`, and the refactored `legacy/old_format.py`;
- `evidence/permission-denied.md`, `evidence/page.png`, `evidence/review.md` and
  `evidence/contract-check.md`;
- `REPORT.md`, `LEDGER.md` and `prompts/`;
- the tags `a5-tests-locked` and `a5-submit`.

If the `a5-submit` tag is missing, the grader uses the latest commit on `main` pushed
before the deadline.

## How it is graded

100 points, item by item, as listed in RUBRIC.md:

- **40 points:** your backend, checked by hidden tests of R1 to R11. They test the same
  rules as your acceptance tests, with their own cases.
- **15 points:** your instructions, permission rules and three agents.
- **22 points:** tests first: the lock, locked files unchanged, your tests passing on
  your backend and on a correct reference backend, your tests catching seeded bugs in
  the reference backend, the plan and task commits, and the layer check.
- **15 points:** the reviews, the spec change order, your decisions and ADR, and the
  legacy work. The grader runs your characterization tests against copies of the
  original file in which one behavior was changed; good characterization tests fail on
  each copy.
- **8 points:** your report and provenance ledger.

About 80 points are checked by script; `python tools/check.py` runs the same checks
except the hidden tests and seeded bugs. The rest is read by the instructor.

# Assignment 5 report

Name:
Agent tool and version (Claude Code or Antigravity CLI):

Answer each question in two to five sentences, below the question, unless it asks for a
table. Point to commits, files, tests or rule IDs where you can.

## 1. Clarify (Part 3)

How many questions did the agent list? Which one, if guessed wrong, would have changed
the backend's behavior the most, and what did you decide?

## 2. Tests before the lock (Part 4)

Name one weak test you found before the lock and how you fixed it. Did any locked test
turn out to be wrong later? If so, which test, which rule, and why.

## 3. The plan (Part 5)

What did you reject from the plan, or add to "Not in this change", and why?

## 4. Review findings (Part 7)

One row for every finding in `evidence/review.md` and `evidence/contract-check.md`.

| # | Agent | Finding, in a few words | Fixed (commit SHA) or rejected (reason) |
|---|---|---|---|
| 1 | | | |

## 5. The spec change (Part 8)

Did the contract checker, or any earlier step, notice that the page already handles an
error code the spec did not define? Why does a change go spec, then test, then code, in
three commits?

## 6. Where the lock stops (Part 4)

Name one way an agent could still change a locked test despite your deny rule, and what
in this assignment would catch it.

## 7. Legacy parser (Part 10)

Which odd behaviors did you pin? Did the agent's first refactor change any behavior, and
how did you find out? Before fixing one of these bugs for real, what would you check?

## 8. The agent team

What did giving each agent one job and its own tools buy you? Name one thing that went
wrong with an agent and how you caught it.

## Screenshot

`evidence/page.png` shows the page with at least one booking made through your backend.

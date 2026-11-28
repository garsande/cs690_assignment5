# Part 4 - Acceptance Test Audit


## 1. Session information

- Date: 2026-11-27
- Tool: Claude Code
- Tool version: 2.1.332
- Model: Opus 5.5
- Agent: Main agent and test-writer subagent
- Prompt: prompts/04-acceptance-tests.txt, prompts/04-acceptance-test-corrections.txt, prompts/04-acceptance-test-review.txt
- Subagent task: Write acceptance tests R1-R10
- Reported subagent execution time: 3 minutes 41 seconds
- Acceptance test cases generated: 245
- Specification rules covered: R1-R10
- Test files generated: 10
- Shared helper modules generated: 1
- Reported pytest results:
  - Passed: 0
  - Failed: 9
  - Errors: 236
- Reported failure cause:
  ModuleNotFoundError: No module named 'app.main'
- Backend implementation: Not started
- Acceptance tests locked: No

## 2. AI assistance and provenance

Claude Code generated and corrected the acceptance tests using the test-writer subagent. ChatGPT (GPT-6.2) provided review recommendations, identified findings F1-F8, assisted with correction prompts and prepared audit documentation. The project owner executed the local verification commands and retains responsibility for final approval and repository changes.

Related ledger entries: Entry 2 (Claude Code) and Entry 2A (ChatGPT).

Prompt references (ChatGPT files are reconstructed summaries, not verbatim transcripts):

- `prompts/04-acceptance-tests.txt`

## 3. Original Claude response

```text
test-writer(Write acceptance tests R1-R10)
Backgrounded agent (↓ to manage · ctrl+o to expand)

The test-writer subagent is now writing acceptance tests for R1–R10 in tests/acceptance/. I've told it to:

- take every expected value from docs/spec.md only, without running any code to find out what the answers should be
- leave out any case where the spec is unclear and list it, rather than guess
- stay out of frontend/ and app/
- name each test so it's clear which rule it covers

I'll report the tests by rule once it finishes, along with any gaps it found in the spec.

Waiting for 1 background agent to finish

Message from @test-writer (ctrl+o to expand)

  Ran 1 shell command

Agent "Write acceptance tests R1-R10" finished · 3m 41s

  Ran 1 shell command

I used the test-writer subagent to write 245 acceptance tests for R1–R10 in tests/acceptance/. They all load in pytest without errors. Every expected value comes from docs/spec.md, and nothing was run to find them. All 245 fail for now, because there is no backend yet.

Checks (per AGENTS.md):
- tools/check_layers.py: fails, because the five app/ files it checks for don't exist yet.
- python -m pytest: 236 errors and 9 failures. Every one is ModuleNotFoundError: No module named 'app.main'. The 9 "failures" are the R10 tests that start the app inside the test body rather than in a fixture, so pytest counts them differently.
- Python: python doesn't exist on this machine and the system python3 has no FastAPI, so I ran everything with .venv/bin/python.

What every error test checks: the status code, the error code, and that the body has exactly error and message. It never checks the message text. Failed requests also check that the stored bookings didn't change.

Tests by rule (a few tests run several input variants):

Rule: R1
File: test_r01_rooms.py
Tests: 3
What's covered: Exactly the four rooms in id order, only id/name/capacity, list unchanged after a booking
────────────────────────────────────────
Rule: R2
File: test_r02_list_bookings.py
Tests: 38
What's covered: Filtering by date and by room_id; ordered by room then start; exactly six fields per booking;
  missing, badly formatted or impossible dates give 422 invalid_request; leap day accepted; non-integer room_id
  gives 422; unknown room (including 2**70) gives 404 room_not_found; a bad date is reported before a bad room (D4)
────────────────────────────────────────
Rule: R3
File: test_r03_request_shape.py
Tests: 85
What's covered: Valid request returns 201 with six fields and shows up in the list; extra fields ignored; past dates
  allowed (P1); invalid, empty, null or non-object bodies, missing fields, wrong types (D1) and bad date/time
  formats (24:00, 09:60, 9:00 and others) all give 422 invalid_request
────────────────────────────────────────
Rule: R4
File: test_r04_name.py
Tests: 14
What's covered: Name trimmed, with inner spaces and case kept (D3); 1 and 40 characters accepted, also after
  trimming and for Unicode, counted as code points; 41, empty or whitespace-only gives 422 invalid_name
────────────────────────────────────────
Rule: R5
File: test_r05_times.py
Tests: 26
What's covered: 08:00 start, 22:00 end, 30-minute and exactly 3-hour bookings accepted; minutes other than :00/:30,
  outside opening hours, start ≥ end, or longer than 3 hours give 422 invalid_time
────────────────────────────────────────
Rule: R6
File: test_r06_room.py
Tests: 10
What's covered: Rooms 1–4 can be booked; 0, 5, -1, 100 and ±2**70 give 404 room_not_found (D2)
────────────────────────────────────────
Rule: R7
File: test_r07_overlap.py
Tests: 17
What's covered: 8 overlap shapes give 409 overlap; bookings that only touch are allowed, including back-to-back by
  one person (P4); other room or date doesn't conflict; name doesn't matter; 8 identical requests at once create
  exactly one booking (D6)
────────────────────────────────────────
Rule: R8
File: test_r08_cancel.py
Tests: 16
What's covered: 204 with an empty body; anyone can cancel (P3); freed time can be rebooked; deleting twice, unknown,
  0, negative or 2**70 ids give 404 booking_not_found; non-integer id gives 422; ids are never reused and an old
  cancel can't remove a newer booking (D5)
────────────────────────────────────────
Rule: R9
File: test_r09_errors.py
Tests: 24
What's covered: Error body has only error and message on every endpoint; a series of failed requests changes
  nothing; when several rules fail, the error reported follows R3 → R4 → R5 → R6/R7
────────────────────────────────────────
Rule: R10
File: test_r10_application.py
Tests: 12
What's covered: Serves index.html, app.js and styles.css byte-for-byte, whatever the working directory (D7); a fresh
  database has four rooms and no bookings; separate db files are isolated; bookings, cancellations, the overlap rule
  and id numbering survive a restart without duplicating rooms

A shared helper module, tests/acceptance/_rb_helpers.py, holds the common request body, booking setup and error checks.

Points in the spec that need your decision:
1. Impossible dates in POST. R3 says date "follows the format in R2", and R2 requires a real calendar day. The tests read that as 2031-02-30 in a POST giving 422 invalid_request. Two tests depend on that reading: test_r3_non_calendar_date_is_invalid_request and test_r9_r3_before_r4_bad_date_and_long_name.
2. Left out because the spec doesn't settle them:
   - room_id= (empty), 01, +1, " 1", and digits other than 0–9 in dates or times
   - a client-sent id field, a non-JSON content type, response content types and field order
   - unsupported routes, which D8 leaves to FastAPI
   - the daily booking limit, which section 7 lists as proposed, not built
3. Concurrency test. The R7 test that sends 8 identical requests at once relies on the test client handling parallel requests. If it's ever flaky, check the test setup before blaming the backend.

There are also two new files not in git, evidence/04-acceptance-test-audit.md and prompts/04-acceptance-tests.txt. They look like your own notes, so I didn't touch them. Nothing has been committed.
```

## 4. Generated test files and coverage

- `tests/acceptance/_rb_helpers.py`
- `tests/acceptance/test_r01_rooms.py`
- `tests/acceptance/test_r02_list_bookings.py`
- `tests/acceptance/test_r03_request_shape.py`
- `tests/acceptance/test_r04_name.py`
- `tests/acceptance/test_r05_times.py`
- `tests/acceptance/test_r06_room.py`
- `tests/acceptance/test_r07_overlap.py`
- `tests/acceptance/test_r08_cancel.py`
- `tests/acceptance/test_r09_errors.py`
- `tests/acceptance/test_r10_application.py`

| Rule | Initial cases | Revised cases | Coverage |
|---|---:|---:|---|
| R1 | 3 | 3 | Room list and exact fields |
| R2 | 38 | 38 | Date and room filters, sorting, validation |
| R3 | 85 | 86 | Request shape, strict types, ignored extra fields |
| R4 | 14 | 16 | Trimming and Unicode length boundaries |
| R5 | 26 | 26 | Opening hours, duration and time increments |
| R6 | 10 | 10 | Room existence and integer range |
| R7 | 17 | 17 | Overlap, touching bookings and concurrency |
| R8 | 16 | 16 | Cancellation, absent IDs and non-reuse |
| R9 | 24 | 26 | Error contract, precedence and unchanged state |
| R10 | 12 | 12 | Static files, isolation and persistence |
| **Total** | **245** | **250** | R1-R10 |

## 5. AI-assisted review findings

The initial acceptance test suite contained 245 collected
test cases across ten test files, with one shared helper
module.

All mandatory boundary conditions were present, and the
suite covered rules R1-R10 and decisions D1-D7.
D8 was intentionally not tested because it delegates
undefined routes to FastAPI.

The following issues were identified during review:

| Finding | Rule | Issue | Requested action |
|---|---|---|---|
| F1 | R9 | Some error tests omit unchanged-state checks | Strengthen error tests |
| F2 | R9 | Failed-request series ignores response codes | Assert every response |
| F3 | R8 | Tests assume booking IDs cannot be zero or negative | Remove unsupported assumption |
| F4 | R7, D6 | Concurrency test has weak exception handling and incomplete error assertions | Strengthen concurrency test |
| F5 | R4, D3 | Unicode tests do not distinguish code points from UTF-16 units | Add supplementary Unicode boundaries |
| F6 | R3 | Client-supplied booking ID is not tested | Verify extra id field is ignored |
| F7 | R9, R10 | Restart overlap test omits complete error and state assertions | Strengthen restart test |
| F8 | R9 | Some test names overstate rule violations | Correct test names and comments |

The interpretation of impossible POST calendar dates
as 422 invalid_request was accepted under R2 and R3.

The daily booking limit remains excluded because it is
not part of Version 1.

A follow-up correction prompt was prepared in:
prompts/04-acceptance-test-corrections.txt

The acceptance tests remain unlocked until the corrections
have been reviewed and the required test checker has
been executed.

## 6. Correction session - F1-F8

### Session information

- Date: 2026-11-27
- Tool: Claude Code
- Tool version: 2.1.332
- Model: Opus 5.5
- Agent: Main agent and test-writer subagent
- Prompt: prompts/04-acceptance-test-corrections.txt
- Reported subagent execution time: 3 minutes 26 seconds
- Reported total correction time: 4 minutes 12 seconds
- Original acceptance test cases: 245
- Revised acceptance test cases: 250
- Findings addressed: F1-F8

### Original Claude correction response

```text
The test-writer subagent is now working through F1–F8 on the existing tests in tests/acceptance/. It's the same one that wrote them, so it already knows the test files. I've passed on your constraints: change only the acceptance tests, take expected values from the spec only, and treat impossible POST dates as 422 invalid_request. I've also told it not to run pytest (not even to check that the tests load) or the layer checker.

When it finishes, I'll report each finding separately with the files and tests changed, the reason for each change, and the new test counts by rule. Then I'll stop, without running any checks, so you can review the changes first.

Crunched for 21s · done 8:22 PM

Message from @test-writer (ctrl+o to expand)

  Ran 1 shell command

Agent "Write acceptance tests R1-R10" finished · 3m 26s

The test-writer subagent made all eight corrections (F1–F8) in tests/acceptance/, but nothing has been run. As you asked, it didn't run pytest (not even to check that the tests load) or the layer checker. It counted tests by parsing the files with Python's ast module, so all 10 files are at least valid Python. Git shows nothing changed outside tests/acceptance/ apart from your own evidence/ and prompts/ files.

One design choice to review first. Most of F1 and F2 runs through new shared error helpers in tests/acceptance/_rb_helpers.py. Each helper takes a snapshot of the stored bookings, sends the request, checks the status, the error code and that the body has only error and message, then confirms the snapshot hasn't changed. The snapshot covers both standard test dates plus the request's own date when it is a real calendar date. If those dates hold no bookings, the helper first creates one reference booking (room 4, 20:00–21:00, on the second test date) so that a removed or changed booking would be noticed. The alternative is for each test to create its own booking.

F1 – State check on every error test

- R2 (test_r02_list_bookings.py): all 9 GET error tests now create a booking and use assert_get_error. Some never compared state; the others compared an empty database, where a removed booking can't be detected.
- R3: the invalid-JSON, empty-body and null-body tests now use assert_raw_post_error, for the same empty-database reason. The other POST error tests in R3–R7 needed no edits, because the shared POST helper now does the seeding and date snapshots.
- R8: five DELETE error tests now use assert_delete_error. The empty-database test checks that both dates are still empty.
- R9: every error-body test now creates a booking and compares state. The combined DELETE test was split in two, one for a non-integer id and one for an unknown id, so each request gets its own state check.

F2 – Failed request series

test_r9_series_of_failed_requests_changes_nothing now starts with three bookings over two dates. It sends nine failing requests and, after each one, checks the exact status, error code, body shape and unchanged snapshot:

┌──────────────────────────────────┬───────────────────────┐
│             Request              │       Expected        │
├──────────────────────────────────┼───────────────────────┤
│ POST with a missing field        │ 422 invalid_request   │
├──────────────────────────────────┼───────────────────────┤
│ POST with a whitespace-only name │ 422 invalid_name      │
├──────────────────────────────────┼───────────────────────┤
│ POST starting at 07:00           │ 422 invalid_time      │
├──────────────────────────────────┼───────────────────────┤
│ POST for room 7                  │ 404 room_not_found    │
├──────────────────────────────────┼───────────────────────┤
│ POST that overlaps               │ 409 overlap           │
├──────────────────────────────────┼───────────────────────┤
│ DELETE abc                       │ 422 invalid_request   │
├──────────────────────────────────┼───────────────────────┤
│ DELETE an id no booking has      │ 404 booking_not_found │
├──────────────────────────────────┼───────────────────────┤
│ GET for 2031-02-30               │ 422 invalid_request   │
├──────────────────────────────────┼───────────────────────┤
│ GET for room 6                   │ 404 room_not_found    │
└──────────────────────────────────┴───────────────────────┘

The old version checked no status or code, and its "unknown" id could in theory have matched a real booking.

F3 – Booking ids

All in test_r08_cancel.py:
- Replaced: the old zero/negative test, which hard-coded 0 and -1, is now test_r8_absent_non_positive_id_is_booking_not_found. It picks a zero or negative id that no current booking has.
- Added: test_r8_absent_id_below_existing_ids_is_booking_not_found, using the smallest current id minus 1.
- Changed:
  - the unknown-id test now uses the largest current id plus 1, instead of id + 1000;
  - the 2**70 test first asserts that no booking has that id;
  - the delete-twice test first confirms the id is really gone.
- Kept: the empty-database test with id 1, since no booking exists there at all.

F4 – Concurrency (D6)

test_r7_concurrent_identical_requests_create_one_booking was rewritten:
- No waiting forever: every wait has a 30-second limit, any error inside a worker is raised again in the test, and cleanup always runs.
- Responses: exactly one 201 and seven 409 overlap, each 409 with the full R9 body. It doesn't assume which request wins.
- Stored state: exactly one booking, and it matches the 201 response.

F5 – Unicode boundaries (D3)

Two new R4 tests use emoji, which count as 1 character each but as 2 under UTF-16 counting:
- 40 emoji: accepted, and the name is returned and stored unchanged.
- 41 emoji: 422 invalid_name, with no change to stored bookings.

F6 – Client-supplied id

New test test_r3_client_supplied_id_is_ignored creates a booking, then posts a second valid booking (different room and time) whose extra id field is the first booking's id. It checks for 201 with a different id from the backend, the values that were sent, and a listing of exactly the two bookings, so the first is unchanged. It assumes nothing about how ids are numbered.

F7 – Overlap after restart

test_r10_restart_still_enforces_overlap now:
- checks the restarted app lists only the original booking;
- sends the overlapping request through the shared helper, so the 409 needs the full R9 body and state must not change;
- confirms afterwards that the original booking is the only one stored.

F8 – R9 test names

Every rule-order test now has a comment saying which input breaks which rule:

┌─────────────────────────────────────────────┬───────────────────────────────────────────────────────┬────────────────────────────────────────────────┐
│                  Old name                   │                       New name                        │                      Why                       │
├─────────────────────────────────────────────┼───────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
│ test_r9_r3_before_r6_wrong_type_room        │ test_r9_r3_before_r6_bad_time_format_and_unknown_room │ Room "99" as a string broke only R3; now room  │
│                                             │                                                       │ 99 with end 10:3                               │
├─────────────────────────────────────────────┼───────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
│                                             │                                                       │ A malformed time can't really overlap; now     │
│ test_r9_r3_before_r7_bad_format_and_overlap │ test_r9_r3_before_r7_wrong_name_type_and_overlap      │ booked_by=123 with times identical to an       │
│                                             │                                                       │ existing booking                               │
├─────────────────────────────────────────────┼───────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
│ test_r9_r3_before_all_other_rules           │ test_r9_r3_before_r4_r5_r6                            │ R6 and R7 can never both fail, and room 1.5    │
│                                             │                                                       │ didn't really break R6                         │
├─────────────────────────────────────────────┼───────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
│ test_r9_r4_before_r5_r6_r7_together         │ test_r9_r4_before_r5_and_r6                           │ Room 8 can't overlap anything                  │
├─────────────────────────────────────────────┼───────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
│ (new)                                       │ test_r9_r4_before_r5_and_r7                           │ Empty name plus 09:00–10:15 over an existing   │
│                                             │                                                       │ 09:00–10:00, expects invalid_name              │
└─────────────────────────────────────────────┴───────────────────────────────────────────────────────┴────────────────────────────────────────────────┘

The comment on the R6-only test now says only R6 is broken, because R6 and R7 can't fail together.

Test counts by rule

Counted from the files, not by running pytest:

┌───────┬────────────────┬───────────────────────┐
│ Rule  │ Test functions │ Cases (with variants) │
├───────┼────────────────┼───────────────────────┤
│ R1    │ 3              │ 3                     │
├───────┼────────────────┼───────────────────────┤
│ R2    │ 16             │ 38                    │
├───────┼────────────────┼───────────────────────┤
│ R3    │ 19             │ 86 (was 85)           │
├───────┼────────────────┼───────────────────────┤
│ R4    │ 13             │ 16 (was 14)           │
├───────┼────────────────┼───────────────────────┤
│ R5    │ 15             │ 26                    │
├───────┼────────────────┼───────────────────────┤
│ R6    │ 4              │ 10                    │
├───────┼────────────────┼───────────────────────┤
│ R7    │ 10             │ 17                    │
├───────┼────────────────┼───────────────────────┤
│ R8    │ 13             │ 16                    │
├───────┼────────────────┼───────────────────────┤
│ R9    │ 26             │ 26 (was 24)           │
├───────┼────────────────┼───────────────────────┤
│ R10   │ 12             │ 12                    │
├───────┼────────────────┼───────────────────────┤
│ Total │                │ 250 (was 245)         │
└───────┴────────────────┴───────────────────────┘

All earlier boundary cases are kept. The daily booking limit isn't tested, no open spec questions were given an assumed answer, and impossible calendar dates in POST still give 422 invalid_request, as you accepted.

Because tests/acceptance/ has never been committed, git diff won't show what changed. You'll need to read the files directly. When you've reviewed them, say so and I'll run python tools/check_layers.py and python -m pytest.

Baked for 4m 12s · done 8:25 PM

recap: We're writing acceptance tests for RoomBook rules R1 to R10 before any backend exists. The F1 to F8 fixes are written, bringing it to 250 tests, but nothing has been run. Next, once you've reviewed the changed tests, I'll run the layer checker and pytest. (turn off recaps in /config)
```

## 7. Revised suite review

The revised acceptance test suite was reviewed against
Version 1 of docs/spec.md, including decisions D1-D8.

The test-writer addressed the eight findings identified
during the initial review.

| Finding | Review result |
|---|---|
| F1 | Accepted: error helpers verify unchanged booking state |
| F2 | Accepted: every failed request in the series is checked |
| F3 | Accepted: unsupported booking ID assumptions removed |
| F4 | Accepted: concurrency assertions and worker handling improved |
| F5 | Accepted: supplementary Unicode boundary tests added |
| F6 | Accepted: client-supplied ID is ignored |
| F7 | Accepted: restart overlap and state assertions strengthened |
| F8 | Accepted: validation precedence tests corrected |

### Shared helper decision

The shared error-helper design was accepted because it
provides consistent status, error-code, response-shape
and unchanged-state assertions.

The automatic reference booking is created only when
the relevant dates contain no bookings.

Tests that explicitly require an empty database do not
use the automatic seeding mechanism.

### Boundary condition verification

- [x] Exactly three hours
- [x] Opening time 08:00
- [x] Closing time 22:00
- [x] Touching bookings
- [x] Name of exactly 40 characters
- [x] Name of 41 characters
- [x] Invalid calendar date 2031-02-30
- [x] Error code assertions
- [x] Unchanged-state assertions for relevant booking dates
- [x] No exact error message assertions

### Process compliance

The initial generation session ran pytest and the layer checker before the full human review. The correction session stopped after writing the changes and counting cases using AST analysis, as reported by Claude. The owner subsequently ran the required local checks.

## 8. Local pre-implementation verification

Date recorded in original audit: 2026-11-28 (confirm local session date).

### Check 1: Repository status

Command:

```bash
git status --short
```

Result:

```text
?? evidence/04-acceptance-test-audit.md
?? prompts/04-acceptance-test-corrections.txt
?? prompts/04-acceptance-tests.txt
?? tests/acceptance/
```

Only the expected Part 4 artifacts were listed.

### Check 2: Acceptance test collection

Command:

```bash
python3 -m pytest tests/acceptance --collect-only -q
```

Result:

```text
250 tests collected in 0.18s
```

### Check 3: Assignment test checker

Command:

```bash
python3 tools/check.py tests
```

Result:

```text
[ OK ] 250 acceptance tests collected (at least 20)
[ OK ] R1: 3 tests named test_r1_...
[ OK ] R2: 38 tests named test_r2_...
[ OK ] R3: 86 tests named test_r3_...
[ OK ] R4: 16 tests named test_r4_...
[ OK ] R5: 26 tests named test_r5_...
[ OK ] R6: 10 tests named test_r6_...
[ OK ] R7: 17 tests named test_r7_...
[ OK ] R8: 16 tests named test_r8_...
[ OK ] R9: 26 tests named test_r9_...
[ OK ] R10: 12 tests named test_r10_...
[ -- ] R11: 0 tests (R11 comes in Part 8)
[INFO] run now: 0 passed, 250 failed or errored

All checks passed.
```

### Check 4: Pre-implementation acceptance test execution

Command:

```bash
python3 -m pytest tests/acceptance -q --tb=no
```

Result:

```text
9 failed, 241 errors in 1.44s
```

All failures and errors resulted from:

ModuleNotFoundError: No module named 'app.main'

This is expected because the backend has not yet been
implemented.

The result establishes the initial red state of the
acceptance test suite before implementation.

### Check 5: Layer checker

Command:

```bash
python3 tools/check_layers.py
```

Result:

```text
Layer check FAILED:
  L4: app/main.py is missing
  L4: app/routes.py is missing
  L4: app/service.py is missing
  L4: app/repository.py is missing
  L4: app/models.py is missing
```

This failure is expected at this stage. No backend
files were created to satisfy the checker prematurely.

### Check 6: Whitespace verification

Command:

```bash
git diff --check
```

Result:

```text
No output.
```

The untracked files will be checked again after staging.

### Final pre-lock decision

The revised acceptance test suite satisfies the
pre-implementation checker requirements.

- 250 acceptance tests collected.
- All ten Version 1 rules covered.
- All eight review findings addressed.
- Zero acceptance tests passed before implementation.
- R11 intentionally excluded.
- Backend implementation has not started.

The suite is approved for the permanent acceptance
test permission lock, subject to final owner approval.

Permission enforcement and the Git lock tag will be
verified separately.

## 9. Remaining risks

- Worker timeouts cannot forcibly terminate a running Python thread.
- Shared error helpers depend on successful booking creation and listing.
- Booking snapshots cover relevant test dates, not every possible date.
- Passing behavior against a completed backend has not yet been demonstrated.


## 10. Permission lock and completion status

- [x] Initial generation and correction reports preserved.
- [x] F1-F8 corrections reviewed.
- [x] Local checker passed.
- [x] 250 acceptance test cases collected.
- [x] Zero acceptance tests passed before implementation.
- [x] Ledger entries recorded.
- [x] Acceptance test deny rule configured.
- [x] Acceptance test commit created.
- [x] a5-tests-locked tag created.
- [x] Commit and tag pushed to GitHub.
- [x] Actual tool-level permission denial demonstrated.

### Permission rule

The following deny rule is configured in
.claude/settings.json:

`Edit(/tests/acceptance/**)`

The redundant Write rule was removed after Claude Code
reported that it would never match.

### Lock commit

- Commit SHA: eac243b
- Tag: a5-tests-locked
- Branch: main

The remote tag and main branch were verified to point
to the same commit at the time of review.

### Permission enforcement result

The configured permission rule was successfully
demonstrated through an actual denied Edit operation.

Claude Code attempted to change an expected HTTP
status code from 201 to 418 in:

tests/acceptance/test_r03_request_shape.py

The permission system blocked the operation.

The original prompt and denial response are recorded in:

- prompts/04-permission-denial-test.txt
- evidence/permission-denied.md

Repository comparison against a5-tests-locked
confirmed that no locked acceptance test files
were modified.

Part 4 is complete.

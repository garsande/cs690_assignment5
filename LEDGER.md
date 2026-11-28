# Provenance Ledger

Write one entry per reviewable change, when the work is done, using exactly the schema
in HANDOUT.md. Put the prompts you typed into AI tools in `prompts/` and name the file in
the entry's `prompts` field. When a subagent did the work, name it in the `tool` field.

## Worked example (not graded; leave it here and add your entries under "My entries")

This shows the level of detail expected. The change is not part of this assignment, and
the commit SHA, date and numbers are made up.

```
## Entry 0
artifact:  commit 3f9c2ab, GET /api/health in app/routes.py (example only)
tool:      Claude Code 2.1.x, main agent, Claude Opus model, 2031-03-01
prompts:   asked for a health endpoint that returns {"ok": true}; prompts/00-health.txt
review:    read the diff. The agent also added a "version" field and a new package to
           read it from git; I rejected both because the request did not ask for them,
           and kept only the endpoint.
checks:    python -m pytest: 41 passed. python tools/check_layers.py: passed.
evidence:  request from the operations team, ticket OPS-12
risk:      no test checks the endpoint under load; not needed for this change.
```

## My entries



## Entry 1 - Part 3: Specification clarification

artifact:  docs/spec.md, section 7;
           evidence/03-spec-clarification.md

tool:      Claude Code, 2.1.332, Opus 5.5,
           2026-11-27, main agent

prompts:   prompts/03-clarify-spec.txt

review:    Claude identified 17 questions (Q1-Q17), including
           one conflict between the frontend and specification.

           I reviewed the questions and approved eight
           clarification decisions:

           I deferred Q1, the daily booking limit, because
           it would introduce a new rejection condition
           and error code not defined in Version 1.

           I recorded the approved decisions in section 7
           without changing the existing API contract,
           rules R1-R10 or product owner decisions P1-P4.

checks:    git status --short:
           Only the four expected Part 3 files were listed.

           git diff -- docs/spec.md:
           Confirmed D1-D8 and the deferred daily limit.
           Existing requirements remained unchanged.

           git diff -- app/ frontend/ tests/:
           No output; no tracked changes in these directories.

           python3 tools/check.py setup:
           All 11 checks passed.

           git diff --check:
           No output; no whitespace errors detected.

evidence:  docs/spec.md, section 7, decisions D1-D8;
           rules R2, R3, R4, R6, R7, R8, R9 and R10;
           evidence/03-spec-clarification.md;
           prompts/03-clarify-spec.txt.

risk:      The approved decisions have not yet been implemented
           or tested. Strict input validation and concurrent
           booking protection require careful implementation.

           Exact textual integer syntax, Unicode digit handling,
           duplicate JSON keys, duplicate query parameters,
           missing frontend file behavior and recovery from
           partially initialized databases remain unresolved.

           The daily booking limit is intentionally deferred
           until a formal specification change.


## Entry 1A - Part 3: Specification clarification review and audit

artifact:  evidence/03-spec-clarification.md
           docs/spec.md, Section 7

tool:      ChatGPT, GPT-6.2, 2026-11-27.
           Conversational review and documentation assistant.

prompts:   Reviewed the clarification questions generated
           by Claude Code, evaluated specification
           ambiguities, recommended clarification decisions,
           and assisted with preparing the specification
           clarification audit.

           prompts/03-spec-review.txt

review:    Reviewed the 17 clarification questions
           reported by Claude Code and evaluated them against
           the existing specification, frontend contract and
           assignment requirements.

           Each question was classified as accepted,
           partially accepted, deferred, already specified
           or not selected.

           Recommended eight clarification decisions.

           I approved the eight decisions before updating
           Section 7 of docs/spec.md.

           The daily booking limit was deferred until
           Part 8 because it is not a Version 1 requirement.

           Organizing the clarification
           evidence, decision rationale, verification
           checklist and remaining risks.

           The original Claude Code response was retained
           in the evidence document.

           Final specification decisions and repository
           changes remained under my control.

checks:    The setup checker reported all checks passed.

           The supplied Git diff showed the clarification
           decisions added to Section 7 without changes
           to the existing business rules or API contract.

           No changes were reported in app/, frontend/
           or tests/.

           The whitespace check produced no output.


evidence:  evidence/03-spec-clarification.md
           prompts/03-spec-review.txt
           prompts/03-clarify-spec.txt
           docs/spec.md, Section 7, decisions D1-D8
           Existing specification rules R1-R10
           Product owner decisions P1-P4
           

risk:      Some specification ambiguities remain
           intentionally unresolved because they are
           outside the selected clarification scope.

           The recommended decisions had not yet been
           validated against an implemented backend.


## Entry 2 - Part 4: Acceptance test creation and review

artifact:  tests/acceptance/test_r01_rooms.py
           tests/acceptance/test_r02_list_bookings.py
           tests/acceptance/test_r03_request_shape.py
           tests/acceptance/test_r04_name.py
           tests/acceptance/test_r05_times.py
           tests/acceptance/test_r06_room.py
           tests/acceptance/test_r07_overlap.py
           tests/acceptance/test_r08_cancel.py
           tests/acceptance/test_r09_errors.py
           tests/acceptance/test_r10_application.py
           tests/acceptance/_rb_helpers.py
           evidence/04-acceptance-test-audit.md

tool:      Claude Code 2.1.332, Opus 5.5,
           2026-11-27 to 2026-11-28,
           main agent and test-writer subagent.

prompts:   Asked the test-writer subagent to generate
           acceptance tests for rules R1-R10 using
           docs/spec.md as the source of expected
           behavior.

           prompts/04-acceptance-tests.txt

           Submitted a follow-up correction prompt
           addressing eight findings identified during
           the review of the initial acceptance tests.

           prompts/04-acceptance-test-corrections.txt

	   Tested acceptance test permission enforcement
           by requesting a change to an expected status
           code from 201 to 418.

           prompts/04-permission-denial-test.txt

review:    The initial test-writer session generated
           245 acceptance test cases covering R1-R10.

           The tests were reviewed against Version 1
           of docs/spec.md, including decisions D1-D8
           and product owner decisions P1-P4.

           Mandatory boundary conditions were checked,
           including exactly three-hour bookings,
           opening and closing times, touching bookings,
           40- and 41-character names, and impossible
           calendar dates.

           Eight findings were identified:

           F1: Incomplete unchanged-state assertions
               in some rejected-request tests.

           F2: Missing response assertions in the
               series of failed requests.

           F3: Unsupported assumptions about positive
               booking identifiers.

           F4: Weak concurrency exception handling
               and incomplete response assertions.

           F5: Insufficient Unicode coverage to
               distinguish code-point counting from
               UTF-16 code-unit counting.

           F6: Missing test for a client-supplied
               booking identifier.

           F7: Incomplete error and state assertions
               for overlap enforcement after restart.

           F8: Test names and comments that overstated
               the validation rules being violated.

           The test-writer subagent corrected all
           eight findings. The revised suite contains
           250 acceptance test cases.

           The shared error-helper design was retained
           to provide consistent status, error-code,
           response-shape and unchanged-state checks.

           Impossible POST calendar dates were accepted
           as 422 invalid_request under R2 and R3.

           The daily booking limit was intentionally
           excluded because it is not part of Version 1.

           No backend implementation was introduced
           during acceptance test creation.

checks:    git status --short:
           Only the expected Part 4 artifacts were
           listed as untracked.

           python3 -m pytest tests/acceptance
           --collect-only -q:
           250 tests collected in 0.18s.

           python3 tools/check.py tests:
           All checks passed.
           R1: 3 tests
           R2: 38 tests
           R3: 86 tests
           R4: 16 tests
           R5: 26 tests
           R6: 10 tests
           R7: 17 tests
           R8: 16 tests
           R9: 26 tests
           R10: 12 tests
           R11: 0 tests, intentionally deferred.

           python3 -m pytest tests/acceptance -q --tb=no:
           9 failed, 241 errors in 1.44s.
           Zero tests passed.

           All failures and errors were caused by
           ModuleNotFoundError for app.main, as expected
           before backend implementation.

           python3 tools/check_layers.py:
           Failed because the five required backend
           files do not exist yet. This is expected.

           git diff --check:
           No output. Staged files will be checked
           separately before committing.
	   Permission enforcement demonstration:

           The Edit operation on
           tests/acceptance/test_r03_request_shape.py
           was blocked by the configured deny rule.

           Repository comparison against
           a5-tests-locked confirmed that no locked
           acceptance test files were modified.

evidence:  docs/spec.md, rules R1-R10;
           decisions D1-D8;
           product owner decisions P1-P4;
           tests/acceptance/;
           evidence/04-acceptance-test-audit.md;
           prompts/04-acceptance-tests.txt;
           prompts/04-acceptance-test-corrections.txt.
	   evidence/permission-denied.md;
           prompts/04-permission-denial-test.txt;
           .claude/settings.json;
           commit eac243b, tag a5-tests-locked.

risk:      The acceptance tests have not yet been
           executed successfully against a completed
           backend.

           The concurrency test uses worker timeouts,
           but these cannot forcibly terminate an
           already-running Python thread.

           Shared error helpers depend on successful
           booking creation and listing through the API.

           Booking snapshots inspect relevant test dates
           rather than every possible database date.

           The initial test-generation session ran
           checks before the human review was completed.
           The correction session stopped for review
           before the required local checks were run.

           The acceptance test deny rule has been
           configured in .claude/settings.json.

           The acceptance tests were committed and
           tagged as a5-tests-locked at commit eac243b.

           Actual tool-level permission enforcement was successfully 
	   demonstrated. Claude Code's Edit operation was blocked by the configured deny rule.

	   The locked acceptance test files remain unchanged. Evidence is recorded in evidence/permission-denied.md.



## Entry 2A - Part 4: Acceptance test review and audit

artifact:  evidence/04-acceptance-test-audit.md;
           tests/acceptance/ (review only).

tool:      ChatGPT, GPT-6.2,
           2026-11-27 to 2026-11-28,
           review and documentation assistant.

prompts:   Reviewed Claude Code's initial acceptance
           test report covering 245 test cases and
           its subsequent correction report addressing
           findings F1-F8.

           Both principal review prompts are consolidated
           in prompts/04-acceptance-test-review.txt.


review:    Reviewed the acceptance tests against
           specification rules R1-R10, clarification
           decisions D1-D8, product owner decisions P1-P4
           and the Part 4 requirements.

           Identified eight findings (F1-F8), covering
           unchanged-state assertions, error responses,
           booking identifiers, concurrency, Unicode
           boundaries, extra fields, restart behavior
           and validation precedence.

           Assisted with preparing the correction prompt
           and reviewed the revised acceptance test suite.

           Claude Code's test-writer subagent performed
           the actual test modifications.

           The revised suite contains 250 test cases.
           All eight review findings were addressed.

           The daily booking limit remains excluded
           from Version 1.

           Assisted with preparing the acceptance test
           audit and reviewing the verification results.

           Final decisions and repository changes
           remained under my control.

checks:    Independent test collection:
           250 acceptance test cases collected.

           Reviewed the following local results:

           python3 tools/check.py tests:
           All checks passed; R1-R10 covered.

           python3 -m pytest tests/acceptance -q --tb=no:
           9 failed, 241 errors, zero passed.

           Failures were expected because app.main
           had not been implemented.

           python3 tools/check_layers.py:
           Expected failure due to missing backend files.

           Local verification commands were executed
           by me and supplied to ChatGPT for review.

evidence:  evidence/04-acceptance-test-audit.md;
           prompts/04-acceptance-test-review.txt;
           prompts/04-acceptance-tests.txt;
           prompts/04-acceptance-test-corrections.txt;
           docs/spec.md, R1-R10 and D1-D8;
           tests/acceptance/;
           commit eac243b, tag a5-tests-locked.

risk:      Acceptance tests have not yet passed against
           a completed backend.

           Worker timeouts cannot forcibly terminate
           running Python threads.

           Shared error helpers depend on successful
           booking creation and listing.

           Booking snapshots cover relevant test dates
           rather than every possible database date.

           Actual tool-level permission enforcement was
	   successfully demonstrated. Claude Code's Edit
	   operation was blocked by the configured deny rule.

	   The locked acceptance test files remain unchanged.
	   Evidence is recorded in evidence/permission-denied.md.




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

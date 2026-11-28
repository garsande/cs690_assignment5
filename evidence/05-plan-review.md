# Part 5 — Backend planning evidence

Date: November 28, 2026. Tools: Claude Code (main agent, plan mode); ChatGPT GPT-6.2 (independent review). Claude version/model not independently confirmed for this session; verify against the session header. Prompts: `prompts/05-backend-plan.txt` and `prompts/05-plan-review.txt`. Final plan: `docs/plan.md`.

## 1. Clarification and decision

Claude asked how GET room_id and DELETE id should parse +1, whitespace, underscores, leading zeros and non-ASCII digits. Options were strict ASCII syntax, Python int(), a new specification decision, or a custom response. The custom response selected Python int() semantics, preserving D1 for POST and D2 for out-of-range identifiers. This is an implementation choice, not a new requirement. The response is recorded as Prompt 2.

## 2. Original Claude plan

The following is a review summary, not a verbatim transcript. The original full response was shared in the ChatGPT conversation; retain that original transcript separately or insert it here before submission if verbatim evidence is desired.

Claude proposed repository.py first, models.py and service.py second, and routes.py and main.py third. The repository would use SQLite AUTOINCREMENT and BEGIN IMMEDIATE for atomic overlap checks. The service would enforce R1–R9, strict JSON integer types, name trimming, date/time validation and precedence. The HTTP layer would translate errors and serve the existing frontend. All 250 acceptance tests were expected to remain failing until main.py exists. Daily limits, additional dependencies and changes to locked tests were excluded. The original plan incorrectly omitted models.py from the expected missing-module list and treated browser verification as optional.

## 3. Independent review findings

| ID | Finding | Resolution in final plan |
|---|---|---|
| F1 | Task 1 expected missing modules incomplete | Four missing modules after Task 1; two after Task 2 |
| F2 | Browser verification optional | Mandatory walkthrough and screenshot with booking visible |
| F3 | Optional formal agent reviews after Task 3 | Reserved for Part 7 |
| F4 | json.loads accepts nonstandard constants | Reject NaN and Infinity, including extra fields; verify otherwise valid body and unchanged state |
| F5 | Python integer conversion limit | Normalize signs, underscores, Unicode decimal digits and leading zeros; preserve global limit; document limitations |
| F6 | Automatic documentation endpoints | Disable docs, redoc and OpenAPI as conservative D8 choice |
| F7 | Smoke-check evidence | Report actual results, without temporary paths in ledger |
| F8 | Factory annotation missing | Preserve create_app(db_path: str = "roombook.db") |

Prompt 3 requested these corrections. F5 and F6 were additional implementation considerations, not explicit handout requirements.

## 4. Revised Claude response (verbatim supplied transcript)

```text
 Here is Claude's plan:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 RoomBook backend plan: R1 to R10 in three tasks

 Context

 app/ holds only __init__.py. The 250 tests in tests/acceptance/ are locked. They cover
 R1–R10 and D1–D8: R1 3, R2 38, R3 86, R4 16, R5 26, R6 10, R7 17, R8 16, R9 26, R10 12.
 The goal is a backend that matches docs/spec.md, passes those tests unedited, and passes
 tools/check_layers.py (L1–L5). frontend/, docs/spec.md, AGENTS.md, and the API
 contract stay unchanged.

 What this means for "done": every acceptance test goes through the client /
 new_client fixtures in tests/conftest.py, which import app.main.create_app. So no
 acceptance test can pass before Task 3. Tasks 1 and 2 are checked with a throwaway smoke
 script kept in the session scratchpad, plus the layer checker. The scratchpad is never
 committed, and the ledger never names temporary paths. Expected checker failures are
 reported word for word, not hidden.

 Run commands with .venv/bin/python. Plain python is not on PATH here; python3 is 3.12.

 Cross-cutting design (from the spec and AGENTS.md):
 - Stdlib only: sqlite3, dataclasses, re, datetime, json. No pydantic request
   models, so FastAPI's automatic 422 bodies never appear and R9 holds.
 - Error flow: the service raises RuleViolation(code, message), and routes map the code to a
   status and {"error", "message"}. Only the six codes in §6 are used.
 - Date and time formats (R2/R3) are checked with re.fullmatch using [0-9]. This avoids
   \d, which matches Unicode digits, and fromisoformat alone, which also accepts 20310314.

 Step 0: record the plan. Before Task 1, write this plan to docs/plan.md, including the
 "Implementation choices" section below.

 Implementation choices

 These resolve ambiguities. They are not new business rules and do not change §1–§6 or D1–D8.

 - IC1. Textual integers (GET room_id, DELETE {id}). Approved by the user. The text is
   parsed with Python int(text), so +1,  1, 1_0, 007 and Unicode decimal digits count
   as integers. A conversion failure gives 422 invalid_request. Integers outside SQLite's
   64-bit range follow D2 and give the applicable 404. POST room_id stays strict under D1:
   it must be a JSON integer, with no bool, float or string.
 - IC2. Python's integer string limit (F5). Python 3.11+ makes int() raise
   ValueError on strings longer than 4300 digits. Such a string is still a valid integer, and
   it is always outside the SQLite range. The limit is not changed globally
   (sys.set_int_max_str_digits is never called). Instead:
   - Textual ids: when int(text) raises ValueError, the service checks the text against
     int()'s own grammar: \s*[+-]?\d+(?:_\d+)*\s*, with re Unicode \d/\s. If it
     matches, the value is treated as out of range, so D2 applies and the response is the
     applicable 404. Otherwise the response is 422 invalid_request.
   - JSON bodies: json.loads(..., parse_int=_parse_int). _parse_int calls int(s). On the
     length ValueError it returns a sign-preserving out-of-range int (2**63 or
     -(2**63) - 1). The value is still a JSON integer for D1 and is still out of range for D2.
     The service then reports R4/R5 first if those fail, and otherwise 404 room_not_found.
   - Remaining limitation (documented): the regex fallback copies int()'s grammar instead
     of calling int(), so rare whitespace or digit-class differences could behave unlike
     int(). The exact value of an over-limit integer is not kept; only "out of range" is.
     Very long URLs may also be rejected by the HTTP server (uvicorn/h11 limits) before the app
     sees them. That is outside the backend's control and outside the tests.
 - IC3. Strict JSON (F4). POST bodies are decoded with
   json.loads(body, parse_constant=_reject, parse_int=_parse_int). _reject raises
   ValueError for NaN, Infinity and -Infinity, so any nonstandard constant gives
   422 invalid_request, including inside extra fields that are otherwise ignored. Invalid
   UTF-8 also raises ValueError and gives 422.
 - IC4. No auto-generated endpoints (F6, D8). FastAPI(docs_url=None, redoc_url=None, openapi_url=None) means /docs, /redoc and /openapi.json do not 
   exist. Unknown routes
   get FastAPI's default 404/405 under D8.

 ---

 Task 1

 app/repository.py. All SQL lives here. It is the only module that imports sqlite3.

 Creates: app/repository.py.

 - _connect(db_path): sqlite3.connect(db_path, timeout=30, isolation_level=None). It is
   closed in finally on every operation. Each operation gets its own connection, never shared.
 - _in_sqlite_range(n): -2**63 <= n < 2**63. This is the D2 guard. Out-of-range ids are
   treated as missing before any SQL runs, so OverflowError never happens.
 - init_db(db_path): creates the tables if they do not exist:
   - rooms(id INTEGER PRIMARY KEY, name, capacity)
   - bookings(id INTEGER PRIMARY KEY AUTOINCREMENT, room_id, date, start, end, booked_by)

   AUTOINCREMENT gives D5: ids are not reused, even across restarts. The four §2 rooms are
   inserted only when rooms is empty.
 - list_rooms(db_path) -> list[dict]: ordered by id.
 - room_exists(db_path, room_id) -> bool: False when out of range.
 - list_bookings(db_path, date, room_id=None) -> list[dict]: ordered by room_id, start.
 - insert_booking_if_free(db_path, room_id, date, start, end, booked_by) -> dict | None
   (D6): runs BEGIN IMMEDIATE, then the overlap query
   (room_id=? AND date=? AND start < :end AND end > :start). On a clash it rolls back and
   returns None. Otherwise it inserts, commits and returns the new row.
 - delete_booking(db_path, booking_id) -> bool: False when out of range or when no row exists.
 - Reads return plain dicts with exactly the §4 fields: 3 for a room, 6 for a booking.

 Done means:
 - Smoke check (scratchpad script, temp DB). The actual output is reported for the ledger
   and evidence, without the script's path. It checks:
   - tables are created and the 4 rooms are seeded, with no duplicates after a second init_db;
   - both list orderings are right;
   - a clash returns None, and touching bookings are accepted;
   - delete returns True, then False;
   - an id issued after a delete is larger than the deleted one;
   - 2**70 and -(2**70) give False or None with no exception.
 - .venv/bin/python tools/check_layers.py fails with L4 only: app/main.py,
   app/routes.py, app/service.py and app/models.py are missing. There are no L1, L2,
   L3 or L5 problems. This failure is expected and is reported word for word.
 - .venv/bin/python -m pytest: 0 of 250 pass. Each test errors with
   No module named 'app.main'. This is expected and is reported with the counts.

 Task 2

 app/models.py and app/service.py. These hold the §5 rules. They have no HTTP code and
 no SQL.

 Creates: app/models.py and app/service.py.

 models.py holds only request data shapes:
 - @dataclass(frozen=True) NewBooking(room_id: int, date: str, start: str, end: str, booked_by: str): the request after it passes R3–R5, with the name trimmed.

 service.py:
 - RuleViolation(Exception), with .code and .message.
 - BookingService(db_path) holds the path and calls repository. Results are passed on as
   dicts.
   - list_rooms(): R1.
   - list_bookings(date_raw: str | None, room_id_raw: str | None): R2. The date is checked
     first (D4): it must be present, match [0-9]{4}-[0-9]{2}-[0-9]{2}, and be a real calendar
     day. Then room_id is parsed with IC1/IC2. Parsing failure gives invalid_request. An
     unknown or out-of-range room gives room_not_found.
   - create_booking(payload: object) -> dict checks the rules in the R9 order:
     - R3: the payload is a dict with all 5 keys. type(room_id) is int (D1). The other
       four fields are str. The date uses the R2 check. Times match [0-9]{2}:[0-9]{2}, with
       the hour at most 23 and the minute at most 59. Extra keys, including id, are ignored.
     - R4: booked_by.strip() must give 1 <= len() <= 40 (D3).
     - R5: minutes are in {0, 30}; start ≥ 08:00; end ≤ 22:00; start < end; at most 180 minutes.
     - R6: repository.room_exists.
     - R7: if repository.insert_booking_if_free returns None, raise overlap.
   - cancel_booking(id_raw: str): R8. The id is parsed with IC1/IC2. Parsing failure gives
     invalid_request. An unknown or out-of-range id gives booking_not_found.

 Done means:
 - Smoke check (scratchpad script calling BookingService on a temp DB). The actual
   output is reported, without the script's path. It checks:
   - one valid and one invalid input per rule, R1–R8;
   - every R9 ordering case in test_r09_errors.py;
   - D4 ordering;
   - IC1 inputs (+1,  1, 1_0, 1.5) and the IC2 input, a 5000-digit id string, which
     gives the 404 code and not 422;
   - after every failed call, a DB snapshot that is unchanged.
 - tools/check_layers.py fails with L4 only: app/main.py and app/routes.py are
   missing. Nothing else is reported. This failure is expected and is reported word for word.
 - pytest: still 0 of 250, for the same reason. The counts are reported.

 Task 3

 app/routes.py and app/main.py. HTTP translation and the application factory.

 Creates: app/routes.py and app/main.py.

 routes.py translates requests and responses only. It imports service, never repository.
 - router = APIRouter(). The service comes from request.app.state.service.
 - ERROR_STATUS maps each code to a status:
   - invalid_request, invalid_name, invalid_time: 422
   - room_not_found, booking_not_found: 404
   - overlap: 409

   An error(code, message) helper builds the JSONResponse with exactly error and message.
 - GET /api/rooms: 200 with the list of rooms.
 - GET /api/bookings: passes the raw request.query_params.get("date") and
   .get("room_id") to the service. FastAPI does no validation of its own.
 - POST /api/bookings: an async handler that runs await request.body(), then the strict
   decode in IC3/IC2. A ValueError gives invalid_request. The service call runs inside
   run_in_threadpool. Success gives 201 with the booking.
 - DELETE /api/bookings/{booking_id}: booking_id: str. Success gives
   Response(status_code=204) with an empty body.
 - Every handler turns RuleViolation into error(...).

 main.py:
 - FRONTEND = Path(__file__).resolve().parent.parent / "frontend", so the path does not
   depend on the working directory (D7).
 - def create_app(db_path: str = "roombook.db") -> FastAPI: is the exact §3 signature.
   a. It calls repository.init_db(db_path). L3 restricts only routes.py.
   b. It creates app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None) (IC4).
   c. It sets app.state.service = BookingService(db_path) and runs app.include_router(router).
   d. It serves GET /, /app.js and /styles.css as FileResponses from FRONTEND.

   There are no other endpoints.

 Done means:
 - .venv/bin/python tools/check_layers.py prints Layer check passed: L1 to L5 hold.
 - .venv/bin/python -m pytest gives 250 passed: R1 3, R2 38, R3 86, R4 16, R5 26,
   R6 10, R7 17 (including the 8-thread D6 test), R8 16, R9 26, R10 12.
 - Spot checks, run with TestClient in the scratchpad and reported:
   - /docs, /redoc and /openapi.json return 404.
   - A body containing {"x": NaN} returns 422 invalid_request and creates nothing.
 - Mandatory browser verification (Part 6):
   a. Start .venv/bin/uvicorn "app.main:create_app" --factory --port 8000. The DB file is a
      *.db file, which .gitignore already covers. Delete it afterwards.
   b. Open http://localhost:8000/ in the browser.
   c. Create a booking and confirm it appears on the page.
   d. Try an overlapping booking in the same room and time, and confirm the page shows the
      overlap error.
   e. Cancel the booking and confirm it is removed.
   f. Capture a screenshot to evidence/page.png.

   If no browser tool is available in the session, stop and ask the human to do steps 2–6
   rather than skip them.
 - git status shows no changes in frontend/, tests/, docs/spec.md or AGENTS.md.

 ---

 Not in this change

 - The daily booking limit and the daily_limit error. §7 lists them as "Proposed, not built".
 - Any endpoint, field, error code or status not in §4 or §6. This includes OpenAPI, docs and
   redoc (disabled, IC4), get-one-booking, edit, room CRUD, and custom 404/405 handlers (D8).
 - Capacity or headcount checks (P2), past-date checks (P1), and auth or ownership checks on
   cancel (P3).
 - Any new or edited tests. tests/acceptance/, tests/conftest.py, frontend/,
   docs/spec.md and AGENTS.md are unchanged.
 - New dependencies, an ORM, migration tools, and changing Python's integer string limit
   globally.
 - Formal reviewer and contract-checker subagent runs. These are kept for Part 7.
 - Committing the smoke scripts or temporary DBs, and naming temporary paths in LEDGER.md.
 - Importing data from legacy/ or the CSV.

 Verification (after each task)

 1. .venv/bin/python tools/check_layers.py: report the exact output.
 2. .venv/bin/python -m pytest: report the pass, fail and error counts.
 3. Tasks 1–2: report the smoke check's actual output, for the ledger and evidence.
 4. Task 3: the spot checks, then the browser walkthrough with evidence/page.png.
 5. After each task, stop and report before going on to the next.
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌

```

## 5. Follow-up review and final plan

The revised plan addressed F1–F8 but assumed every over-limit integer string was out of range, used a weak invalid-JSON spot check with missing required fields, and scheduled the screenshot after cancellation. Prompt 4 requested normalization of leading zeros, an otherwise valid JSON booking with an invalid extra constant, a screenshot showing a booking, and protection of existing databases. It also required actual pytest counts and explicit acceptance-suite execution. The saved `docs/plan.md` incorporates these corrections. IC1–IC4 are accepted at the planning level. No separate final Claude save-response transcript was supplied; the saved plan itself was inspected.

## 6. Actual local verification 

```text
$ git status --short
?? docs/plan.md
?? evidence/05-plan-review.md
?? prompts/05-backend-plan.txt
?? prompts/05-plan-review.txt
$ git diff -- app/ frontend/ tests/ docs/spec.md AGENTS.md
$ git diff a5-tests-locked -- tests/acceptance/
$ grep -n "^## " docs/plan.md
6:## Context
56:## Implementation choices
128:## Task 1
176:## Task 2
231:## Task 3
325:## Not in this change
344:## Verification (after each task)
$ git diff --check
```

The diff commands produced no reported output. The four required headings are present. The whitespace check did not cover untracked files; repeat with git diff --cached --check after staging. The uploaded archive contained the final plan and four Claude prompts; both review-document placeholders were empty. ChatGPT prepared their content without modifying the repository.

## 7. Approval and remaining risks

All eight findings were addressed at the planning level. The service must retain business-rule ownership while the repository provides atomic database operations. Unicode parsing fallback differences, concurrency, HTTP JSON handling and actual test compatibility remain unverified. Use an absolute executable path when starting uvicorn outside the repository. No backend code or acceptance tests were executed by ChatGPT during Part 5. Expected test counts are predictions, not results. Ledger references: Entry 3 and Entry 3A.

# RoomBook backend plan: R1 to R10 in three tasks

Status: approved by the human reviewer, with the final corrections (F2, F4, F5 follow-ups)
applied.

## Context

`app/` holds only `__init__.py`. The 250 tests in `tests/acceptance/` are locked. They cover
R1–R10 and D1–D8:

| File | Tests |
|---|---|
| R1 | 3 |
| R2 | 38 |
| R3 | 86 |
| R4 | 16 |
| R5 | 26 |
| R6 | 10 |
| R7 | 17 |
| R8 | 16 |
| R9 | 26 |
| R10 | 12 |

The goal is a backend that matches `docs/spec.md`, passes those tests unedited, and passes
`tools/check_layers.py` (L1–L5). `frontend/`, `docs/spec.md`, `AGENTS.md`, the locked tests
and the API contract stay unchanged.

**What "done" means before Task 3.** Every acceptance test goes through the `client` /
`new_client` fixtures in `tests/conftest.py`, and those fixtures import
`app.main.create_app`. So no acceptance test can pass before Task 3. Tasks 1 and 2 are checked
with a throwaway smoke script and the layer checker:

- The smoke script is never committed, and the ledger never names temporary paths.
- Its actual output is reported so it can be recorded in the ledger and the evidence.
- An expected checker failure is reported word for word, never hidden.
- pytest's actual pass, failure and error counts are reported exactly as pytest prints them.
  The plan does not assume that a missing `app.main` shows up only as errors; some tests may
  be reported as failures.

On this machine `python` is not on PATH. "`python -m pytest`" is run as
`.venv/bin/python -m pytest`, using the project venv (Python 3.12).

Design that applies to every task (from the spec and AGENTS.md):

- **Stdlib only:** `sqlite3`, `dataclasses`, `re`, `datetime`, `json`, `unicodedata`.
- **No pydantic request models.** FastAPI's automatic 422 bodies therefore never appear, so R9
  holds.
- **Error flow:** the service raises `RuleViolation(code, message)`. Routes map the code to a
  status and return `{"error", "message"}`. Only the six codes in §6 are used.
- **Date and time formats** (R2/R3) use `re.fullmatch` with `[0-9]`. They never use `\d`,
  which matches Unicode digits, and never rely on `fromisoformat` alone, which also accepts
  `20310314`.
- **Review stops:** after each implementation task, work stops for human review before the
  next task begins.

## Implementation choices

These choices resolve ambiguities. They are not new business rules, and they do not change
§1–§6, P1–P4 or D1–D8.

### IC1. Textual integers (GET `room_id`, DELETE `{id}`): approved

The text is parsed with Python's `int(text)` semantics:

- `+1`, ` 1`, `1_0`, `007` and Unicode decimal digits count as integers.
- A string that is not an integer under those semantics gives `422 invalid_request`.
- An integer outside SQLite's 64-bit range follows D2 and gives the applicable 404.

POST `room_id` stays strict under D1: it must be a JSON integer, never a bool, float or string.

### IC2. Python's integer string conversion limit (F5, corrected)

Python 3.11+ raises `ValueError` from `int()` on decimal strings longer than 4300 digits.
**Such a string is not necessarily out of range.** For example, 5000 zeros followed by `1`
is the valid integer 1. The global limit is never changed (`sys.set_int_max_str_digits` is
not called). Instead, textual ids go through `parse_textual_int(text)` in the service, which
returns an `int`, an "out of range" marker, or "invalid":

1. Try `int(text)`. If it succeeds, use the value; the D2 range check happens in the repository.
2. If it raises `ValueError`, check the text against `int()`'s base-10 grammar:
   `\s*[+-]?\d+(?:_\d+)*\s*`. Here `re` uses Unicode `\d`/`\s`, as `int()` does. No match
   means the text is invalid, so the response is `422 invalid_request`.
3. If it matches, **normalize** it:
   - strip the whitespace;
   - take the sign;
   - remove the underscores;
   - map each Unicode decimal digit to ASCII with `unicodedata.decimal`;
   - strip the leading zeros. An empty result means 0.
4. If the remaining significant digits number 19 or fewer, convert them with `int()`. They
   are well under the limit, so this cannot fail. Apply the sign and use the exact value, so
   `0…01` becomes 1 and is looked up as room 1 or booking 1. Otherwise the value has at
   least 10^19 magnitude and is definitely outside SQLite's range, so it is out of range
   (D2), which gives the applicable 404.

**JSON bodies.** These are decoded with `json.loads(..., parse_int=_parse_int)`. Python's
`json` scanner accepts only JSON's integer grammar, which is `-?(0|[1-9][0-9]*)` in ASCII:
no leading zeros, underscores or Unicode digits. A JSON integer over 4300 digits therefore
really has more than 4300 significant digits and is out of range. When `int(s)` raises the
length `ValueError`, `_parse_int` returns a sign-preserving out-of-range `int`, either
`2**63` or `-(2**63) - 1`. That value is still a JSON integer for D1 and still out of range
for D2, so the service reports R4/R5 first if they fail, and otherwise `404 room_not_found`.

**Remaining limitations (documented):**

- Step 2's regex copies `int()`'s grammar instead of calling `int()`. Rare differences in
  Unicode whitespace or digit classes between `re` and `int()` could make an over-limit
  string behave differently from `int()`. Under-limit strings always use `int()` itself.
- For an out-of-range JSON integer over the limit, only "out of range" is kept, not the
  exact value. Nothing needs the exact value.
- Very long URLs or bodies may be rejected by the HTTP server (uvicorn/h11 limits) before
  the app sees them. That is outside the backend's control and not covered by the tests.

### IC3. Strict JSON (F4)

POST bodies are decoded with `json.loads(body, parse_constant=_reject, parse_int=_parse_int)`.
`_reject` raises `ValueError` for `NaN`, `Infinity` and `-Infinity`. Any nonstandard constant
therefore gives `422 invalid_request`, **including inside extra fields that would otherwise be
ignored**. Invalid UTF-8 also raises `ValueError` and gives 422.

### IC4. No auto-generated endpoints (F6, D8)

`FastAPI(docs_url=None, redoc_url=None, openapi_url=None)` means `/docs`, `/redoc` and
`/openapi.json` do not exist. Unknown routes and methods get FastAPI's default 404/405 under
D8.

---

## Task 1

**`app/repository.py`**: all SQL. This is the only module that imports `sqlite3`.

**Creates:** `app/repository.py`.

Functions:

- `_connect(db_path)`: opens the connection with
  `sqlite3.connect(db_path, timeout=30, isolation_level=None)` and closes it in `finally`.
  Each operation gets its own connection; a connection is never shared.
- `_in_sqlite_range(n)`: `-2**63 <= n < 2**63`. This is the D2 guard. Out-of-range ids are
  treated as missing before any SQL runs, so `OverflowError` never happens.
- `init_db(db_path)`: creates the tables if they do not exist.
  - `rooms(id INTEGER PRIMARY KEY, name, capacity)`.
  - `bookings(id INTEGER PRIMARY KEY AUTOINCREMENT, room_id, date, start, end, booked_by)`.
    `AUTOINCREMENT` gives D5: ids are never reused, even across restarts.
  - The four §2 rooms are inserted only when `rooms` is empty.
- `list_rooms(db_path) -> list[dict]`: ordered by `id`.
- `room_exists(db_path, room_id) -> bool`: False when out of range.
- `list_bookings(db_path, date, room_id=None) -> list[dict]`: ordered by `room_id, start`.
- `insert_booking_if_free(db_path, room_id, date, start, end, booked_by) -> dict | None`
  (D6): runs `BEGIN IMMEDIATE`, then the overlap query
  `room_id=? AND date=? AND start < :end AND end > :start`. On a clash it rolls back and
  returns None. Otherwise it inserts, commits and returns the new row.
- `delete_booking(db_path, booking_id) -> bool`: False when out of range or when there is
  no row.

Reads return plain dicts with exactly the §4 fields: 3 for a room, 6 for a booking.

**Done means:**

- **Smoke check.** A scratchpad script runs against a disposable temp DB. Its actual output
  is reported, without the script path. It confirms:
  - the tables are created and the 4 rooms are seeded;
  - a second `init_db` adds no duplicate rooms;
  - both list orderings are correct;
  - a clash returns None, and touching bookings are accepted;
  - delete returns True, then False;
  - an id issued after a delete is larger than the deleted one;
  - `2**70` and `-(2**70)` give False/None with no exception.
- **Layer checker.** `tools/check_layers.py` fails with **L4 only**. It reports `app/main.py`,
  `app/routes.py`, `app/service.py` and `app/models.py` as missing, with no L1, L2, L3 or L5
  problems. This is expected and is reported word for word.
- **pytest.** `python -m pytest` and `python -m pytest tests/acceptance` pass 0 of 250. The
  actual passed, failed and error counts are reported as printed.
- **Stop for human review.**

## Task 2

**`app/models.py` and `app/service.py`**: the §5 rules, with no HTTP code and no SQL.

**Creates:** `app/models.py` and `app/service.py`.

`models.py` holds request data shapes only:

- `@dataclass(frozen=True) NewBooking(room_id: int, date: str, start: str, end: str,
  booked_by: str)`: the request after R3–R5 pass, with the name already trimmed.

`service.py`:

- `RuleViolation(Exception)`, with `.code` and `.message`.
- `parse_textual_int(text)`, which implements IC1 and IC2.
- `BookingService(db_path)` holds the path and calls `repository`. Results are passed on as
  dicts.
  - `list_rooms()`: R1.
  - `list_bookings(date_raw: str | None, room_id_raw: str | None)`: R2.
    - The date is checked first (D4). It must be present, match
      `[0-9]{4}-[0-9]{2}-[0-9]{2}`, and be a real calendar day.
    - Then `room_id` goes through `parse_textual_int`. Invalid gives `invalid_request`.
      Unknown or out of range gives `room_not_found`.
  - `create_booking(payload: object) -> dict`, in the R9 order:
    - **R3:** the payload is a `dict` with all 5 keys. `type(room_id) is int` (D1). The other
      four fields are `str`. The date uses the R2 check. Times match `[0-9]{2}:[0-9]{2}` with
      the hour at most 23 and the minute at most 59. Extra keys, including `id`, are ignored.
    - **R4:** `booked_by.strip()` has `1 <= len() <= 40` (D3).
    - **R5:** the minutes are in {0, 30}; start ≥ 08:00; end ≤ 22:00; start < end; at most
      180 minutes.
    - **R6:** `repository.room_exists`.
    - **R7:** `repository.insert_booking_if_free` returns None, which gives `overlap`.
  - `cancel_booking(id_raw: str)`: R8. The id goes through `parse_textual_int`. Invalid gives
    `invalid_request`. Unknown or out of range gives `booking_not_found`.

**Done means:**

- **Smoke check.** A scratchpad script calls `BookingService` on a disposable temp DB. Its
  actual output is reported, without the script path. It covers:
  - a valid and an invalid input for each of R1–R8;
  - every R9 ordering case in `test_r09_errors.py`;
  - the D4 ordering;
  - IC1 inputs `+1`, ` 1`, `1_0`, `007`, a Unicode-digit `１`, and the invalid `1.5`;
  - IC2 inputs:
    - 5000 zeros followed by `1` resolves to 1, so room 1 is found and booking 1 is looked up;
    - a 5000-digit non-zero string gives the 404 code, not 422;
    - an underscored over-limit string with leading zeros is normalized correctly.
  - a DB snapshot after every failed call, which must be unchanged.
- **Layer checker.** `tools/check_layers.py` fails with **L4 only**. It reports `app/main.py`
  and `app/routes.py` as missing and nothing else. This is expected and is reported word for
  word.
- **pytest.** `python -m pytest` and `python -m pytest tests/acceptance` still pass 0 of 250.
  The actual passed, failed and error counts are reported.
- **Stop for human review.**

## Task 3

**`app/routes.py` and `app/main.py`**: HTTP translation and the application factory.

**Creates:** `app/routes.py` and `app/main.py`.

`routes.py` translates requests and responses only. It imports `service`, never `repository`.

- `router = APIRouter()`. The service comes from `request.app.state.service`.
- `ERROR_STATUS` maps each code to a status:
  - `invalid_request`, `invalid_name`, `invalid_time`: 422.
  - `room_not_found`, `booking_not_found`: 404.
  - `overlap`: 409.
- `error(code, message)` returns a `JSONResponse` with exactly `error` and `message`.
- `GET /api/rooms` returns 200 with the list.
- `GET /api/bookings` passes the raw `request.query_params.get("date")` and
  `.get("room_id")` to the service. FastAPI does no validation of its own.
- `POST /api/bookings` is an async handler.
  - It reads the body with `await request.body()` and decodes it strictly (IC3/IC2).
    `ValueError` gives `invalid_request`.
  - The service call runs in `run_in_threadpool`.
  - It returns 201 with the booking.
- `DELETE /api/bookings/{booking_id}` takes `booking_id: str` and returns
  `Response(status_code=204)` with an empty body.
- Every handler turns a `RuleViolation` into `error(...)`.

`main.py`:

- `FRONTEND = Path(__file__).resolve().parent.parent / "frontend"`, so the path does not
  depend on the working directory (D7).
- `def create_app(db_path: str = "roombook.db") -> FastAPI:` keeps the exact §3 signature. It:
  1. calls `repository.init_db(db_path)` (L3 restricts only `routes.py`);
  2. creates `app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)` (IC4);
  3. sets `app.state.service = BookingService(db_path)` and calls
     `app.include_router(router)`;
  4. serves `GET /`, `/app.js` and `/styles.css` as `FileResponse`s from `FRONTEND`.

  It adds no other endpoints.

**Done means:**

- **Layer checker.** `tools/check_layers.py` prints `Layer check passed: L1 to L5 hold.`
- **pytest.** `python -m pytest tests/acceptance`, run explicitly as Part 6 requires, gives
  **250 passed**:

  | File | Tests |
  |---|---|
  | R1 | 3 |
  | R2 | 38 |
  | R3 | 86 |
  | R4 | 16 |
  | R5 | 26 |
  | R6 | 10 |
  | R7 | 17, including the 8-thread D6 test |
  | R8 | 16 |
  | R9 | 26 |
  | R10 | 12 |

  `python -m pytest` is also run. The actual passed, failed and error counts for both runs
  are reported.
- **Spot checks.** These run with TestClient on a disposable temp DB, and the results are
  reported.
  - `/docs`, `/redoc` and `/openapi.json` return 404 (IC4).
  - **Strict JSON (IC3).** Two raw bodies are POSTed, each an otherwise valid booking request
    with all five required fields plus one extra field:
    `{"room_id": 1, "date": "2031-03-14", "start": "09:00", "end": "10:00", "booked_by": "Ana", "extra": NaN}`,
    and the same request with `Infinity`. Each must return `422 invalid_request`, and the
    booking snapshot must be unchanged.
  - **IC2 through HTTP.** `GET /api/bookings?date=2031-03-14&room_id=` with 5000 zeros
    followed by `1` returns 200 with room 1's bookings.
- **Mandatory browser verification (Part 6).**
  1. Use a disposable database. Start uvicorn from a new, empty scratchpad directory with
     `--app-dir` pointing at the repo, so the default `roombook.db` is created there and not
     in the repo:
     `.venv/bin/uvicorn app.main:create_app --factory --port 8000 --app-dir <repo>`
     First check that the target file does not already exist. Never delete or overwrite an
     existing database.
  2. Open `http://localhost:8000/` in a browser.
  3. Create booking A, then booking B in a different slot. Confirm that both appear.
  4. Try a booking that overlaps A in the same room and time. Confirm that the page shows
     the overlap error and that A is unchanged.
  5. Cancel B. Confirm that B is removed and A stays.
  6. With A still visible on the page, capture **`evidence/page.png`**.
  7. Stop uvicorn. Delete the disposable verification database only after the human
     approves.

  If no browser tool is available in the session, stop and ask the human to do steps 2–6
  rather than skip them.
- **Unchanged files.** `git status` shows no changes to `frontend/`, `tests/`,
  `docs/spec.md` or `AGENTS.md`.
- **Stop for human review.**

---

## Not in this change

- The daily booking limit and the `daily_limit` error ("Proposed, not built" in §7).
- Any endpoint, field, error code or status not in §4/§6. This includes OpenAPI, docs and
  redoc (disabled, IC4), a get-one-booking endpoint, editing, room CRUD, and custom 404/405
  handlers (D8).
- Capacity or headcount checks (P2), past-date checks (P1), and auth or ownership checks on
  cancel (P3).
- New or edited tests. `tests/acceptance/`, `tests/conftest.py`, `frontend/`,
  `docs/spec.md` and `AGENTS.md` stay unchanged.
- New dependencies, an ORM, migration tooling, and changes to Python's global integer
  string conversion limit.
- Formal `reviewer` and `contract-checker` subagent runs. These are reserved for Part 7.
- Committing smoke scripts or temporary databases, and naming temporary paths in `LEDGER.md`.
- Automatically deleting any database. Only the disposable verification database is removed,
  and only after the human approves.
- Importing data from `legacy/` or its CSV.
- Commits. These are made only when the human asks.

## Verification (after each task)

1. Run `python -m pytest tests/acceptance` and `python -m pytest`, and report the actual
   passed, failed and error counts.
2. Run `python tools/check_layers.py` and report its exact output.
3. For Tasks 1 and 2, report the smoke check's actual output, for the ledger and evidence.
4. For Task 3, run the spot checks, then the browser walkthrough that ends with
   `evidence/page.png`.
5. Stop for human review before the next task.

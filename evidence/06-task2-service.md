# Task 2 — Models and service evidence

Date: 2026-11-28. Claude Code main agent implemented the task; ChatGPT GPT-6.2 provided independent review. Claude version/model should be confirmed from the session.

## Original implementation response

The Task 2 portion of the supplied transcript follows.

```text
❯ Do Task 2 of docs/plan.md and nothing else. Follow
  AGENTS.md. When you finish, run python tools/check_layers.py
  and python -m pytest tests/acceptance, and report the
  results. Do not edit any test.

  Ran 1 shell command

● Write(app/models.py)
Wrote 16 lines to app/models.py
"""Request data shapes for RoomBook. No HTTP code and no SQL."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NewBooking:
    """A POST /api/bookings request that has passed R3 to R5, with the name trimmed."""
… +6 lines

● Write(app/service.py)
Wrote 198 lines to app/service.py
"""The section 5 booking rules for RoomBook. No HTTP code and no SQL.

Every rule failure is raised as RuleViolation(code, message), using only the
codes in section 6. The HTTP layer maps each code to its status.
"""

from __future__ import annotations

import datetime
import re
… +188 lines

Now the Task 2 smoke script.

  Ran 1 shell command

Task 2 is done: I created app/models.py and app/service.py and changed nothing else. The smoke check passed, and the layer checker and pytest both fail exactly as the plan predicts for Task 2. I've stopped here for your review before Task 3.

What I built:
- app/models.py holds only NewBooking, a frozen dataclass for a request that has passed R3–R5, with the name already trimmed.
- app/service.py has no HTTP code and no SQL; it calls repository for everything stored. It contains:
  - RuleViolation(code, message) and the six §6 error codes. No other codes are used.
  - parse_textual_int, which follows IC1 and IC2. It returns an int, OUT_OF_RANGE or INVALID, and never changes Python's global integer limit.
  - BookingService with list_rooms (R1), list_bookings (R2, checking the date before room_id per D4), create_booking (R3→R4→R5→R6→R7, the R9 order) and cancel_booking (R8).
  - Date and time checks that only accept the ASCII digits 0–9, so other Unicode digits are rejected, and dates must be real calendar days. room_id is rejected unless it is a true integer (D1), and names are trimmed with strip() and counted with len() (D3).

Smoke check (run once against a temporary database, which was then deleted; the script isn't committed). After every call that should fail, it compared the rooms, bookings and id-counter tables before and after, and none had changed.
--- R1
PASS 4 rooms in id order
--- R3/R4/R5/R6/R7 create
PASS valid create, name trimmed, extras ignored: {'id': 1, 'room_id': 1, 'date': '2031-03-14', 'start': '09:00', 'end': '10:00', 'booked_by': 'Ana  Lee'}
PASS touching booking accepted (R7)
PASS R3 not a dict -> invalid_request (got invalid_request; db unchanged=True)
PASS R3 missing field -> invalid_request (got invalid_request; db unchanged=True)
PASS R3 room_id bool (D1) -> invalid_request (got invalid_request; db unchanged=True)
PASS R3 room_id float (D1) -> invalid_request (got invalid_request; db unchanged=True)
PASS R3 room_id string (D1) -> invalid_request (got invalid_request; db unchanged=True)
PASS R3 date Unicode digits -> invalid_request (got invalid_request; db unchanged=True)
PASS R3 date 20310314 -> invalid_request (got invalid_request; db unchanged=True)
PASS R3 time 24:00 -> invalid_request (got invalid_request; db unchanged=True)
PASS R3 time 09:60 -> invalid_request (got invalid_request; db unchanged=True)
PASS R4 41 chars -> invalid_name (got invalid_name; db unchanged=True)
PASS R4 40 chars ok
PASS R5 :15 minutes -> invalid_time (got invalid_time; db unchanged=True)
PASS R5 before 08:00 -> invalid_time (got invalid_time; db unchanged=True)
PASS R5 after 22:00 -> invalid_time (got invalid_time; db unchanged=True)
PASS R5 start == end -> invalid_time (got invalid_time; db unchanged=True)
PASS R5 210 minutes -> invalid_time (got invalid_time; db unchanged=True)
PASS R5 exactly 180 minutes ok
PASS R6 room 5 -> room_not_found (got room_not_found; db unchanged=True)
PASS R6 room 2**63 (out of range) -> room_not_found (got room_not_found; db unchanged=True)
PASS R6 room -(2**63)-1 -> room_not_found (got room_not_found; db unchanged=True)
PASS R7 overlap -> overlap (got overlap; db unchanged=True)
--- R2 list
PASS list ordered by room_id, start
PASS room filter
PASS empty date gives []
PASS R2 date missing -> invalid_request (got invalid_request; db unchanged=True)
PASS R2 2031-02-30 -> invalid_request (got invalid_request; db unchanged=True)
PASS R2 room_id abc -> invalid_request (got invalid_request; db unchanged=True)
PASS R2 room_id 6 -> room_not_found (got room_not_found; db unchanged=True)
PASS D4 bad date + bad room_id -> date first -> invalid_request (got invalid_request; db unchanged=True)
PASS D4 bad date + unknown room -> date first -> invalid_request (got invalid_request; db unchanged=True)
--- R9 ordering (test_r09_errors.py cases)
PASS R3>R4 missing date + empty name -> invalid_request (got invalid_request; db unchanged=True)
PASS R3>R4 bad date + long name -> invalid_request (got invalid_request; db unchanged=True)
PASS R3>R5 9:00 + :15 -> invalid_request (got invalid_request; db unchanged=True)
PASS R3>R6 10:3 + room 99 -> invalid_request (got invalid_request; db unchanged=True)
PASS R3>R6 slashes + room 99 -> invalid_request (got invalid_request; db unchanged=True)
PASS R3>R7 name 123 + overlap -> invalid_request (got invalid_request; db unchanged=True)
PASS R3>R4,R5,R6 -> invalid_request (got invalid_request; db unchanged=True)
PASS R4>R5 -> invalid_name (got invalid_name; db unchanged=True)
PASS R4>R6 -> invalid_name (got invalid_name; db unchanged=True)
PASS R4>R7 -> invalid_name (got invalid_name; db unchanged=True)
PASS R4>R5,R6 -> invalid_name (got invalid_name; db unchanged=True)
PASS R4>R5,R7 -> invalid_name (got invalid_name; db unchanged=True)
PASS R5>R6 -> invalid_time (got invalid_time; db unchanged=True)
PASS R5>R7 210 min -> invalid_time (got invalid_time; db unchanged=True)
PASS R5>R7 :15 inside existing -> invalid_time (got invalid_time; db unchanged=True)
PASS R6 only (room 0) -> room_not_found (got room_not_found; db unchanged=True)
--- IC1
PASS parse_textual_int('+1') = 1
PASS parse_textual_int(' 1') = 1
PASS parse_textual_int('1_0') = 10
PASS parse_textual_int('007') = 7
PASS parse_textual_int('１') = 1
PASS parse_textual_int('1.5') = INVALID
PASS parse_textual_int('') = INVALID
PASS parse_textual_int('abc') = INVALID
PASS room_id '+1' finds room 1
PASS room_id '\uff11' finds room 1
PASS room_id '1.5' -> invalid_request (got invalid_request; db unchanged=True)
PASS cancel '1.5' -> invalid_request (got invalid_request; db unchanged=True)
--- IC2
PASS 5000 zeros + 1 -> 1
PASS room_id 0..01 lists room 1
PASS 5000 nines -> OUT_OF_RANGE
PASS -5000 nines -> OUT_OF_RANGE
PASS room_id 5000 nines -> room_not_found (got room_not_found; db unchanged=True)
PASS cancel 5000 nines -> booking_not_found (got booking_not_found; db unchanged=True)
PASS underscored over-limit with leading zeros -> 42
PASS '- 0..0_7' with whitespace and sign -> -7
PASS over-limit bad grammar (double underscore) -> INVALID
PASS over-limit with letter -> INVALID
--- R8 cancel
PASS cancel 'xyz' -> invalid_request (got invalid_request; db unchanged=True)
PASS cancel unknown 106 -> booking_not_found (got booking_not_found; db unchanged=True)
PASS cancel 2**70 -> booking_not_found (got booking_not_found; db unchanged=True)
PASS 0..01 cancels booking 1
PASS cancel same id again -> booking_not_found (got booking_not_found; db unchanged=True)
PASS freed slot can be booked again
ALL SMOKE CHECKS PASSED
Note on two smoke-output labels:
- "cancel 2**70" is the D2 range check through cancel_booking; the over-length text cases are the IC2 lines.
- The "'- 0..0_7'" check actually feeds the text with no space after the minus sign.

python tools/check_layers.py (run as .venv/bin/python) exited with code 1. This is the expected L4-only failure, with no L1, L2, L3 or L5 problems:
Layer check FAILED:
  L4: app/main.py is missing
  L4: app/routes.py is missing

python -m pytest tests/acceptance: 9 failed, 241 errors in 2.48s, so 0 of 250 pass. All 250 fail with ModuleNotFoundError: No module named 'app.main'. I also ran python -m pytest with the same result: 9 failed, 241 errors.

No tests were edited. git status shows only app/models.py and app/service.py as new. Nothing has been committed.
```

## Independent review and F1

The frozen NewBooking model and service separation, R1–R9 validation, D1–D4 and IC1–IC2 were reviewed. F1: regex whitespace and strip accepted U+001C–U+001F in the fallback although int() rejects them. Independent examples were `"\x1c1"` and `"1\x1f"`. The reviewer requested a localized correction and regression checks, without changing protected files. The initial independent service checks passed for creation, name trimming, invalid dates, precedence, overlap, range checks, cancellation and unchanged state after six rejected calls.

## Correction response (summary, not verbatim)

Claude changed the fallback regex to capture leading whitespace, sign, digit groups and trailing whitespace. A short probe of distinct characters is validated using int() before normalization. Claude reported 77 original smoke checks and 58 regression checks passed, zero mismatches in its Unicode experiment, unchanged database snapshots after rejected calls and global limit unchanged at 4300. Layer checker exited 1 for missing main.py and routes.py only. Acceptance pytest: 9 failed, 241 errors in 2.23s, all missing app.main; full pytest same counts. Claude reported no test edits or commit. The command output also showed a ledger whitespace change and prompt heading formatting change; attribution to the agent is not established. The complete correction response remains in the chat; this section is a summary.

## Local verification

Models: 16 lines; service: 214 lines. Protected file diffs empty. Layer checker: two expected L4 missing modules. Acceptance tests: 0 passed, 9 failed, 241 errors in 1.73s, all missing app.main. git diff --check flagged LEDGER.md:855 new blank line at EOF; fix before commit. Full supplied transcript follows.

```text
 git status --short

git diff --no-index /dev/null app/models.py

git diff --no-index /dev/null app/service.py

git diff HEAD -- app/repository.py

git diff a5-tests-locked -- tests/acceptance/

git diff HEAD -- frontend/ docs/spec.md docs/plan.md AGENTS.md

git diff -- LEDGER.md

python3 tools/check_layers.py

python3 -m pytest tests/acceptance -q --tb=no

git diff --check
 M LEDGER.md
?? app/models.py
?? app/service.py
?? prompts/06-task2-service.txt
diff --git a/app/models.py b/app/models.py
new file mode 100644
index 0000000..bf24b6c
--- /dev/null
+++ b/app/models.py
@@ -0,0 +1,16 @@
+"""Request data shapes for RoomBook. No HTTP code and no SQL."""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+
+
+@dataclass(frozen=True)
+class NewBooking:
+    """A POST /api/bookings request that has passed R3 to R5, with the name trimmed."""
+
+    room_id: int
+    date: str
+    start: str
+    end: str
+    booked_by: str
diff --git a/app/service.py b/app/service.py
new file mode 100644
index 0000000..e6385cb
--- /dev/null
+++ b/app/service.py
@@ -0,0 +1,214 @@
+"""The section 5 booking rules for RoomBook. No HTTP code and no SQL.
+
+Every rule failure is raised as RuleViolation(code, message), using only the
+codes in section 6. The HTTP layer maps each code to its status.
+"""
+
+from __future__ import annotations
+
+import datetime
+import re
+import unicodedata
+
+from . import repository
+from .models import NewBooking
+
+# Section 6 error codes.
+INVALID_REQUEST = "invalid_request"
+INVALID_NAME = "invalid_name"
+INVALID_TIME = "invalid_time"
+ROOM_NOT_FOUND = "room_not_found"
+BOOKING_NOT_FOUND = "booking_not_found"
+OVERLAP = "overlap"
+
+_REQUIRED_FIELDS = ("room_id", "date", "start", "end", "booked_by")
+
+# ASCII digits only: "\d" would also match other Unicode decimal digits.
+_DATE_SHAPE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
+_TIME_SHAPE = re.compile(r"[0-9]{2}:[0-9]{2}")
+
+# The shape of int()'s base-10 grammar (IC2 step 2): whitespace, sign, digit groups
+# split by single underscores, whitespace. Unicode \s and \d are wider than or equal to
+# what int() accepts (for example \s matches U+001C..U+001F, which int() rejects), so
+# parse_textual_int asks int() itself to confirm the whitespace and digit characters.
+_INT_GRAMMAR = re.compile(r"(\s*)([+-]?)(\d+(?:_\d+)*)(\s*)")
+
+_OPEN = 8 * 60
+_CLOSE = 22 * 60
+_MAX_MINUTES = 180
+
+
+class RuleViolation(Exception):
+    """A request broke a section 5 rule."""
+
+    def __init__(self, code: str, message: str) -> None:
+        super().__init__(message)
+        self.code = code
+        self.message = message
+
+
+class _Marker:
+    def __init__(self, name: str) -> None:
+        self._name = name
+
+    def __repr__(self) -> str:
+        return self._name
+
+
+# Results of parse_textual_int besides a plain int.
+OUT_OF_RANGE = _Marker("OUT_OF_RANGE")
+INVALID = _Marker("INVALID")
+
+
+def parse_textual_int(text: str) -> int | _Marker:
+    """Parse a textual id with int() semantics (IC1), working past int()'s length limit (IC2).
+
+    Returns the int, OUT_OF_RANGE for an integer of 10**19 or more in magnitude, or
+    INVALID when the text is not an integer.
+    """
+    try:
+        return int(text)
+    except ValueError:
+        pass
+    # int() refused the text. Fall back only when the refusal is int()'s length limit.
+    match = _INT_GRAMMAR.fullmatch(text)
+    if match is None:
+        return INVALID
+    lead, sign, body, trail = match.groups()
+    digits = body.replace("_", "")
+    # Let int() itself judge every whitespace and digit character, on a probe short
+    # enough to stay under the length limit (each distinct character once). If int()
+    # rejects the probe, it rejects the original text for that same reason.
+    probe = (
+        "".join(dict.fromkeys(lead))
+        + sign
+        + "".join(dict.fromkeys(digits))
+        + "".join(dict.fromkeys(trail))
+    )
+    try:
+        int(probe)
+    except ValueError:
+        return INVALID
+    negative = sign == "-"
+    digits = "".join(str(unicodedata.decimal(ch)) for ch in digits).lstrip("0")
+    if len(digits) > 19:
+        return OUT_OF_RANGE
+    value = int(digits) if digits else 0
+    return -value if negative else value
+
+
+def _is_valid_date(value: str) -> bool:
+    """R2: exactly YYYY-MM-DD and a real calendar day."""
+    if not _DATE_SHAPE.fullmatch(value):
+        return False
+    try:
+        datetime.date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
+    except ValueError:
+        return False
+    return True
+
+
+def _is_valid_time(value: str) -> bool:
+    """R3: exactly HH:MM, from 00:00 to 23:59."""
+    if not _TIME_SHAPE.fullmatch(value):
+        return False
+    return int(value[0:2]) <= 23 and int(value[3:5]) <= 59
+
+
+def _minutes(value: str) -> int:
+    return int(value[0:2]) * 60 + int(value[3:5])
+
diff --git a/LEDGER.md b/LEDGER.md
index a4cf82e..fbbc46b 100644
--- a/LEDGER.md
+++ b/LEDGER.md
@@ -852,4 +852,5 @@ risk:      The independent repository checks do not
            Concurrent requests through the HTTP interface,
            database isolation and restart behavior must
            still pass the locked acceptance tests.
+

\ No newline at end of file
Layer check FAILED:
  L4: app/main.py is missing
  L4: app/routes.py is missing
EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE [ 59%]
EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEFFFFFFFFF                                               [100%]
================================================================= short test summary info ==================================================================
FAILED tests/acceptance/test_r10_application.py::test_r10_serves_page_independent_of_working_directory - ModuleNotFoundError: No module named 'app.main'
FAILED tests/acceptance/test_r10_application.py::test_r10_fresh_database_has_four_rooms_and_no_bookings - ModuleNotFoundError: No module named 'app.main'
FAILED tests/acceptance/test_r10_application.py::test_r10_database_file_is_created_at_db_path - ModuleNotFoundError: No module named 'app.main'
FAILED tests/acceptance/test_r10_application.py::test_r10_different_files_do_not_share_bookings - ModuleNotFoundError: No module named 'app.main'
FAILED tests/acceptance/test_r10_application.py::test_r10_restart_on_same_file_sees_saved_bookings - ModuleNotFoundError: No module named 'app.main'
FAILED tests/acceptance/test_r10_application.py::test_r10_restart_keeps_rooms_without_duplicates - ModuleNotFoundError: No module named 'app.main'
FAILED tests/acceptance/test_r10_application.py::test_r10_restart_still_enforces_overlap - ModuleNotFoundError: No module named 'app.main'
FAILED tests/acceptance/test_r10_application.py::test_r10_cancel_persists_across_restart - ModuleNotFoundError: No module named 'app.main'
FAILED tests/acceptance/test_r10_application.py::test_r10_ids_not_reused_across_restart - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r01_rooms.py::test_r1_lists_four_rooms_in_id_order - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r01_rooms.py::test_r1_each_room_has_exactly_three_fields - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r01_rooms.py::test_r1_rooms_unchanged_after_bookings - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_empty_date_returns_empty_list - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_returns_only_bookings_on_given_date - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_booking_objects_have_exactly_six_fields - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_ordered_by_room_id_then_start - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_room_filter_returns_only_that_room - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_room_filter_with_no_bookings_returns_empty_list - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_leap_day_is_a_valid_date - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_missing_date_is_invalid_request - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_missing_date_with_room_id_is_invalid_request - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_badly_formatted_date_is_invalid_request[] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_badly_formatted_date_is_invalid_request[2031-3-14] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_badly_formatted_date_is_invalid_request[2031-03-4] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_badly_formatted_date_is_invalid_request[31-03-14] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_badly_formatted_date_is_invalid_request[20310314] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_badly_formatted_date_is_invalid_request[2031/03/14] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_badly_formatted_date_is_invalid_request[2031-03-14T00:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_badly_formatted_date_is_invalid_request[ 2031-03-14] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_badly_formatted_date_is_invalid_request[2031-03-14 ] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_badly_formatted_date_is_invalid_request[abcd-ef-gh] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_badly_formatted_date_is_invalid_request[14-03-2031] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_non_calendar_date_is_invalid_request[2031-02-29] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_non_calendar_date_is_invalid_request[2031-02-30] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_non_calendar_date_is_invalid_request[2031-04-31] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_non_calendar_date_is_invalid_request[2031-13-01] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_non_calendar_date_is_invalid_request[2031-00-10] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_non_calendar_date_is_invalid_request[2031-01-00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_non_calendar_date_is_invalid_request[2031-01-32] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_non_integer_room_id_is_invalid_request[abc] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_non_integer_room_id_is_invalid_request[1.5] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_non_integer_room_id_is_invalid_request[one] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_non_integer_room_id_is_invalid_request[1a] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_unknown_room_id_is_room_not_found[0] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_unknown_room_id_is_room_not_found[5] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_unknown_room_id_is_room_not_found[-1] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_unknown_room_id_is_room_not_found[99] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_room_id_beyond_sqlite_range_is_room_not_found - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_invalid_date_checked_before_unknown_room - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r02_list_bookings.py::test_r2_invalid_date_checked_before_non_integer_room - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_valid_request_creates_booking - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_created_booking_is_listed - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_extra_fields_are_ignored - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_client_supplied_id_is_ignored - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_past_date_is_allowed - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_leap_day_is_accepted - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_invalid_json_is_invalid_request - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_empty_body_is_invalid_request - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_body_not_an_object_is_invalid_request[payload0] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_body_not_an_object_is_invalid_request[payload1] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_body_not_an_object_is_invalid_request[text] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_body_not_an_object_is_invalid_request[42] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_body_not_an_object_is_invalid_request[True] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_missing_field_is_invalid_request[room_id] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_missing_field_is_invalid_request[date] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_missing_field_is_invalid_request[start] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_missing_field_is_invalid_request[end] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_missing_field_is_invalid_request[booked_by] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_empty_object_is_invalid_request - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_room_id_wrong_type_is_invalid_request[1] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_room_id_wrong_type_is_invalid_request[1.0] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_room_id_wrong_type_is_invalid_request[1.5] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_room_id_wrong_type_is_invalid_request[True] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_room_id_wrong_type_is_invalid_request[False] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_room_id_wrong_type_is_invalid_request[None] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_room_id_wrong_type_is_invalid_request[value6] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_room_id_wrong_type_is_invalid_request[value7] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[123-date] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[123-start] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[123-end] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[123-booked_by] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[None-date] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[None-start] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[None-end] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[None-booked_by] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[True-date] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[True-start] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[True-end] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[True-booked_by] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[value3-date] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[value3-start] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[value3-end] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[value3-booked_by] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[value4-date] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[value4-start] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[value4-end] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_string_field_wrong_type_is_invalid_request[value4-booked_by] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_date_is_invalid_request[] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_date_is_invalid_request[2031-3-14] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_date_is_invalid_request[2031-03-4] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_date_is_invalid_request[20310314] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_date_is_invalid_request[2031/03/14] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_date_is_invalid_request[ 2031-03-14] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_date_is_invalid_request[2031-03-14 ] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_date_is_invalid_request[14-03-2031] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_non_calendar_date_is_invalid_request[2031-02-29] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_non_calendar_date_is_invalid_request[2031-02-30] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_non_calendar_date_is_invalid_request[2031-04-31] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_non_calendar_date_is_invalid_request[2031-13-01] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_non_calendar_date_is_invalid_request[2031-00-10] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_start_is_invalid_request[9:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_start_is_invalid_request[09:0] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_start_is_invalid_request[0900] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_start_is_invalid_request[09-00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_start_is_invalid_request[09:00:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_start_is_invalid_request[24:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_start_is_invalid_request[25:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_start_is_invalid_request[09:60] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_start_is_invalid_request[9:30] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_start_is_invalid_request[] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_start_is_invalid_request[ 09:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_start_is_invalid_request[ab:cd] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_end_is_invalid_request[9:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_end_is_invalid_request[09:0] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_end_is_invalid_request[0900] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_end_is_invalid_request[09-00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_end_is_invalid_request[09:00:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_end_is_invalid_request[24:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_end_is_invalid_request[25:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_end_is_invalid_request[09:60] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_end_is_invalid_request[9:30] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_end_is_invalid_request[] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_end_is_invalid_request[ 09:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_badly_formatted_end_is_invalid_request[ab:cd] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_failed_request_keeps_existing_bookings - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r03_request_shape.py::test_r3_json_null_body_is_invalid_request - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_name_is_trimmed_in_response_and_storage - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_tabs_and_newlines_are_trimmed - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_internal_whitespace_and_case_preserved - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_one_character_name_is_accepted - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_forty_character_name_is_accepted - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_forty_characters_after_trimming_is_accepted - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_forty_unicode_code_points_is_accepted - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_forty_supplementary_plane_characters_is_accepted - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_forty_one_supplementary_plane_characters_is_invalid_name - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_forty_one_characters_is_invalid_name - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_forty_one_unicode_code_points_is_invalid_name - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_empty_name_is_invalid_name - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_whitespace_only_name_is_invalid_name[ ] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_whitespace_only_name_is_invalid_name[     ] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_whitespace_only_name_is_invalid_name[\t] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r04_name.py::test_r4_whitespace_only_name_is_invalid_name[\n \t ] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_earliest_start_is_accepted - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_latest_end_is_accepted - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_thirty_minute_booking_is_accepted - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_exactly_three_hours_is_accepted - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_three_hours_on_half_hours_is_accepted - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_three_hours_ending_at_closing_is_accepted - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_start_minutes_not_00_or_30_is_invalid_time[09:15-10:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_start_minutes_not_00_or_30_is_invalid_time[09:01-10:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_start_minutes_not_00_or_30_is_invalid_time[09:59-10:30] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_start_minutes_not_00_or_30_is_invalid_time[09:45-10:30] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_end_minutes_not_00_or_30_is_invalid_time[09:00-10:15] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_end_minutes_not_00_or_30_is_invalid_time[09:00-10:01] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_end_minutes_not_00_or_30_is_invalid_time[09:00-09:59] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_end_minutes_not_00_or_30_is_invalid_time[09:00-10:45] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_start_before_opening_is_invalid_time[07:30-08:30] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_start_before_opening_is_invalid_time[07:00-08:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_start_before_opening_is_invalid_time[00:00-01:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_end_after_closing_is_invalid_time[21:30-22:30] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_end_after_closing_is_invalid_time[21:00-23:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_end_after_closing_is_invalid_time[22:00-23:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_end_after_closing_is_invalid_time[23:00-23:30] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_end_at_2359_is_invalid_time - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_start_equal_to_end_is_invalid_time - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_start_after_end_is_invalid_time - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_three_and_a_half_hours_is_invalid_time - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r05_times.py::test_r5_much_longer_than_three_hours_is_invalid_time - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r06_room.py::test_r6_each_room_can_be_booked[1] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r06_room.py::test_r6_each_room_can_be_booked[2] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r06_room.py::test_r6_each_room_can_be_booked[3] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r06_room.py::test_r6_each_room_can_be_booked[4] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r06_room.py::test_r6_unknown_room_is_room_not_found[0] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r06_room.py::test_r6_unknown_room_is_room_not_found[5] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r06_room.py::test_r6_unknown_room_is_room_not_found[-1] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r06_room.py::test_r6_unknown_room_is_room_not_found[100] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r06_room.py::test_r6_room_id_beyond_sqlite_range_is_room_not_found - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r06_room.py::test_r6_large_negative_room_id_is_room_not_found - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_overlapping_booking_same_room_same_date_is_overlap[10:00-12:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_overlapping_booking_same_room_same_date_is_overlap[09:00-10:30] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_overlapping_booking_same_room_same_date_is_overlap[11:30-13:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_overlapping_booking_same_room_same_date_is_overlap[10:30-11:30] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_overlapping_booking_same_room_same_date_is_overlap[09:00-12:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_overlapping_booking_same_room_same_date_is_overlap[10:00-10:30] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_overlapping_booking_same_room_same_date_is_overlap[11:30-12:00] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_overlapping_booking_same_room_same_date_is_overlap[09:30-10:30] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_booking_ending_when_other_starts_is_allowed - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_booking_starting_when_other_ends_is_allowed - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_back_to_back_by_same_person_is_allowed - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_gap_filled_between_two_bookings_is_allowed - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_same_time_different_room_is_allowed - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_same_time_same_room_different_date_is_allowed - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_overlap_with_one_of_several_bookings_is_overlap - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_overlap_does_not_depend_on_name - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r07_overlap.py::test_r7_concurrent_identical_requests_create_one_booking - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_delete_returns_204_with_empty_body - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_deleted_booking_is_no_longer_listed - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_freed_time_can_be_booked_again - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_anyone_can_cancel_any_booking - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_deleting_twice_is_booking_not_found - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_unknown_id_is_booking_not_found - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_unknown_id_on_empty_database_is_booking_not_found - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_absent_non_positive_id_is_booking_not_found - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_absent_id_below_existing_ids_is_booking_not_found - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_id_beyond_sqlite_range_is_booking_not_found - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_non_integer_id_is_invalid_request[abc] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_non_integer_id_is_invalid_request[1.5] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_non_integer_id_is_invalid_request[1a] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_non_integer_id_is_invalid_request[one] - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_ids_are_not_reused_after_cancellation - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r08_cancel.py::test_r8_stale_cancel_does_not_remove_new_booking - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_get_bookings_error_body_has_exactly_error_and_message - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_get_bookings_room_not_found_body_shape - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_invalid_json_error_body_shape - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_missing_field_error_body_shape - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_wrong_type_error_body_shape - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_delete_invalid_id_error_body_shape - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_delete_unknown_id_error_body_shape - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_overlap_error_body_shape - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_series_of_failed_requests_changes_nothing - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_rejected_overlap_leaves_original_booking_unchanged - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r3_before_r4_missing_field_and_bad_name - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r3_before_r4_bad_date_and_long_name - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r3_before_r5_bad_time_format_and_bad_minutes - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r3_before_r6_bad_time_format_and_unknown_room - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r3_before_r6_bad_date_and_unknown_room - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r3_before_r7_wrong_name_type_and_overlap - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r3_before_r4_r5_r6 - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r4_before_r5 - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r4_before_r6 - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r4_before_r7 - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r4_before_r5_and_r6 - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r4_before_r5_and_r7 - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r5_before_r6 - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r5_before_r7 - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r5_before_r7_bad_minutes_inside_existing - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r09_errors.py::test_r9_r6_reported_for_unknown_room_with_otherwise_valid_request - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r10_application.py::test_r10_root_serves_index_html - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r10_application.py::test_r10_serves_app_js - ModuleNotFoundError: No module named 'app.main'
ERROR tests/acceptance/test_r10_application.py::test_r10_serves_styles_css - ModuleNotFoundError: No module named 'app.main'
9 failed, 241 errors in 1.73s
LEDGER.md:855: new blank line at EOF.
(.venv) garsande@Garg:~/Assignment-5$
```

## Disposition and risks

Recommended approval of Task 2 and F1 correction, and staged whitespace check. HTTP integration, strict JSON decoding, status mapping, persistence and concurrency through HTTP remain to be verified in Task 3. No daily limit until Part 8.

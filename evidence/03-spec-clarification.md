
# Part 3 - Specification Clarification Audit

## 1. Session information

- Date: 2026-11-27
- Tool: Claude Code
- Tool version: 2.1.332
- Model: Opus 5.5
- Agent: Main agent
- Prompt: prompts/03-clarify-spec.txt
- Reported analysis time: 56 seconds
- Questions identified: 17
- Frontend/specification conflicts identified: 1
- Clarification decisions approved: 8

## 2. Original Claude response

I read docs/spec.md and frontend/app.js and changed nothing. One question comes from a conflict between the page and the spec; the rest come from gaps in the spec.

Conflict between the page and the spec

Q1. Should the backend enforce a daily limit? (R9, section 6; also R4 and R7)
app.js:22 handles an error code daily_limit: "You already have 2 bookings on that day." The spec has no such rule. R9 says error must be one of the codes in section 6, and daily_limit isn't listed. Building it would also need answers the spec doesn't give:
- Who counts as "you": the trimmed booked_by, and is it case-sensitive?
- Does the limit apply per day across all rooms?
- Where does it fall in the R3–R7 error order?

Section 7 says a decision may not add a rejection, so this can't be settled as a D-decision. My reading is that you don't build it and record it under "Proposed, not built". Please confirm.

What counts as valid input

Q2. How strict is "room_id an integer" in the POST body? (R3)
Are any of these integers, or are they all invalid_request?
- true. Python treats a bool as an int.
- 1.0
- "1". FastAPI and Pydantic convert "1" to 1 by default.
- 1e0

Q3. What counts as an integer for room_id in GET /api/bookings? (R2)
Query values are always strings. For each of these, is the answer 422 invalid_request or a lookup that gives 404 room_not_found?
- 01, +1, -1,  1, 1.0
- an empty room_id=. Is that "not an integer" (422), or the same as leaving it out (all rooms)?

Q4. The same question for DELETE /api/bookings/{id}. (R8)
Should -1, 007, +5 or a 30-digit number give 404 booking_not_found or 422 invalid_request? An integer bigger than SQLite can store would make the database lookup fail. The same applies to a very large room_id (R6).

Q5. Do "four digits" and "two digits" mean only the ASCII digits 0–9? (R2, R3)
Python's \d and int() also accept digits from other scripts, such as ٢٠٣١-٠٣-١٤.

Q6. Which years count as "a real calendar day"? (R2, R3)
0000-01-01 matches the format, but Python's date type can't represent year 0. Is it invalid_request?

Q7. Are these JSON edge cases valid? (R3)
- NaN and Infinity, which Python's JSON parser accepts but standard JSON doesn't.
- An object with the same key twice: is it rejected, or does the last value win?
- A body sent without a Content-Type: application/json header: is it still parsed?

Q8. Is date required to be a single value? (R2)
What happens with ?date= (empty), or with date given twice (?date=a&date=b)?

The name (R4)

Q9. How is "1 to 40 characters" counted? (R4)
By Unicode code points (Python len), by UTF-16 units (JavaScript .length, which counts an emoji as 2), or by visible characters?

Q10. Which whitespace is trimmed? (R4)
Python's str.strip() and JavaScript's trim() disagree on some characters, such as \u0085 and \u180e, and neither removes the zero-width space \u200b. Are newlines, tabs or control characters allowed inside a name?

Error order and error format

Q11. In GET /api/bookings, which error wins when both parameters are bad? (R2, R9)
R9 sets an order only for POST. For example, ?date=bad&room_id=99 could give 422 invalid_request or 404 room_not_found.

Q12. What do requests outside section 4 return? (R9)
R9 covers only "the endpoints in section 4". It doesn't say what PUT /api/bookings/1, GET /api/bookings/5, /api/bookings/ with a trailing slash, or an unknown /api/... path should return. Should they use the {error, message} shape? If so, with which code, since none in section 6 fits a 404 or 405?

Q13. What should message say for invalid_request? (R9)
The spec says message is any text and isn't tested. But app.js:62-63 shows the backend's message to the user after "The request was not valid.", so the wording will appear on the page. Is there a required style, or should it name the field at fault?

Bookings and storage

Q14. May the id of a cancelled booking be reused? (section 2, R8)
The spec only promises that "no two current bookings share an id". SQLite without AUTOINCREMENT can hand out a deleted id again. A cancel button on a page that hasn't been refreshed would then delete someone else's booking instead of getting booking_not_found.

Q15. Must two bookings sent at the same moment be checked one after the other? (R7, R9)
With a separate connection per request, two overlapping POSTs could both pass the overlap check unless the check and the insert run as one transaction. Is "never two overlapping bookings, even under concurrency" required?

Q16. Which frontend/ folder does the backend serve? (section 3, R10)
Is the path relative to the current working directory or to the repository? Is GET /index.html also served? What should happen if the file is missing?

Q17. What if the database file already has some rooms, but not all four? (section 3, R10)
"Adds the four rooms if the file has no rooms yet" doesn't cover a file with, say, two rooms. Should the backend leave it alone, fill in the missing rooms, or report an error?

Q1 matters most: it's the only place where the page and the spec actually conflict. Q2–Q4 and Q14 are the gaps most likely to make tests or real use go wrong, because FastAPI's defaults (converting "1" to 1, accepting true as a number) and SQLite's id reuse each pick an answer silently if nobody decides.

Crunched for 56s · done 1:55 AM

recap: You're getting the RoomBook backend spec clear before any code is written, and I've listed 17 open questions (Q1–Q17), led by the page's daily_limit error that the spec doesn't define. Next, you decide on Q1, ideally recording it as "Proposed, not built", and answer the rest. (turn off recaps in /config)


## 3. Human review and decision log

I reviewed the 17 questions identified during the specification
clarification exercise. I selected eight decisions that address
important implementation ambiguities without introducing new
business requirements or changing the existing API contract.

The daily booking limit was deferred because it is not part of
Version 1 of the specification.

| Question | Rule | Topic | Disposition | Reason | Decision |
|---|---|---|---|---|---|
| Q1 | R4, R7, R9 | Daily booking limit | Deferred | Not defined in Version 1; would introduce a new rejection condition and error code. | Proposed, not built |
| Q2 | R3 | Strict JSON integer validation | Accepted | Prevents implicit conversion of booleans, strings and floating-point values into integer room identifiers. | D1 |
| Q3 | R2 | Query parameter integer syntax | Not selected | No additional integer syntax policy was approved during this clarification. | None |
| Q4 | R2, R6, R8 | Large integer identifiers | Partially accepted | Prevents SQLite overflow while preserving existing not-found errors. Exact textual integer syntax remains unspecified. | D2 |
| Q5 | R2, R3 | ASCII versus Unicode digits | Not selected | No additional digit-encoding restriction was approved. | None |
| Q6 | R2, R3 | Calendar year zero | Existing rule | The specification already requires a real calendar day. | None |
| Q7 | R3 | JSON edge cases | Not selected | Duplicate keys and Content-Type handling were not formally decided. Invalid JSON remains governed by R3. | None |
| Q8 | R2 | Empty and duplicate date parameters | Partially covered | Empty dates violate R2. Duplicate parameter handling remains unspecified. | None |
| Q9 | R4 | Character counting | Accepted | Python len() provides a consistent Unicode code-point counting method. | D3 |
| Q10 | R4 | Whitespace handling | Accepted | Python str.strip() provides consistent trimming while preserving internal whitespace and capitalization. | D3 |
| Q11 | R2, R9 | GET validation precedence | Accepted | Provides deterministic error handling when both query parameters are invalid. | D4 |
| Q12 | R9 | Undefined endpoints | Accepted | Avoids adding unsupported endpoints or error codes. | D8 |
| Q13 | R9 | Error message wording | Existing rule | R9 already permits any short, helpful error message. | None |
| Q14 | R8 | Booking identifier reuse | Accepted | Prevents stale cancellation requests from deleting unrelated bookings. | D5 |
| Q15 | R7, R9 | Concurrent bookings | Accepted | Prevents concurrent requests from creating overlapping bookings. | D6 |
| Q16 | R10 | Frontend file location | Partially accepted | Repository-relative paths avoid dependence on the working directory. Additional static routes and missing-file behavior were not specified. | D7 |
| Q17 | R10 | Partially initialized database | Not selected | Recovery behavior for inconsistent database files was not formally decided. | None |

## 4. Approved decisions

The following decisions were approved for section 7 of
docs/spec.md:

- D1: Strict JSON integer validation.
- D2: Safe handling of large integer identifiers.
- D3: Consistent name trimming and character counting.
- D4: Deterministic GET parameter validation order.
- D5: No reuse of cancelled booking identifiers.
- D6: Atomic and serialized overlap checking and insertion.
- D7: Repository-relative frontend file resolution.
- D8: Default FastAPI handling for undefined API endpoints.

These decisions clarify implementation behavior without adding
a new endpoint, field, error code, or business rejection rule.

## 5. Deferred requirement

### Q1 - Daily booking limit

The frontend contains a daily_limit error message indicating
that a person may have a maximum of two bookings per day.

However, this requirement does not exist in Version 1 of
docs/spec.md or its error-code table.

Implementing it now would violate the current specification
by rejecting requests that are otherwise valid.

The requirement is therefore recorded under "Proposed, not
built" in section 7 and will be addressed only after a formal
specification change.


## 6. Verification

Claude reported that it read docs/spec.md and frontend/app.js
without changing any files.

After reviewing Claude's 17 questions, I approved eight
clarification decisions and manually updated section 7
of the specification.

### Verification commands and results

1. git status --short

   M LEDGER.md
   M docs/spec.md
   ?? evidence/03-spec-clarification.md
   ?? prompts/03-clarify-spec.txt

   Result: Only the expected Part 3 files were changed
   or created.

2. git diff -- docs/spec.md

   Result: Eight approved decisions were added to section 7.
   The daily booking limit was recorded under "Proposed,
   not built". Existing requirements and product owner
   decisions were preserved. An additional blank line
   was added before section 7.

3. git diff -- app/ frontend/ tests/

   Result: No output. No tracked changes were detected
   in the backend, frontend or test directories.

4. python3 tools/check.py setup

   [ OK ] Python 3.12.3 (3.11 or later needed)
   [ OK ] fastapi 0.165.0 installed (requirements.txt pins 0.165.0)
   [ OK ] uvicorn 0.54.0 installed (requirements.txt pins 0.54.0)
   [ OK ] httpx 0.28.1 installed (requirements.txt pins 0.28.1)
   [ OK ] pytest 9.2.0 installed (requirements.txt pins 9.2.0)
   [ OK ] inside a git repository
   [ OK ] origin is git@github.com:garsande/cs690_assignment5.git
   [ OK ] frontend/index.html present
   [ OK ] frontend/app.js present
   [ OK ] docs/spec.md present
   [ OK ] tests/conftest.py present

   All checks passed.

5. git diff --check

   Result: No output. No whitespace errors were detected
   in the tracked changes.

### Verification conclusion

The specification clarification is complete. The approved
decisions preserve the existing API contract and do not
introduce additional business rejection rules.

The environment setup checks passed. Backend behavior and
acceptance tests have not yet been implemented or verified.



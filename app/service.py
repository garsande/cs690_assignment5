"""The section 5 booking rules for RoomBook. No HTTP code and no SQL.

Every rule failure is raised as RuleViolation(code, message), using only the
codes in section 6. The HTTP layer maps each code to its status.
"""

from __future__ import annotations

import datetime
import re
import unicodedata

from . import repository
from .models import NewBooking

# Section 6 error codes.
INVALID_REQUEST = "invalid_request"
INVALID_NAME = "invalid_name"
INVALID_TIME = "invalid_time"
ROOM_NOT_FOUND = "room_not_found"
BOOKING_NOT_FOUND = "booking_not_found"
OVERLAP = "overlap"

_REQUIRED_FIELDS = ("room_id", "date", "start", "end", "booked_by")

# ASCII digits only: "\d" would also match other Unicode decimal digits.
_DATE_SHAPE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_TIME_SHAPE = re.compile(r"[0-9]{2}:[0-9]{2}")

# The shape of int()'s base-10 grammar (IC2 step 2): whitespace, sign, digit groups
# split by single underscores, whitespace. Unicode \s and \d are wider than or equal to
# what int() accepts (for example \s matches U+001C..U+001F, which int() rejects), so
# parse_textual_int asks int() itself to confirm the whitespace and digit characters.
_INT_GRAMMAR = re.compile(r"(\s*)([+-]?)(\d+(?:_\d+)*)(\s*)")

_OPEN = 8 * 60
_CLOSE = 22 * 60
_MAX_MINUTES = 180


class RuleViolation(Exception):
    """A request broke a section 5 rule."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class _Marker:
    def __init__(self, name: str) -> None:
        self._name = name

    def __repr__(self) -> str:
        return self._name


# Results of parse_textual_int besides a plain int.
OUT_OF_RANGE = _Marker("OUT_OF_RANGE")
INVALID = _Marker("INVALID")


def parse_textual_int(text: str) -> int | _Marker:
    """Parse a textual id with int() semantics (IC1), working past int()'s length limit (IC2).

    Returns the int, OUT_OF_RANGE for an integer of 10**19 or more in magnitude, or
    INVALID when the text is not an integer.
    """
    try:
        return int(text)
    except ValueError:
        pass
    # int() refused the text. Fall back only when the refusal is int()'s length limit.
    match = _INT_GRAMMAR.fullmatch(text)
    if match is None:
        return INVALID
    lead, sign, body, trail = match.groups()
    digits = body.replace("_", "")
    # Let int() itself judge every whitespace and digit character, on a probe short
    # enough to stay under the length limit (each distinct character once). If int()
    # rejects the probe, it rejects the original text for that same reason.
    probe = (
        "".join(dict.fromkeys(lead))
        + sign
        + "".join(dict.fromkeys(digits))
        + "".join(dict.fromkeys(trail))
    )
    try:
        int(probe)
    except ValueError:
        return INVALID
    negative = sign == "-"
    digits = "".join(str(unicodedata.decimal(ch)) for ch in digits).lstrip("0")
    if len(digits) > 19:
        return OUT_OF_RANGE
    value = int(digits) if digits else 0
    return -value if negative else value


def _is_valid_date(value: str) -> bool:
    """R2: exactly YYYY-MM-DD and a real calendar day."""
    if not _DATE_SHAPE.fullmatch(value):
        return False
    try:
        datetime.date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
    except ValueError:
        return False
    return True


def _is_valid_time(value: str) -> bool:
    """R3: exactly HH:MM, from 00:00 to 23:59."""
    if not _TIME_SHAPE.fullmatch(value):
        return False
    return int(value[0:2]) <= 23 and int(value[3:5]) <= 59


def _minutes(value: str) -> int:
    return int(value[0:2]) * 60 + int(value[3:5])


class BookingService:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def list_rooms(self) -> list[dict]:
        """R1."""
        return repository.list_rooms(self.db_path)

    def list_bookings(self, date_raw: str | None, room_id_raw: str | None) -> list[dict]:
        """R2. The date is checked before room_id (D4)."""
        if date_raw is None or not _is_valid_date(date_raw):
            raise RuleViolation(INVALID_REQUEST, "date must be a real day as YYYY-MM-DD.")
        if room_id_raw is None:
            return repository.list_bookings(self.db_path, date_raw)
        room_id = parse_textual_int(room_id_raw)
        if room_id is INVALID:
            raise RuleViolation(INVALID_REQUEST, "room_id must be an integer.")
        if room_id is OUT_OF_RANGE or not repository.room_exists(self.db_path, room_id):
            raise RuleViolation(ROOM_NOT_FOUND, "That room does not exist.")
        return repository.list_bookings(self.db_path, date_raw, room_id)

    def create_booking(self, payload: object) -> dict:
        """R3 to R7, reported in that order (R9)."""
        booking = self._check_request(payload)
        if not repository.room_exists(self.db_path, booking.room_id):
            raise RuleViolation(ROOM_NOT_FOUND, "That room does not exist.")
        created = repository.insert_booking_if_free(
            self.db_path,
            booking.room_id,
            booking.date,
            booking.start,
            booking.end,
            booking.booked_by,
        )
        if created is None:
            raise RuleViolation(OVERLAP, "That room is already booked at that time.")
        return created

    def cancel_booking(self, id_raw: str) -> None:
        """R8."""
        booking_id = parse_textual_int(id_raw)
        if booking_id is INVALID:
            raise RuleViolation(INVALID_REQUEST, "The booking id must be an integer.")
        if booking_id is OUT_OF_RANGE or not repository.delete_booking(self.db_path, booking_id):
            raise RuleViolation(BOOKING_NOT_FOUND, "No booking has that id.")

    @staticmethod
    def _check_request(payload: object) -> NewBooking:
        """R3, R4 and R5, in that order. Fields not listed in R3 are ignored."""
        # R3: request shape.
        if not isinstance(payload, dict) or any(f not in payload for f in _REQUIRED_FIELDS):
            raise RuleViolation(
                INVALID_REQUEST,
                "The body must be a JSON object with room_id, date, start, end and booked_by.",
            )
        room_id = payload["room_id"]
        date = payload["date"]
        start = payload["start"]
        end = payload["end"]
        booked_by = payload["booked_by"]
        if type(room_id) is not int:  # D1: no bool, float or string.
            raise RuleViolation(INVALID_REQUEST, "room_id must be an integer.")
        if not all(isinstance(v, str) for v in (date, start, end, booked_by)):
            raise RuleViolation(
                INVALID_REQUEST, "date, start, end and booked_by must be strings."
            )
        if not _is_valid_date(date):
            raise RuleViolation(INVALID_REQUEST, "date must be a real day as YYYY-MM-DD.")
        if not (_is_valid_time(start) and _is_valid_time(end)):
            raise RuleViolation(INVALID_REQUEST, "start and end must be times as HH:MM.")

        # R4: name (D3).
        name = booked_by.strip()
        if not 1 <= len(name) <= 40:
            raise RuleViolation(INVALID_NAME, "The name must be 1 to 40 characters.")

        # R5: times.
        start_min = _minutes(start)
        end_min = _minutes(end)
        if (
            start_min % 60 not in (0, 30)
            or end_min % 60 not in (0, 30)
            or start_min < _OPEN
            or end_min > _CLOSE
            or start_min >= end_min
            or end_min - start_min > _MAX_MINUTES
        ):
            raise RuleViolation(
                INVALID_TIME,
                "Bookings use :00 or :30, run 08:00 to 22:00, and last up to 3 hours.",
            )

        return NewBooking(room_id=room_id, date=date, start=start, end=end, booked_by=name)

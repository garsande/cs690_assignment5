"""Shared helpers for RoomBook acceptance tests. Expected values come from docs/spec.md."""

import datetime
import re

DATE = "2031-03-14"
OTHER_DATE = "2031-03-15"

# Reference booking created by the error helpers when the database is empty, so that
# an error test can detect a booking being changed or removed, not only created (R9).
SEED = {
    "room_id": 4,
    "date": OTHER_DATE,
    "start": "20:00",
    "end": "21:00",
    "booked_by": "Seed Booking",
}

BOOKING_FIELDS = {"id", "room_id", "date", "start", "end", "booked_by"}
ROOM_FIELDS = {"id", "name", "capacity"}

ROOMS = [
    {"id": 1, "name": "Quiet Room A", "capacity": 2},
    {"id": 2, "name": "Quiet Room B", "capacity": 2},
    {"id": 3, "name": "Group Room C", "capacity": 6},
    {"id": 4, "name": "Group Room D", "capacity": 8},
]

_DATE_SHAPE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def body(**overrides):
    """A valid POST /api/bookings body (spec section 4), with optional overrides."""
    data = {
        "room_id": 1,
        "date": DATE,
        "start": "09:00",
        "end": "10:30",
        "booked_by": "Ana",
    }
    data.update(overrides)
    return data


def without(field):
    data = body()
    del data[field]
    return data


def book(client, **overrides):
    """Create a booking that must succeed; return the booking object."""
    r = client.post("/api/bookings", json=body(**overrides))
    assert r.status_code == 201, r.text
    return r.json()


def list_bookings(client, date=DATE, room_id=None):
    params = {"date": date}
    if room_id is not None:
        params["room_id"] = room_id
    r = client.get("/api/bookings", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def is_valid_date(value):
    """True when value is a date that R2 accepts, so it can be used in a snapshot."""
    if not isinstance(value, str) or not _DATE_SHAPE.fullmatch(value):
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _dates(extra=()):
    dates = [DATE, OTHER_DATE]
    for d in extra:
        if is_valid_date(d) and d not in dates:
            dates.append(d)
    return tuple(dates)


def snapshot(client, dates=()):
    """All stored bookings on DATE, OTHER_DATE and any extra valid dates given."""
    return {d: list_bookings(client, d) for d in _dates(dates)}


def existing_ids(client, dates=()):
    return {b["id"] for items in snapshot(client, dates).values() for b in items}


def absent_id_above(client, dates=()):
    """An id that no current booking has: larger than every existing id."""
    ids = existing_ids(client, dates)
    return max(ids) + 1 if ids else 1


def absent_non_positive_id(client, dates=()):
    """A zero or negative id that no current booking has (ids need not be positive)."""
    ids = existing_ids(client, dates)
    candidate = 0
    while candidate in ids:
        candidate -= 1
    return candidate


def ensure_seed(client, dates=()):
    """If the snapshotted dates hold no bookings, create the SEED booking."""
    if not any(snapshot(client, dates).values()):
        r = client.post("/api/bookings", json=dict(SEED))
        assert r.status_code == 201, r.text


def assert_error(response, status, code):
    """R9: status, error code, and a body with exactly `error` and `message`."""
    assert response.status_code == status, response.text
    data = response.json()
    assert isinstance(data, dict)
    assert set(data.keys()) == {"error", "message"}
    assert data["error"] == code
    assert isinstance(data["message"], str)


def _payload_dates(payload, dates):
    extra = list(dates)
    if isinstance(payload, dict):
        extra.append(payload.get("date"))
    return extra


def assert_post_error(client, payload, status, code, dates=()):
    """POST a JSON payload that must fail; check the R9 error and unchanged state."""
    dates = _payload_dates(payload, dates)
    ensure_seed(client, dates)
    before = snapshot(client, dates)
    r = client.post("/api/bookings", json=payload)
    assert_error(r, status, code)
    assert snapshot(client, dates) == before


def assert_raw_post_error(client, content, status, code, dates=()):
    """POST raw bytes as application/json that must fail; check R9 and unchanged state."""
    ensure_seed(client, dates)
    before = snapshot(client, dates)
    r = client.post(
        "/api/bookings", content=content, headers={"Content-Type": "application/json"}
    )
    assert_error(r, status, code)
    assert snapshot(client, dates) == before


def assert_get_error(client, params, status, code, dates=()):
    """GET /api/bookings that must fail; check R9 and unchanged state."""
    dates = list(dates) + [params.get("date")]
    ensure_seed(client, dates)
    before = snapshot(client, dates)
    r = client.get("/api/bookings", params=params)
    assert_error(r, status, code)
    assert snapshot(client, dates) == before


def assert_delete_error(client, booking_id, status, code, dates=()):
    """DELETE /api/bookings/{id} that must fail; check R9 and unchanged state."""
    ensure_seed(client, dates)
    before = snapshot(client, dates)
    r = client.delete(f"/api/bookings/{booking_id}")
    assert_error(r, status, code)
    assert snapshot(client, dates) == before

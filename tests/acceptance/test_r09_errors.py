"""R9. Errors: body shape, no side effects, and rule order for POST."""

from _rb_helpers import (
    DATE,
    OTHER_DATE,
    absent_id_above,
    assert_delete_error,
    assert_error,
    assert_get_error,
    assert_post_error,
    assert_raw_post_error,
    body,
    book,
    list_bookings,
    snapshot,
    without,
)


# --- Error body shape on every endpoint, with unchanged state -------------------

def test_r9_get_bookings_error_body_has_exactly_error_and_message(client):
    book(client)
    assert_get_error(client, {"date": "nope"}, 422, "invalid_request")


def test_r9_get_bookings_room_not_found_body_shape(client):
    book(client)
    assert_get_error(client, {"date": DATE, "room_id": 9}, 404, "room_not_found")


def test_r9_invalid_json_error_body_shape(client):
    book(client)
    assert_raw_post_error(client, b"not json", 422, "invalid_request")


def test_r9_missing_field_error_body_shape(client):
    book(client, room_id=2)
    assert_post_error(client, without("booked_by"), 422, "invalid_request")


def test_r9_wrong_type_error_body_shape(client):
    book(client, room_id=2)
    assert_post_error(client, body(room_id="two"), 422, "invalid_request")


def test_r9_delete_invalid_id_error_body_shape(client):
    book(client)
    assert_delete_error(client, "xyz", 422, "invalid_request")


def test_r9_delete_unknown_id_error_body_shape(client):
    book(client)
    assert_delete_error(client, absent_id_above(client), 404, "booking_not_found")


def test_r9_overlap_error_body_shape(client):
    book(client)
    assert_post_error(client, body(), 409, "overlap")


# --- A failed request changes nothing -------------------------------------------

def test_r9_series_of_failed_requests_changes_nothing(client):
    a = book(client, room_id=1, start="09:00", end="10:00")
    b = book(client, room_id=3, start="15:00", end="16:00")
    c = book(client, room_id=2, date=OTHER_DATE, start="12:00", end="13:00")
    before = snapshot(client)
    assert before == {DATE: [a, b], OTHER_DATE: [c]}
    missing = absent_id_above(client)

    assert_error(client.post("/api/bookings", json=without("room_id")), 422, "invalid_request")
    assert snapshot(client) == before
    assert_error(client.post("/api/bookings", json=body(booked_by=" ")), 422, "invalid_name")
    assert snapshot(client) == before
    assert_error(
        client.post("/api/bookings", json=body(start="07:00", end="08:00")), 422, "invalid_time"
    )
    assert snapshot(client) == before
    assert_error(client.post("/api/bookings", json=body(room_id=7)), 404, "room_not_found")
    assert snapshot(client) == before
    assert_error(
        client.post("/api/bookings", json=body(room_id=1, start="09:30", end="10:30")),
        409,
        "overlap",
    )
    assert snapshot(client) == before
    assert_error(client.delete("/api/bookings/abc"), 422, "invalid_request")
    assert snapshot(client) == before
    assert_error(client.delete(f"/api/bookings/{missing}"), 404, "booking_not_found")
    assert snapshot(client) == before
    assert_error(client.get("/api/bookings", params={"date": "2031-02-30"}), 422, "invalid_request")
    assert snapshot(client) == before
    assert_error(
        client.get("/api/bookings", params={"date": DATE, "room_id": 6}), 404, "room_not_found"
    )
    assert snapshot(client) == before

    assert list_bookings(client, DATE) == [a, b]
    assert list_bookings(client, OTHER_DATE) == [c]


def test_r9_rejected_overlap_leaves_original_booking_unchanged(client):
    a = book(client, room_id=2, start="10:00", end="11:00", booked_by="Ana")
    assert_post_error(
        client, body(room_id=2, start="10:00", end="11:00", booked_by="Ben"), 409, "overlap"
    )
    assert list_bookings(client) == [a]


# --- Order of rules for POST: R3, R4, R5, R6, R7 ---------------------------------
# Each test name lists only rules that its input really breaks.

def test_r9_r3_before_r4_missing_field_and_bad_name(client):
    # R3: date missing. R4: empty name.
    payload = without("date")
    payload["booked_by"] = ""
    assert_post_error(client, payload, 422, "invalid_request")


def test_r9_r3_before_r4_bad_date_and_long_name(client):
    # R3: impossible calendar date. R4: 41 characters.
    assert_post_error(client, body(date="2031-02-30", booked_by="n" * 41), 422, "invalid_request")


def test_r9_r3_before_r5_bad_time_format_and_bad_minutes(client):
    # R3: start "9:00" badly formatted. R5: end minutes are 15.
    assert_post_error(client, body(start="9:00", end="10:15"), 422, "invalid_request")


def test_r9_r3_before_r6_bad_time_format_and_unknown_room(client):
    # R3: end "10:3" badly formatted. R6: room 99 does not exist.
    assert_post_error(client, body(room_id=99, end="10:3"), 422, "invalid_request")


def test_r9_r3_before_r6_bad_date_and_unknown_room(client):
    # R3: date uses slashes. R6: room 99 does not exist.
    assert_post_error(client, body(room_id=99, date="2031/03/14"), 422, "invalid_request")


def test_r9_r3_before_r7_wrong_name_type_and_overlap(client):
    # R3: booked_by is not a string. R7: same room, date and times as an existing booking.
    book(client, room_id=1, start="09:00", end="10:30")
    assert_post_error(
        client, body(room_id=1, start="09:00", end="10:30", booked_by=123), 422, "invalid_request"
    )


def test_r9_r3_before_r4_r5_r6(client):
    # R3: date "2031-3-14" badly formatted. R4: empty name.
    # R5: start minutes are 15 and start is before 08:00. R6: room 99 does not exist.
    payload = {"room_id": 99, "date": "2031-3-14", "start": "07:15", "end": "09:30", "booked_by": ""}
    assert_post_error(client, payload, 422, "invalid_request")


def test_r9_r4_before_r5(client):
    # R4: whitespace-only name. R5: start before 08:00 and longer than 3 hours.
    assert_post_error(client, body(booked_by="   ", start="07:00", end="12:00"), 422, "invalid_name")


def test_r9_r4_before_r6(client):
    # R4: empty name. R6: room 42 does not exist.
    assert_post_error(client, body(booked_by="", room_id=42), 422, "invalid_name")


def test_r9_r4_before_r7(client):
    # R4: 41 characters. R7: same room, date and times as an existing booking.
    book(client, room_id=1, start="09:00", end="10:30")
    assert_post_error(client, body(room_id=1, booked_by="q" * 41), 422, "invalid_name")


def test_r9_r4_before_r5_and_r6(client):
    # R4: empty name. R5: minutes are 15 and 45. R6: room 8 does not exist.
    assert_post_error(
        client, body(room_id=8, booked_by="", start="09:15", end="09:45"), 422, "invalid_name"
    )


def test_r9_r4_before_r5_and_r7(client):
    # R4: empty name. R5: end minutes are 15.
    # R7: 09:00-10:15 overlaps the existing 09:00-10:00 booking in the same room and date.
    book(client, room_id=1, start="09:00", end="10:00")
    assert_post_error(
        client, body(room_id=1, booked_by="", start="09:00", end="10:15"), 422, "invalid_name"
    )


def test_r9_r5_before_r6(client):
    # R5: start after end. R6: room 5 does not exist.
    assert_post_error(client, body(room_id=5, start="10:00", end="09:00"), 422, "invalid_time")


def test_r9_r5_before_r7(client):
    # R5: 210 minutes. R7: overlaps the existing 09:00-12:00 booking.
    book(client, room_id=1, start="09:00", end="12:00")
    assert_post_error(client, body(room_id=1, start="09:00", end="12:30"), 422, "invalid_time")


def test_r9_r5_before_r7_bad_minutes_inside_existing(client):
    # R5: start minutes are 15. R7: lies inside the existing 09:00-12:00 booking.
    book(client, room_id=1, start="09:00", end="12:00")
    assert_post_error(client, body(room_id=1, start="10:15", end="11:00"), 422, "invalid_time")


def test_r9_r6_reported_for_unknown_room_with_otherwise_valid_request(client):
    # Only R6 is broken: room 0 does not exist. (R6 and R7 cannot both be broken,
    # since an overlap needs an existing room.)
    book(client, room_id=1, start="09:00", end="10:30")
    assert_post_error(client, body(room_id=0), 404, "room_not_found")

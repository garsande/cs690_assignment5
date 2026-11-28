"""R8. Cancel."""

import pytest

from _rb_helpers import (
    DATE,
    OTHER_DATE,
    absent_id_above,
    absent_non_positive_id,
    assert_delete_error,
    assert_error,
    body,
    book,
    existing_ids,
    list_bookings,
    snapshot,
)


def test_r8_delete_returns_204_with_empty_body(client):
    b = book(client)
    r = client.delete(f"/api/bookings/{b['id']}")
    assert r.status_code == 204
    assert r.content == b""


def test_r8_deleted_booking_is_no_longer_listed(client):
    a = book(client, room_id=1)
    b = book(client, room_id=2)
    assert client.delete(f"/api/bookings/{a['id']}").status_code == 204
    assert list_bookings(client) == [b]


def test_r8_freed_time_can_be_booked_again(client):
    a = book(client, room_id=1, start="10:00", end="12:00")
    assert client.delete(f"/api/bookings/{a['id']}").status_code == 204
    r = client.post("/api/bookings", json=body(room_id=1, start="10:00", end="12:00", booked_by="Ben"))
    assert r.status_code == 201
    assert r.json()["booked_by"] == "Ben"


def test_r8_anyone_can_cancel_any_booking(client):
    # P3: no login, delete needs only the id.
    b = book(client, booked_by="Someone Else")
    assert client.delete(f"/api/bookings/{b['id']}").status_code == 204


def test_r8_deleting_twice_is_booking_not_found(client):
    a = book(client, room_id=1)
    keep = book(client, room_id=2)
    assert client.delete(f"/api/bookings/{a['id']}").status_code == 204
    assert a["id"] not in existing_ids(client)
    assert_delete_error(client, a["id"], 404, "booking_not_found")
    assert list_bookings(client) == [keep]


def test_r8_unknown_id_is_booking_not_found(client):
    b = book(client)
    missing = absent_id_above(client)
    assert_delete_error(client, missing, 404, "booking_not_found")
    assert list_bookings(client) == [b]


def test_r8_unknown_id_on_empty_database_is_booking_not_found(client):
    # No booking has ever been created here, so no booking has id 1.
    r = client.delete("/api/bookings/1")
    assert_error(r, 404, "booking_not_found")
    assert snapshot(client) == {DATE: [], OTHER_DATE: []}


def test_r8_absent_non_positive_id_is_booking_not_found(client):
    # Ids are not required to be positive, so pick a zero or negative id that
    # no current booking has.
    b = book(client)
    missing = absent_non_positive_id(client)
    assert_delete_error(client, missing, 404, "booking_not_found")
    assert list_bookings(client) == [b]


def test_r8_absent_id_below_existing_ids_is_booking_not_found(client):
    a = book(client, room_id=1)
    b = book(client, room_id=2)
    missing = min(existing_ids(client)) - 1
    assert_delete_error(client, missing, 404, "booking_not_found")
    assert list_bookings(client) == [a, b]


def test_r8_id_beyond_sqlite_range_is_booking_not_found(client):
    # D2: a valid integer outside SQLite's range is a nonexistent id.
    b = book(client)
    huge = 2**70
    assert huge not in existing_ids(client)
    assert_delete_error(client, huge, 404, "booking_not_found")
    assert list_bookings(client) == [b]


@pytest.mark.parametrize("bad_id", ["abc", "1.5", "1a", "one"])
def test_r8_non_integer_id_is_invalid_request(client, bad_id):
    b = book(client)
    assert_delete_error(client, bad_id, 422, "invalid_request")
    assert list_bookings(client) == [b]


def test_r8_ids_are_not_reused_after_cancellation(client):
    # D5.
    a = book(client, room_id=1)
    assert client.delete(f"/api/bookings/{a['id']}").status_code == 204
    b = book(client, room_id=1)
    assert b["id"] != a["id"]


def test_r8_stale_cancel_does_not_remove_new_booking(client):
    # D5: a repeated cancel of an old id must not delete a later booking.
    a = book(client, room_id=1)
    assert client.delete(f"/api/bookings/{a['id']}").status_code == 204
    b = book(client, room_id=1)
    assert_delete_error(client, a["id"], 404, "booking_not_found")
    assert list_bookings(client, DATE) == [b]

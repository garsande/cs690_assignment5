"""R3. Request shape of POST /api/bookings."""

import pytest

from _rb_helpers import (
    BOOKING_FIELDS,
    DATE,
    assert_post_error,
    assert_raw_post_error,
    body,
    book,
    without,
)


def test_r3_valid_request_creates_booking(client):
    r = client.post("/api/bookings", json=body())
    assert r.status_code == 201
    data = r.json()
    assert set(data.keys()) == BOOKING_FIELDS
    assert isinstance(data["id"], int) and not isinstance(data["id"], bool)
    assert data["room_id"] == 1
    assert data["date"] == DATE
    assert data["start"] == "09:00"
    assert data["end"] == "10:30"
    assert data["booked_by"] == "Ana"


def test_r3_created_booking_is_listed(client):
    created = client.post("/api/bookings", json=body()).json()
    r = client.get("/api/bookings", params={"date": DATE})
    assert r.json() == [created]


def test_r3_extra_fields_are_ignored(client):
    payload = body(colour="blue", people=4, notes=None)
    r = client.post("/api/bookings", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert set(data.keys()) == BOOKING_FIELDS
    assert data["booked_by"] == "Ana"
    assert data["room_id"] == 1


def test_r3_client_supplied_id_is_ignored(client):
    first = book(client, room_id=1, start="09:00", end="10:00", booked_by="First")
    payload = body(room_id=2, start="11:00", end="12:00", booked_by="Second", id=first["id"])
    r = client.post("/api/bookings", json=payload)
    assert r.status_code == 201, r.text
    second = r.json()
    assert set(second.keys()) == BOOKING_FIELDS
    assert second["id"] != first["id"]
    assert second["room_id"] == 2
    assert second["start"] == "11:00"
    assert second["end"] == "12:00"
    assert second["booked_by"] == "Second"
    listed = client.get("/api/bookings", params={"date": DATE}).json()
    assert listed == [first, second]


def test_r3_past_date_is_allowed(client):
    # P1: the backend never compares a date with today.
    r = client.post("/api/bookings", json=body(date="1999-01-04"))
    assert r.status_code == 201
    assert r.json()["date"] == "1999-01-04"


def test_r3_leap_day_is_accepted(client):
    r = client.post("/api/bookings", json=body(date="2032-02-29"))
    assert r.status_code == 201


def test_r3_invalid_json_is_invalid_request(client):
    assert_raw_post_error(client, b'{"room_id": 1, "date": ', 422, "invalid_request")


def test_r3_empty_body_is_invalid_request(client):
    assert_raw_post_error(client, b"", 422, "invalid_request")


@pytest.mark.parametrize("payload", [[], [body()], "text", 42, True])
def test_r3_body_not_an_object_is_invalid_request(client, payload):
    assert_post_error(client, payload, 422, "invalid_request")


@pytest.mark.parametrize("field", ["room_id", "date", "start", "end", "booked_by"])
def test_r3_missing_field_is_invalid_request(client, field):
    assert_post_error(client, without(field), 422, "invalid_request")


def test_r3_empty_object_is_invalid_request(client):
    assert_post_error(client, {}, 422, "invalid_request")


@pytest.mark.parametrize("value", ["1", 1.0, 1.5, True, False, None, [1], {"id": 1}])
def test_r3_room_id_wrong_type_is_invalid_request(client, value):
    # D1: booleans, numeric strings and floats are not integers.
    assert_post_error(client, body(room_id=value), 422, "invalid_request")


@pytest.mark.parametrize("field", ["date", "start", "end", "booked_by"])
@pytest.mark.parametrize("value", [123, None, True, ["x"], {"a": 1}])
def test_r3_string_field_wrong_type_is_invalid_request(client, field, value):
    assert_post_error(client, body(**{field: value}), 422, "invalid_request")


@pytest.mark.parametrize(
    "bad_date",
    ["", "2031-3-14", "2031-03-4", "20310314", "2031/03/14", " 2031-03-14", "2031-03-14 ", "14-03-2031"],
)
def test_r3_badly_formatted_date_is_invalid_request(client, bad_date):
    assert_post_error(client, body(date=bad_date), 422, "invalid_request")


@pytest.mark.parametrize("bad_date", ["2031-02-29", "2031-02-30", "2031-04-31", "2031-13-01", "2031-00-10"])
def test_r3_non_calendar_date_is_invalid_request(client, bad_date):
    assert_post_error(client, body(date=bad_date), 422, "invalid_request")


BAD_TIMES = ["9:00", "09:0", "0900", "09-00", "09:00:00", "24:00", "25:00", "09:60", "9:30", "", " 09:00", "ab:cd"]


@pytest.mark.parametrize("bad_time", BAD_TIMES)
def test_r3_badly_formatted_start_is_invalid_request(client, bad_time):
    assert_post_error(client, body(start=bad_time), 422, "invalid_request")


@pytest.mark.parametrize("bad_time", BAD_TIMES)
def test_r3_badly_formatted_end_is_invalid_request(client, bad_time):
    assert_post_error(client, body(end=bad_time), 422, "invalid_request")


def test_r3_failed_request_keeps_existing_bookings(client):
    existing = client.post("/api/bookings", json=body(room_id=2)).json()
    assert_post_error(client, without("date"), 422, "invalid_request")
    r = client.get("/api/bookings", params={"date": DATE})
    assert r.json() == [existing]



def test_r3_json_null_body_is_invalid_request(client):
    assert_raw_post_error(client, b"null", 422, "invalid_request")

"""R2. List bookings."""

import pytest

from _rb_helpers import BOOKING_FIELDS, DATE, OTHER_DATE, assert_get_error, book


def test_r2_empty_date_returns_empty_list(client):
    r = client.get("/api/bookings", params={"date": DATE})
    assert r.status_code == 200
    assert r.json() == []


def test_r2_returns_only_bookings_on_given_date(client):
    a = book(client, date=DATE)
    book(client, date=OTHER_DATE)
    r = client.get("/api/bookings", params={"date": DATE})
    assert r.status_code == 200
    assert r.json() == [a]


def test_r2_booking_objects_have_exactly_six_fields(client):
    book(client)
    items = client.get("/api/bookings", params={"date": DATE}).json()
    assert len(items) == 1
    assert set(items[0].keys()) == BOOKING_FIELDS


def test_r2_ordered_by_room_id_then_start(client):
    b1 = book(client, room_id=3, start="14:00", end="15:00")
    b2 = book(client, room_id=1, start="16:00", end="17:00")
    b3 = book(client, room_id=3, start="09:00", end="10:00")
    b4 = book(client, room_id=1, start="08:00", end="09:00")
    b5 = book(client, room_id=2, start="12:00", end="13:00")
    r = client.get("/api/bookings", params={"date": DATE})
    assert r.status_code == 200
    assert r.json() == [b4, b2, b5, b3, b1]


def test_r2_room_filter_returns_only_that_room(client):
    a = book(client, room_id=2, start="10:00", end="11:00")
    b = book(client, room_id=2, start="08:00", end="09:00")
    book(client, room_id=1)
    book(client, room_id=4)
    r = client.get("/api/bookings", params={"date": DATE, "room_id": 2})
    assert r.status_code == 200
    assert r.json() == [b, a]


def test_r2_room_filter_with_no_bookings_returns_empty_list(client):
    book(client, room_id=1)
    r = client.get("/api/bookings", params={"date": DATE, "room_id": 4})
    assert r.status_code == 200
    assert r.json() == []


def test_r2_leap_day_is_a_valid_date(client):
    r = client.get("/api/bookings", params={"date": "2032-02-29"})
    assert r.status_code == 200
    assert r.json() == []


def test_r2_missing_date_is_invalid_request(client):
    book(client)
    assert_get_error(client, {}, 422, "invalid_request")


def test_r2_missing_date_with_room_id_is_invalid_request(client):
    book(client)
    assert_get_error(client, {"room_id": 1}, 422, "invalid_request")


@pytest.mark.parametrize(
    "bad_date",
    [
        "",
        "2031-3-14",
        "2031-03-4",
        "31-03-14",
        "20310314",
        "2031/03/14",
        "2031-03-14T00:00",
        " 2031-03-14",
        "2031-03-14 ",
        "abcd-ef-gh",
        "14-03-2031",
    ],
)
def test_r2_badly_formatted_date_is_invalid_request(client, bad_date):
    book(client)
    assert_get_error(client, {"date": bad_date}, 422, "invalid_request")


@pytest.mark.parametrize(
    "bad_date",
    ["2031-02-29", "2031-02-30", "2031-04-31", "2031-13-01", "2031-00-10", "2031-01-00", "2031-01-32"],
)
def test_r2_non_calendar_date_is_invalid_request(client, bad_date):
    book(client)
    assert_get_error(client, {"date": bad_date}, 422, "invalid_request")


@pytest.mark.parametrize("bad_room", ["abc", "1.5", "one", "1a"])
def test_r2_non_integer_room_id_is_invalid_request(client, bad_room):
    book(client)
    assert_get_error(client, {"date": DATE, "room_id": bad_room}, 422, "invalid_request")


@pytest.mark.parametrize("missing_room", [0, 5, -1, 99])
def test_r2_unknown_room_id_is_room_not_found(client, missing_room):
    book(client)
    assert_get_error(client, {"date": DATE, "room_id": missing_room}, 404, "room_not_found")


def test_r2_room_id_beyond_sqlite_range_is_room_not_found(client):
    # D2: valid integers outside SQLite's range are nonexistent ids.
    book(client)
    assert_get_error(client, {"date": DATE, "room_id": str(2**70)}, 404, "room_not_found")


def test_r2_invalid_date_checked_before_unknown_room(client):
    # D4: date is validated before room_id.
    book(client)
    assert_get_error(client, {"date": "2031-02-30", "room_id": 99}, 422, "invalid_request")


def test_r2_invalid_date_checked_before_non_integer_room(client):
    # D4: date is validated before room_id.
    book(client)
    assert_get_error(client, {"date": "bad", "room_id": "abc"}, 422, "invalid_request")

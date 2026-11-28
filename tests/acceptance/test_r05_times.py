"""R5. Times."""

import pytest

from _rb_helpers import assert_post_error, body


def _ok(client, start, end):
    r = client.post("/api/bookings", json=body(start=start, end=end))
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["start"] == start
    assert data["end"] == end


def test_r5_earliest_start_is_accepted(client):
    _ok(client, "08:00", "09:00")


def test_r5_latest_end_is_accepted(client):
    _ok(client, "21:30", "22:00")


def test_r5_thirty_minute_booking_is_accepted(client):
    _ok(client, "12:30", "13:00")


def test_r5_exactly_three_hours_is_accepted(client):
    _ok(client, "09:00", "12:00")


def test_r5_three_hours_on_half_hours_is_accepted(client):
    _ok(client, "18:30", "21:30")


def test_r5_three_hours_ending_at_closing_is_accepted(client):
    _ok(client, "19:00", "22:00")


@pytest.mark.parametrize(
    "start,end",
    [("09:15", "10:00"), ("09:01", "10:00"), ("09:59", "10:30"), ("09:45", "10:30")],
)
def test_r5_start_minutes_not_00_or_30_is_invalid_time(client, start, end):
    assert_post_error(client, body(start=start, end=end), 422, "invalid_time")


@pytest.mark.parametrize(
    "start,end",
    [("09:00", "10:15"), ("09:00", "10:01"), ("09:00", "09:59"), ("09:00", "10:45")],
)
def test_r5_end_minutes_not_00_or_30_is_invalid_time(client, start, end):
    assert_post_error(client, body(start=start, end=end), 422, "invalid_time")


@pytest.mark.parametrize("start,end", [("07:30", "08:30"), ("07:00", "08:00"), ("00:00", "01:00")])
def test_r5_start_before_opening_is_invalid_time(client, start, end):
    assert_post_error(client, body(start=start, end=end), 422, "invalid_time")


@pytest.mark.parametrize("start,end", [("21:30", "22:30"), ("21:00", "23:00"), ("22:00", "23:00"), ("23:00", "23:30")])
def test_r5_end_after_closing_is_invalid_time(client, start, end):
    assert_post_error(client, body(start=start, end=end), 422, "invalid_time")


def test_r5_end_at_2359_is_invalid_time(client):
    assert_post_error(client, body(start="21:30", end="23:59"), 422, "invalid_time")


def test_r5_start_equal_to_end_is_invalid_time(client):
    assert_post_error(client, body(start="10:00", end="10:00"), 422, "invalid_time")


def test_r5_start_after_end_is_invalid_time(client):
    assert_post_error(client, body(start="11:00", end="10:00"), 422, "invalid_time")


def test_r5_three_and_a_half_hours_is_invalid_time(client):
    assert_post_error(client, body(start="09:00", end="12:30"), 422, "invalid_time")


def test_r5_much_longer_than_three_hours_is_invalid_time(client):
    assert_post_error(client, body(start="08:00", end="22:00"), 422, "invalid_time")

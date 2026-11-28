"""R6. Room."""

import pytest

from _rb_helpers import assert_post_error, body


@pytest.mark.parametrize("room_id", [1, 2, 3, 4])
def test_r6_each_room_can_be_booked(client, room_id):
    r = client.post("/api/bookings", json=body(room_id=room_id))
    assert r.status_code == 201
    assert r.json()["room_id"] == room_id


@pytest.mark.parametrize("room_id", [0, 5, -1, 100])
def test_r6_unknown_room_is_room_not_found(client, room_id):
    assert_post_error(client, body(room_id=room_id), 404, "room_not_found")


def test_r6_room_id_beyond_sqlite_range_is_room_not_found(client):
    # D2: valid integers outside SQLite's range are nonexistent ids.
    assert_post_error(client, body(room_id=2**70), 404, "room_not_found")


def test_r6_large_negative_room_id_is_room_not_found(client):
    assert_post_error(client, body(room_id=-(2**70)), 404, "room_not_found")

"""R1. List rooms."""

from _rb_helpers import ROOMS, ROOM_FIELDS, book


def test_r1_lists_four_rooms_in_id_order(client):
    r = client.get("/api/rooms")
    assert r.status_code == 200
    assert r.json() == ROOMS


def test_r1_each_room_has_exactly_three_fields(client):
    rooms = client.get("/api/rooms").json()
    assert len(rooms) == 4
    for room in rooms:
        assert set(room.keys()) == ROOM_FIELDS


def test_r1_rooms_unchanged_after_bookings(client):
    book(client, room_id=3)
    r = client.get("/api/rooms")
    assert r.status_code == 200
    assert r.json() == ROOMS

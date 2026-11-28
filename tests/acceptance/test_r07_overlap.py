"""R7. No overlap."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from _rb_helpers import (
    BOOKING_FIELDS,
    DATE,
    OTHER_DATE,
    assert_error,
    assert_post_error,
    body,
    book,
    list_bookings,
    snapshot,
)


@pytest.mark.parametrize(
    "start,end",
    [
        ("10:00", "12:00"),  # identical
        ("09:00", "10:30"),  # overlaps the start
        ("11:30", "13:00"),  # overlaps the end
        ("10:30", "11:30"),  # inside
        ("09:00", "12:00"),  # contains
        ("10:00", "10:30"),  # same start, shorter
        ("11:30", "12:00"),  # same end, shorter
        ("09:30", "10:30"),  # 30 minute overlap at start
    ],
)
def test_r7_overlapping_booking_same_room_same_date_is_overlap(client, start, end):
    book(client, room_id=1, start="10:00", end="12:00")
    assert_post_error(client, body(room_id=1, start=start, end=end), 409, "overlap")


def test_r7_booking_ending_when_other_starts_is_allowed(client):
    book(client, room_id=1, start="10:00", end="12:00")
    r = client.post("/api/bookings", json=body(room_id=1, start="08:30", end="10:00"))
    assert r.status_code == 201


def test_r7_booking_starting_when_other_ends_is_allowed(client):
    book(client, room_id=1, start="10:00", end="12:00")
    r = client.post("/api/bookings", json=body(room_id=1, start="12:00", end="13:00"))
    assert r.status_code == 201


def test_r7_back_to_back_by_same_person_is_allowed(client):
    # P4.
    book(client, room_id=2, start="09:00", end="10:00", booked_by="Ana")
    book(client, room_id=2, start="10:00", end="11:00", booked_by="Ana")
    assert len(list_bookings(client, room_id=2)) == 2


def test_r7_gap_filled_between_two_bookings_is_allowed(client):
    book(client, room_id=1, start="09:00", end="10:00")
    book(client, room_id=1, start="11:00", end="12:00")
    r = client.post("/api/bookings", json=body(room_id=1, start="10:00", end="11:00"))
    assert r.status_code == 201
    assert len(list_bookings(client, room_id=1)) == 3


def test_r7_same_time_different_room_is_allowed(client):
    book(client, room_id=1, start="10:00", end="12:00")
    r = client.post("/api/bookings", json=body(room_id=2, start="10:00", end="12:00"))
    assert r.status_code == 201


def test_r7_same_time_same_room_different_date_is_allowed(client):
    book(client, room_id=1, date=DATE, start="10:00", end="12:00")
    r = client.post("/api/bookings", json=body(room_id=1, date=OTHER_DATE, start="10:00", end="12:00"))
    assert r.status_code == 201


def test_r7_overlap_with_one_of_several_bookings_is_overlap(client):
    book(client, room_id=3, start="08:00", end="09:00")
    book(client, room_id=3, start="12:00", end="13:00")
    book(client, room_id=4, start="10:00", end="11:00")
    assert_post_error(client, body(room_id=3, start="11:00", end="12:30"), 409, "overlap")


def test_r7_overlap_does_not_depend_on_name(client):
    book(client, room_id=1, start="10:00", end="11:00", booked_by="Ana")
    assert_post_error(
        client, body(room_id=1, start="10:00", end="11:00", booked_by="Ben"), 409, "overlap"
    )


def test_r7_concurrent_identical_requests_create_one_booking(client):
    # D6: overlap check and insert are atomic, so of eight identical concurrent
    # requests exactly one succeeds. Which one succeeds is not assumed.
    workers = 8
    timeout = 30
    payload = body(room_id=4, start="14:00", end="16:00")
    barrier = threading.Barrier(workers, timeout=timeout)

    def worker():
        barrier.wait()  # raises BrokenBarrierError on timeout instead of hanging
        return client.post("/api/bookings", json=payload)

    pool = ThreadPoolExecutor(max_workers=workers)
    try:
        futures = [pool.submit(worker) for _ in range(workers)]
        # result() re-raises any exception from a worker and has its own timeout.
        responses = [f.result(timeout=timeout) for f in futures]
    finally:
        barrier.abort()
        pool.shutdown(wait=False, cancel_futures=True)

    created = [r for r in responses if r.status_code == 201]
    rejected = [r for r in responses if r.status_code != 201]
    assert len(created) == 1, [r.status_code for r in responses]
    assert len(rejected) == workers - 1
    for r in rejected:
        assert_error(r, 409, "overlap")

    booking = created[0].json()
    assert set(booking.keys()) == BOOKING_FIELDS
    assert booking["room_id"] == 4
    assert booking["date"] == DATE
    assert booking["start"] == "14:00"
    assert booking["end"] == "16:00"
    assert booking["booked_by"] == "Ana"
    assert snapshot(client) == {DATE: [booking], OTHER_DATE: []}

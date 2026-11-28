"""Request data shapes for RoomBook. No HTTP code and no SQL."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NewBooking:
    """A POST /api/bookings request that has passed R3 to R5, with the name trimmed."""

    room_id: int
    date: str
    start: str
    end: str
    booked_by: str

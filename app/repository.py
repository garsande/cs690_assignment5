"""All SQL for RoomBook. This is the only module that imports sqlite3.

Every operation opens its own connection and closes it before returning, so no
connection is ever shared between threads.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

# Section 2: the four rooms. They never change.
_ROOMS = [
    (1, "Quiet Room A", 2),
    (2, "Quiet Room B", 2),
    (3, "Group Room C", 6),
    (4, "Group Room D", 8),
]

_ROOM_COLUMNS = 'id, name, capacity'
_BOOKING_COLUMNS = 'id, room_id, date, start, "end", booked_by'


@contextmanager
def _connect(db_path: str) -> Iterator[sqlite3.Connection]:
    """Open a fresh connection for one operation and always close it."""
    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _in_sqlite_range(n: int) -> bool:
    """D2: ids outside SQLite's 64-bit integer range are treated as missing."""
    return -(2**63) <= n < 2**63


def init_db(db_path: str) -> None:
    """Create the tables if needed and seed the four rooms when there are none."""
    with _connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS rooms ("
            " id INTEGER PRIMARY KEY,"
            " name TEXT NOT NULL,"
            " capacity INTEGER NOT NULL)"
        )
        # AUTOINCREMENT: booking ids are never reused (D5).
        conn.execute(
            "CREATE TABLE IF NOT EXISTS bookings ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " room_id INTEGER NOT NULL,"
            " date TEXT NOT NULL,"
            " start TEXT NOT NULL,"
            ' "end" TEXT NOT NULL,'
            " booked_by TEXT NOT NULL)"
        )
        conn.execute("BEGIN IMMEDIATE")
        try:
            (count,) = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()
            if count == 0:
                conn.executemany(
                    "INSERT INTO rooms (id, name, capacity) VALUES (?, ?, ?)", _ROOMS
                )
            conn.execute("COMMIT")
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise


def list_rooms(db_path: str) -> list[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(f"SELECT {_ROOM_COLUMNS} FROM rooms ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def room_exists(db_path: str, room_id: int) -> bool:
    if not _in_sqlite_range(room_id):
        return False
    with _connect(db_path) as conn:
        row = conn.execute("SELECT 1 FROM rooms WHERE id = ?", (room_id,)).fetchone()
    return row is not None


def list_bookings(db_path: str, date: str, room_id: int | None = None) -> list[dict]:
    if room_id is not None and not _in_sqlite_range(room_id):
        return []
    with _connect(db_path) as conn:
        if room_id is None:
            rows = conn.execute(
                f"SELECT {_BOOKING_COLUMNS} FROM bookings"
                " WHERE date = ? ORDER BY room_id, start",
                (date,),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT {_BOOKING_COLUMNS} FROM bookings"
                " WHERE date = ? AND room_id = ? ORDER BY room_id, start",
                (date, room_id),
            ).fetchall()
    return [dict(row) for row in rows]


def insert_booking_if_free(
    db_path: str, room_id: int, date: str, start: str, end: str, booked_by: str
) -> dict | None:
    """D6: check for overlap and insert in one write-serialized transaction.

    Returns the new booking, or None when it would overlap an existing one.
    """
    with _connect(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            clash = conn.execute(
                "SELECT 1 FROM bookings"
                ' WHERE room_id = ? AND date = ? AND start < ? AND "end" > ?'
                " LIMIT 1",
                (room_id, date, end, start),
            ).fetchone()
            if clash is not None:
                conn.execute("ROLLBACK")
                return None
            cur = conn.execute(
                'INSERT INTO bookings (room_id, date, start, "end", booked_by)'
                " VALUES (?, ?, ?, ?, ?)",
                (room_id, date, start, end, booked_by),
            )
            new_id = cur.lastrowid
            conn.execute("COMMIT")
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
    return {
        "id": new_id,
        "room_id": room_id,
        "date": date,
        "start": start,
        "end": end,
        "booked_by": booked_by,
    }


def delete_booking(db_path: str, booking_id: int) -> bool:
    if not _in_sqlite_range(booking_id):
        return False
    with _connect(db_path) as conn:
        cur = conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    return cur.rowcount > 0

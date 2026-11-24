"""Converts rows from the old booking system's export (legacy/old_bookings.csv)
into the format of the new backend.

Written years ago for the old system. Nobody remembers every case it handles, and it
has no tests. The plan is to import the old bookings next term, so this code has to
be made safe to change first.

Run it on the sample export:
    python -m legacy.old_format legacy/old_bookings.csv
"""

ROOMS = {"Room A": 1, "Room B": 2, "Room C": 3, "Room D": 4}


def to_24h(text):
    parts = text.strip().split(" ")
    h = int(parts[0].split(":")[0])
    m = parts[0].split(":")[1]
    if len(parts) > 1 and parts[1] == "PM":
        h = h + 12
    return str(h).zfill(2) + ":" + m


def parse_old_row(row):
    room = ROOMS[row["room"].strip()]
    day = row["day"].strip()
    month = day.split("/")[0]
    d = day.split("/")[1]
    year = day.split("/")[2]
    if len(year) == 2:
        year = "20" + year
    date = year + "-" + month.zfill(2) + "-" + d.zfill(2)
    name = row["who"].strip()
    name = name[0].upper() + name[1:]
    return {
        "room_id": room,
        "date": date,
        "start": to_24h(row["from"]),
        "end": to_24h(row["to"]),
        "booked_by": name,
    }


if __name__ == "__main__":
    import csv
    import sys

    with open(sys.argv[1], newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            print(parse_old_row(row))

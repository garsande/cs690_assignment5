"""R10. The application (spec section 3)."""

from pathlib import Path

from _rb_helpers import DATE, OTHER_DATE, ROOMS, assert_post_error, body, book, list_bookings, snapshot

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"


def test_r10_root_serves_index_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.content == (FRONTEND / "index.html").read_bytes()


def test_r10_serves_app_js(client):
    r = client.get("/app.js")
    assert r.status_code == 200
    assert r.content == (FRONTEND / "app.js").read_bytes()


def test_r10_serves_styles_css(client):
    r = client.get("/styles.css")
    assert r.status_code == 200
    assert r.content == (FRONTEND / "styles.css").read_bytes()


def test_r10_serves_page_independent_of_working_directory(tmp_path, monkeypatch, new_client):
    # D7: frontend is resolved relative to the repository, not the cwd.
    monkeypatch.chdir(tmp_path)
    c = new_client("cwd.db")
    r = c.get("/")
    assert r.status_code == 200
    assert r.content == (FRONTEND / "index.html").read_bytes()


def test_r10_fresh_database_has_four_rooms_and_no_bookings(new_client):
    c = new_client("fresh.db")
    assert c.get("/api/rooms").json() == ROOMS
    assert list_bookings(c) == []


def test_r10_database_file_is_created_at_db_path(tmp_path, new_client):
    new_client("created.db")
    assert (tmp_path / "created.db").exists()


def test_r10_different_files_do_not_share_bookings(new_client):
    a = new_client("a.db")
    b = new_client("b.db")
    created = book(a)
    assert list_bookings(a) == [created]
    assert list_bookings(b) == []
    # The same slot is free in the other database.
    r = b.post("/api/bookings", json=body())
    assert r.status_code == 201
    assert list_bookings(a) == [created]


def test_r10_restart_on_same_file_sees_saved_bookings(new_client):
    first = new_client("same.db")
    created = book(first, room_id=3, start="13:00", end="14:30", booked_by="Ana")
    second = new_client("same.db")
    assert list_bookings(second) == [created]


def test_r10_restart_keeps_rooms_without_duplicates(new_client):
    new_client("rooms.db")
    second = new_client("rooms.db")
    assert second.get("/api/rooms").json() == ROOMS


def test_r10_restart_still_enforces_overlap(new_client):
    first = new_client("ov.db")
    original = book(first, room_id=1, start="10:00", end="11:00", booked_by="Ana")
    second = new_client("ov.db")
    assert list_bookings(second) == [original]
    assert_post_error(
        second, body(room_id=1, start="10:30", end="11:30", booked_by="Ben"), 409, "overlap"
    )
    assert list_bookings(second) == [original]
    assert snapshot(second) == {DATE: [original], OTHER_DATE: []}


def test_r10_cancel_persists_across_restart(new_client):
    first = new_client("cancel.db")
    created = book(first)
    assert first.delete(f"/api/bookings/{created['id']}").status_code == 204
    second = new_client("cancel.db")
    assert list_bookings(second, DATE) == []


def test_r10_ids_not_reused_across_restart(new_client):
    # D5: no id reuse within the same database, also after restart.
    first = new_client("ids.db")
    created = book(first)
    assert first.delete(f"/api/bookings/{created['id']}").status_code == 204
    second = new_client("ids.db")
    again = book(second)
    assert again["id"] != created["id"]

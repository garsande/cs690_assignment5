"""R4. Name."""

import pytest

from _rb_helpers import DATE, assert_post_error, body


def _post(client, name):
    return client.post("/api/bookings", json=body(booked_by=name))


def test_r4_name_is_trimmed_in_response_and_storage(client):
    r = _post(client, "   Ana Lopez  ")
    assert r.status_code == 201
    assert r.json()["booked_by"] == "Ana Lopez"
    listed = client.get("/api/bookings", params={"date": DATE}).json()
    assert listed[0]["booked_by"] == "Ana Lopez"


def test_r4_tabs_and_newlines_are_trimmed(client):
    r = _post(client, "\t\nAna\n\t")
    assert r.status_code == 201
    assert r.json()["booked_by"] == "Ana"


def test_r4_internal_whitespace_and_case_preserved(client):
    # D3: preserve capitalization and internal whitespace.
    r = _post(client, " mAry   ANN  ")
    assert r.status_code == 201
    assert r.json()["booked_by"] == "mAry   ANN"


def test_r4_one_character_name_is_accepted(client):
    r = _post(client, "A")
    assert r.status_code == 201
    assert r.json()["booked_by"] == "A"


def test_r4_forty_character_name_is_accepted(client):
    name = "x" * 40
    r = _post(client, name)
    assert r.status_code == 201
    assert r.json()["booked_by"] == name


def test_r4_forty_characters_after_trimming_is_accepted(client):
    name = "y" * 40
    r = _post(client, "   " + name + "   ")
    assert r.status_code == 201
    assert r.json()["booked_by"] == name


def test_r4_forty_unicode_code_points_is_accepted(client):
    # D3: len() counts Unicode code points.
    name = "é" * 40
    r = _post(client, name)
    assert r.status_code == 201
    assert r.json()["booked_by"] == name


def test_r4_forty_supplementary_plane_characters_is_accepted(client):
    # D3: len() counts code points. Each emoji is one code point but two UTF-16
    # code units, so this tells code-point counting apart from code-unit counting.
    name = "\U0001F600" * 40
    r = _post(client, name)
    assert r.status_code == 201, r.text
    assert r.json()["booked_by"] == name
    assert client.get("/api/bookings", params={"date": DATE}).json()[0]["booked_by"] == name


def test_r4_forty_one_supplementary_plane_characters_is_invalid_name(client):
    assert_post_error(client, body(booked_by="\U0001F600" * 41), 422, "invalid_name")


def test_r4_forty_one_characters_is_invalid_name(client):
    assert_post_error(client, body(booked_by="z" * 41), 422, "invalid_name")


def test_r4_forty_one_unicode_code_points_is_invalid_name(client):
    assert_post_error(client, body(booked_by="é" * 41), 422, "invalid_name")


def test_r4_empty_name_is_invalid_name(client):
    assert_post_error(client, body(booked_by=""), 422, "invalid_name")


@pytest.mark.parametrize("name", [" ", "     ", "\t", "\n \t "])
def test_r4_whitespace_only_name_is_invalid_name(client, name):
    assert_post_error(client, body(booked_by=name), 422, "invalid_name")

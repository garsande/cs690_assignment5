# AGENTS.md

## Project

RoomBook, a study-room booking app. The page in `frontend/` is finished and belongs to
another team. The backend in `app/` is built to match `docs/spec.md`.

## General rules

- Read `docs/spec.md` before every change. The spec is the source of truth: when code
  and spec disagree, the spec wins. When the spec is unclear, stop and ask. Do not guess.
- Never edit anything in `frontend/`.
- Never change a test in `tests/acceptance/` to make code pass.
- Do only the task you were given. Do not add endpoints, fields, error codes, rules,
  packages or features that the spec does not ask for.
- Python 3.11 or later. Use only the packages in `requirements.txt`.
- Run the tests with `python -m pytest`.

## Backend rules

(Part 1: write this section.)

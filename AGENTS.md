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

- Keep HTTP handling in `app/routes.py`; it should translate requests and responses, not make booking decisions.
- Put all section 5 booking rules in `app/service.py`, separate from HTTP and database details.
- Keep SQL exclusively in `app/repository.py`; use `app/models.py` for request data shapes.
- Define `create_app(db_path: str = "roombook.db")` in `app/main.py` and follow section 3 for initialization, static files, and database isolation.
- Format every API failure exactly as R9 requires: only `error` and `message`, with the specified status and code.
- Use Python's built-in `sqlite3` only: no ORM or additional dependencies.
- Open and close a separate SQLite connection per request or repository operation; never share one connection across FastAPI threads.
- After each task, run `python tools/check_layers.py` and `python -m pytest` and report both outcomes.
- Extra safeguard: never hide a failing test or checker result; report the failure and stop before unrelated changes.


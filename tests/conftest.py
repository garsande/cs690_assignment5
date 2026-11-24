"""Shared test fixtures. Given: do not change this file.

The import of app.main happens inside each fixture, so pytest can collect your tests
before the backend exists. Until then, every test that uses a fixture errors with
"No module named 'app.main'", which is the right failure.
"""

from contextlib import ExitStack

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    """A client for a backend with a fresh, empty database file (spec section 3)."""
    from app.main import create_app

    with TestClient(create_app(str(tmp_path / "test.db"))) as c:
        yield c


@pytest.fixture
def new_client(tmp_path):
    """new_client("a.db") returns a client for the database file a.db in a temporary
    folder. Use two names for two separate databases. Calling it again with the same
    name is like restarting the backend on the same file (R10)."""
    stack = ExitStack()

    def make(name: str = "test.db") -> TestClient:
        from app.main import create_app

        return stack.enter_context(TestClient(create_app(str(tmp_path / name))))

    yield make
    stack.close()

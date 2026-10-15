from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_messages(client: TestClient) -> None:
    with app.state.pool.connection() as conn:
        conn.execute("TRUNCATE messages RESTART IDENTITY")

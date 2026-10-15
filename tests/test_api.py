from datetime import datetime

import pytest
from fastapi.testclient import TestClient


def post_message(client: TestClient, author: str, text: str) -> dict:
    response = client.post("/messages", json={"author": author, "text": text})
    assert response.status_code == 201
    return response.json()


def test_index_returns_greeting(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()


def test_health_reports_status_and_version(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"]


def test_list_is_empty_initially(client: TestClient) -> None:
    response = client.get("/messages")

    assert response.status_code == 200
    assert response.json() == []


def test_create_message_returns_created_message(client: TestClient) -> None:
    created = post_message(client, "Ада", "Привет")

    assert created["id"] == 1
    assert created["author"] == "Ада"
    assert created["text"] == "Привет"


def test_list_returns_newest_first(client: TestClient) -> None:
    post_message(client, "Ада", "первое")
    post_message(client, "Алан", "второе")

    texts = [message["text"] for message in client.get("/messages").json()]

    assert texts == ["второе", "первое"]


def test_list_respects_limit(client: TestClient) -> None:
    for number in range(3):
        post_message(client, "Ада", f"сообщение {number}")

    response = client.get("/messages", params={"limit": 2})

    assert len(response.json()) == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"author": "", "text": "текст"},
        {"author": "Ада", "text": ""},
        {"author": "Ада"},
        {"author": "x" * 101, "text": "текст"},
        {"author": "   ", "text": "текст"},
        {"author": "Ада", "text": "\n\t "},
    ],
)
def test_create_message_rejects_invalid_payload(
    client: TestClient, payload: dict
) -> None:
    response = client.post("/messages", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize("limit", [0, 101])
def test_list_rejects_out_of_range_limit(client: TestClient, limit: int) -> None:
    response = client.get("/messages", params={"limit": limit})

    assert response.status_code == 422


def test_create_message_sets_created_at(client: TestClient) -> None:
    created = post_message(client, "Ада", "Привет")

    assert datetime.fromisoformat(created["created_at"]).tzinfo is not None


def test_create_message_strips_surrounding_whitespace(client: TestClient) -> None:
    created = post_message(client, "  Ада ", "\n Привет \t")

    assert created["author"] == "Ада"
    assert created["text"] == "Привет"

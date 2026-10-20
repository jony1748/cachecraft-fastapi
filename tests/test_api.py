from app.services import payloads


def test_create_and_read_interleaved_payload(client):
    response = client.post(
        "/api/v1/payload",
        json={
            "list_1": ["first string", "second string", "third string"],
            "list_2": ["other string", "another string", "last string"],
        },
    )
    assert response.status_code == 201
    body = client.get(f"/api/v1/payload/{response.json()['id']}")
    assert body.json() == {
        "output": (
            "FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING, THIRD STRING, LAST STRING"
        )
    }


def test_reuses_full_payload_identifier(client):
    data = {"list_1": ["a"], "list_2": ["b"]}
    first = client.post("/api/v1/payload", json=data).json()
    second = client.post("/api/v1/payload", json=data).json()
    assert first["id"] == second["id"]
    assert second["reused"] is True


def test_transform_cache_avoids_duplicate_transform_calls(client, monkeypatch):
    calls = []
    monkeypatch.setattr(payloads, "transform", lambda value: calls.append(value) or value.upper())
    client.post("/api/v1/payload", json={"list_1": ["shared"], "list_2": ["first"]})
    client.post("/api/v1/payload", json={"list_1": ["shared"], "list_2": ["second"]})
    assert calls == ["shared", "first", "second"]


def test_repeated_value_is_transformed_once_within_a_request(client, monkeypatch):
    calls = []
    monkeypatch.setattr(payloads, "transform", lambda value: calls.append(value) or value.upper())
    response = client.post("/api/v1/payload", json={"list_1": ["same"], "list_2": ["same"]})
    assert response.status_code == 201
    assert calls == ["same"]


def test_invalid_lengths_and_missing_id_are_clear(client):
    invalid = client.post("/api/v1/payload", json={"list_1": ["a"], "list_2": []})
    missing = client.get("/api/v1/payload/missing")
    assert invalid.status_code == 422
    assert invalid.json()["error"] == "INVALID_INPUT"
    assert missing.status_code == 404
    assert missing.json()["error"] == "PAYLOAD_NOT_FOUND"

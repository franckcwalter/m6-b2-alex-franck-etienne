"""API tests — backend service."""
from __future__ import annotations


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_score_valid(client, valid_payload):
    resp = client.post("/score", json=valid_payload)
    assert resp.status_code == 200
    assert resp.json()["prediction"] in (0, 1)


def test_score_invalid_returns_422(client, valid_payload):
    bad = dict(valid_payload)
    bad["fico_range_low"] = 9999
    resp = client.post("/score", json=bad)
    assert resp.status_code == 422

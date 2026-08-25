"""API tests — backend service."""
from __future__ import annotations

import pytest


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


@pytest.mark.parametrize("client", ["unreachable"], indirect=True)
def test_score_returns_503_when_model_is_unreachable(client, valid_payload):
    resp = client.post("/score", json=valid_payload)

    assert resp.status_code == 503
    assert resp.json()["detail"] == "Model service unavailable"


@pytest.mark.parametrize("client", [500], indirect=True)
def test_score_returns_502_when_model_returns_server_error(client, valid_payload):
    resp = client.post("/score", json=valid_payload)

    assert resp.status_code == 502
    assert resp.json()["detail"] == "Model service error"

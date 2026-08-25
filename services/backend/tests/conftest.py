"""Pytest fixtures — backend service."""
from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

SERVICE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SERVICE_ROOT))

MOCK_PREDICTION = {
    "prediction": 1,
    "probability": 0.73,
    "model_version": "v2.0.0",
    "request_id": "test",
}

_real_async_client = httpx.AsyncClient


@pytest.fixture
def client(monkeypatch):
    """FastAPI TestClient with the model service mocked via httpx.MockTransport."""
    import app.main as main_module
    from app.main import app
    from fastapi.testclient import TestClient

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=MOCK_PREDICTION)

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        main_module.httpx, "AsyncClient",
        lambda **kw: _real_async_client(transport=transport, **kw),
    )

    with TestClient(app) as c:
        yield c


@pytest.fixture
def valid_payload() -> dict:
    return {
        "loan_amnt": 10000.0,
        "int_rate": 13.5,
        "installment": 340.0,
        "annual_inc": 55000.0,
        "dti": 18.2,
        "delinq_2yrs": 0,
        "fico_range_low": 690,
        "revol_util": 42.5,
        "term": "36 months",
        "grade": "B",
        "home_ownership": "MORTGAGE",
        "verification_status": "Not Verified",
        "purpose": "debt_consolidation",
        "emp_length": "10+ years",
    }

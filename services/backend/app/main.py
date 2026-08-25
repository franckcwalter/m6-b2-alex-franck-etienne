"""Backend orchestrator service.

Exposed to the browser (via the nginx frontend), validates input with the
**same Pydantic schema** as the model, calls the `model` service internally
(`http://model:8000/predict`), and exposes `/health`, `/score`.
"""
from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.middleware import LoggingMiddleware
from app.schemas import HealthResponse, LoanApplication, Prediction

MODEL_URL = os.environ.get("MODEL_URL", "http://model:8000")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:8088").split(",")

app = FastAPI(title="Pyrenex Backend Orchestrator", version="1.0.0")
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

# TODO 1 — exposer /metrics avec prometheus-fastapi-instrumentator
#   (cf. service model). Pensez à une métrique métier : compteur d'erreurs
#   upstream lors de l'appel au model.


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Backend liveness (does NOT depend on the model)."""
    return HealthResponse(status="ok")


@app.post("/score", response_model=Prediction)
async def score(application: LoanApplication, request: Request) -> Prediction:
    """Validate input, call the model service, return the prediction.

    - Model unreachable -> 503
    - Model error (5xx) -> 502
    """
    request_id = getattr(request.state, "request_id", "n/a")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{MODEL_URL}/predict",
                json=application.model_dump(),
                headers={"X-Request-ID": request_id},
            )
    except httpx.RequestError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Model service unavailable")

    if resp.status_code >= 500:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Model service error")

    data = resp.json()
    return Prediction(
        prediction=data["prediction"],
        probability=data["probability"],
        model_version=data["model_version"],
        request_id=request_id,
    )

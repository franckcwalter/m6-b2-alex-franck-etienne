"""Tests du garde-fou d'évaluation continue."""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

MODULE_PATH = Path(__file__).parent.parent / "scripts" / "evaluate_model.py"
MODULE_SPEC = importlib.util.spec_from_file_location("evaluate_model", MODULE_PATH)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:
    raise ImportError(f"Cannot load {MODULE_PATH}")
evaluate_model = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(evaluate_model)


class PerfectModel:
    """Modèle déterministe minimal pour tester les métriques."""

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.array([0, 0, 1, 1])

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return np.array(
            [
                [0.9, 0.1],
                [0.8, 0.2],
                [0.2, 0.8],
                [0.1, 0.9],
            ]
        )


@pytest.fixture
def reference_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "feature": [10, 20, 30, 40],
            "loan_status": ["Fully Paid", "Fully Paid", "Charged Off", "Charged Off"],
        }
    )


@pytest.fixture
def metadata() -> dict:
    return {
        "model_version": "test",
        "feature_columns_numeric": ["feature"],
        "feature_columns_categorical": [],
        "target_column": "loan_status",
        "target_mapping": {"Fully Paid": 0, "Charged Off": 1},
    }


def test_compute_metrics_for_perfect_predictions(reference_df, metadata):
    metrics = evaluate_model.compute_metrics(PerfectModel(), reference_df, metadata)

    assert metrics == {
        "f1_macro": 1.0,
        "f1_default": 1.0,
        "roc_auc": 1.0,
        "recall_default": 1.0,
    }


def test_check_thresholds_accepts_golden_metrics():
    metrics = {
        "f1_macro": 0.676,
        "f1_default": 0.672,
        "roc_auc": 0.713,
        "recall_default": 0.664,
    }

    assert evaluate_model.check_thresholds(metrics, metrics) == []


def test_check_thresholds_rejects_degraded_metrics():
    baseline = {
        "f1_macro": 0.676,
        "f1_default": 0.672,
        "roc_auc": 0.713,
        "recall_default": 0.664,
    }
    degraded = {metric_name: 0.0 for metric_name in baseline}

    violations = evaluate_model.check_thresholds(degraded, baseline)

    assert any("f1_macro" in violation for violation in violations)
    assert any("f1_default" in violation for violation in violations)
    assert any("roc_auc" in violation for violation in violations)
    assert any("recall_default" in violation for violation in violations)


def test_freeze_and_load_baseline(tmp_path, monkeypatch, reference_df, metadata):
    reference_set = tmp_path / "data" / "reference_set.csv"
    baseline_path = tmp_path / "data" / "reference_baseline.json"
    reference_set.parent.mkdir()
    monkeypatch.setattr(evaluate_model, "ROOT", tmp_path)
    monkeypatch.setattr(evaluate_model, "REFERENCE_SET", reference_set)
    monkeypatch.setattr(evaluate_model, "REFERENCE_BASELINE", baseline_path)

    baseline = evaluate_model.freeze_baseline(
        PerfectModel(),
        reference_df,
        metadata,
    )

    assert baseline["n_reference"] == 4
    assert baseline["metrics"]["f1_macro"] == 1.0
    assert json.loads(baseline_path.read_text()) == baseline
    assert evaluate_model.load_baseline() == baseline["metrics"]

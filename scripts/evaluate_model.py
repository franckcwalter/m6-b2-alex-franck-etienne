"""Évaluation continue du modèle Pyrenex avec tracking MLflow.

À chaque release : recalcule les métriques cibles sur un jeu de référence
figé, trace le run dans MLflow, compare aux seuils et retourne un code non nul
si la release doit être bloquée.

Usage cible::

    python scripts/evaluate_model.py --freeze-baseline             # une fois, au gel du jeu
    python scripts/evaluate_model.py --release-tag v2.0.0
    python scripts/evaluate_model.py --release-tag bad --degrade   # test du rouge
    mlflow ui    # comparer les runs

Le garde-fou compare toujours au golden run mesuré sur le jeu de référence,
jamais aux métriques du holdout M1 qui proviennent d'une autre population.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, recall_score, roc_auc_score

ROOT = Path(__file__).parent.parent
MODELS_DIR = ROOT / "services" / "model" / "models"
REFERENCE_SET = ROOT / "data" / "reference_set.csv"
REFERENCE_BASELINE = ROOT / "data" / "reference_baseline.json"

THRESHOLDS: dict[str, dict[str, float]] = {
    "f1_macro": {
        # Garantit une qualité globale minimale pour les deux classes.
        "absolute_min": 0.55,
        # Arrondi au-dessus du bruit bootstrap mesuré : 2σ = 0.0431.
        "max_drop_vs_baseline": 0.044,
    },
    "f1_default": {
        # Empêche la qualité sur la classe défaut de devenir inutilisable.
        "absolute_min": 0.40,
        # Arrondi au-dessus du bruit bootstrap mesuré : 2σ = 0.0500.
        "max_drop_vs_baseline": 0.051,
    },
    "roc_auc": {
        # Exige une capacité de discrimination supérieure à un résultat aléatoire.
        "absolute_min": 0.65,
        # Arrondi au-dessus du bruit bootstrap mesuré : 2σ = 0.0473.
        "max_drop_vs_baseline": 0.048,
    },
    "recall_default": {
        # Exige de détecter au minimum 60 % des défauts réels.
        "absolute_min": 0.60,
        # Arrondi au-dessus du bruit bootstrap mesuré : 2σ = 0.0614.
        "max_drop_vs_baseline": 0.062,
    },
}


def compute_metrics(model, df: pd.DataFrame, meta: dict) -> dict[str, float]:
    """Calcule les métriques cibles sur le jeu de référence."""
    feature_columns = (
        meta["feature_columns_numeric"] + meta["feature_columns_categorical"]
    )
    target_column = meta["target_column"]

    X = df[feature_columns]
    y = df[target_column].map(meta["target_mapping"])
    if y.isna().any():
        unknown_targets = sorted(df.loc[y.isna(), target_column].unique())
        raise ValueError(f"Unknown target labels: {unknown_targets}")

    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]

    return {
        "f1_macro": float(f1_score(y, predictions, average="macro")),
        "f1_default": float(f1_score(y, predictions, pos_label=1)),
        "roc_auc": float(roc_auc_score(y, probabilities)),
        "recall_default": float(recall_score(y, predictions, pos_label=1)),
    }


def compute_bootstrap_noise(
    model,
    df: pd.DataFrame,
    meta: dict,
    n_iterations: int = 500,
    random_state: int = 42,
) -> dict:
    """Estime le bruit d'échantillonnage des métriques par bootstrap."""
    rng = np.random.default_rng(random_state)
    target_column = meta["target_column"]
    scores: dict[str, list[float]] = {}
    skipped_iterations = 0

    for _ in range(n_iterations):
        indices = rng.integers(0, len(df), size=len(df))
        sample = df.iloc[indices].reset_index(drop=True)

        if sample[target_column].nunique() < 2:
            skipped_iterations += 1
            continue

        for metric_name, value in compute_metrics(model, sample, meta).items():
            scores.setdefault(metric_name, []).append(value)

    if not scores:
        raise ValueError("Bootstrap failed: no sample contained both target classes")

    metrics = {
        metric_name: {
            "sigma": float(np.std(values)),
            "two_sigma": float(2 * np.std(values)),
        }
        for metric_name, values in scores.items()
    }
    return {
        "requested_iterations": n_iterations,
        "valid_iterations": n_iterations - skipped_iterations,
        "skipped_iterations": skipped_iterations,
        "random_state": random_state,
        "metrics": metrics,
    }


def check_thresholds(metrics: dict[str, float], baseline: dict) -> list[str]:
    """Retourne la liste des violations de seuil (vide = release OK)."""
    violations = []

    for metric_name, rules in THRESHOLDS.items():
        current_value = metrics[metric_name]
        baseline_value = baseline[metric_name]
        absolute_min = rules["absolute_min"]
        max_drop = rules["max_drop_vs_baseline"]

        if current_value < absolute_min:
            violations.append(
                f"{metric_name}={current_value:.4f} is below "
                f"absolute minimum {absolute_min:.4f}"
            )

        actual_drop = baseline_value - current_value
        if actual_drop > max_drop:
            violations.append(
                f"{metric_name} dropped by {actual_drop:.4f} from golden baseline "
                f"(maximum allowed: {max_drop:.4f})"
            )

    return violations


def load_baseline() -> dict:
    """Charge le golden run (baseline mesurée sur le jeu de référence)."""
    if not REFERENCE_BASELINE.exists():
        raise FileNotFoundError(
            "Golden baseline missing. Run "
            "`python scripts/evaluate_model.py --freeze-baseline` first."
        )

    baseline = json.loads(REFERENCE_BASELINE.read_text(encoding="utf-8"))
    metrics = baseline.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError(
            f"Invalid golden baseline: missing metrics in {REFERENCE_BASELINE}"
        )
    return metrics


def freeze_baseline(model, df: pd.DataFrame, meta: dict) -> dict:
    """Mesure et gèle le golden run sur le jeu de référence."""
    baseline = {
        "model_version": meta["model_version"],
        "reference_set": str(REFERENCE_SET.relative_to(ROOT)),
        "n_reference": len(df),
        "metrics": compute_metrics(model, df, meta),
    }
    REFERENCE_BASELINE.write_text(
        json.dumps(baseline, indent=2) + "\n",
        encoding="utf-8",
    )
    return baseline


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-tag", default="dev")
    parser.add_argument("--degrade", action="store_true")
    parser.add_argument("--freeze-baseline", action="store_true")
    parser.add_argument("--bootstrap", action="store_true")
    args = parser.parse_args()

    model = joblib.load(MODELS_DIR / "pyrenex_risk_v2.joblib")
    meta = json.loads((MODELS_DIR / "pyrenex_risk_v2.json").read_text(encoding="utf-8"))
    df = pd.read_csv(REFERENCE_SET)

    if args.freeze_baseline:
        print(json.dumps(freeze_baseline(model, df, meta), indent=2))
        return 0

    if args.bootstrap:
        print(json.dumps(compute_bootstrap_noise(model, df, meta), indent=2))
        return 0

    if args.degrade:
        # Simule un bug de preprocessing : les caractéristiques ne correspondent
        # plus aux vraies réponses, tout en conservant un schéma techniquement valide.
        feature_columns = (
            meta["feature_columns_numeric"] + meta["feature_columns_categorical"]
        )
        shuffled_features = df[feature_columns].sample(
            frac=1,
            random_state=42,
        )
        df = df.copy()
        df[feature_columns] = shuffled_features.reset_index(drop=True)

    metrics = compute_metrics(model, df, meta)
    baseline = load_baseline()
    violations = check_thresholds(metrics, baseline)
    model_params = {
        name: value
        for name, value in meta["hyperparameters"].items()
        if name != "n_jobs"
    }

    mlflow.set_experiment("pyrenex-eval-continue")
    with mlflow.start_run(run_name=args.release_tag):
        mlflow.log_params(
            {
                "model_version": meta["model_version"],
                "release_tag": args.release_tag,
                "reference_set": str(REFERENCE_SET.relative_to(ROOT)),
                "n_reference": len(df),
                "dataset_sha256": meta["dataset_sha256"],
                **model_params,
            }
        )
        mlflow.log_metrics(metrics)
        mlflow.set_tag("release_blocked", str(bool(violations)))

    print(json.dumps({"metrics": metrics, "violations": violations}, indent=2))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())

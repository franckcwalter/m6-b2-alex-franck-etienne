"""Construit un jeu de référence équilibré depuis le holdout M1."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
OUTPUT_PATH = ROOT / "data" / "reference_set.csv"
TARGET_COLUMN = "loan_status"
N_PER_CLASS = 250
RANDOM_STATE = 42


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("holdout", type=Path)
    args = parser.parse_args()

    holdout = pd.read_csv(args.holdout)
    reference_set = (
        holdout.groupby(TARGET_COLUMN, group_keys=False)
        .sample(n=N_PER_CLASS, random_state=RANDOM_STATE)
        .sample(frac=1, random_state=RANDOM_STATE)
        .reset_index(drop=True)
    )
    reference_set.to_csv(OUTPUT_PATH, index=False)

    counts = reference_set[TARGET_COLUMN].value_counts().to_dict()
    print(f"Created {OUTPUT_PATH} with {len(reference_set)} rows: {counts}")


if __name__ == "__main__":
    main()

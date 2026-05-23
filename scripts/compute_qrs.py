#!/usr/bin/env python3
"""Compute Quantum Readiness Score (QRS) rankings for IonSense-QKG.

The QRS is a transparent metadata-driven heuristic for prioritising
battery datasets for near-term hybrid quantum-classical experimentation.
It is not an empirical quantum-advantage score.

Scoring convention:
    high   -> 1.0
    medium -> 0.5
    low    -> 0.0

By default, all six components are uniformly weighted.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd

DEFAULT_COMPONENTS = [
    "feature_compactness",
    "sequence_suitability",
    "modality_compatibility",
    "label_availability",
    "preprocessing_burden",
    "access_reproducibility",
]

SCORE_MAP: Dict[str, float] = {
    "high": 1.0,
    "medium": 0.5,
    "low": 0.0,
}


def parse_weights(weight_string: str | None, components: Iterable[str]) -> Dict[str, float]:
    """Parse optional weights of the form key=value,key=value.

    If no weights are supplied, uniform weights are used. Supplied weights
    are normalised to sum to one.
    """
    components = list(components)
    if not weight_string:
        return {component: 1.0 / len(components) for component in components}

    weights = {component: 0.0 for component in components}
    for item in weight_string.split(","):
        if not item.strip():
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        if key not in weights:
            raise ValueError(f"Unknown QRS component in weights: {key}")
        weights[key] = float(value)

    total = sum(weights.values())
    if total <= 0:
        raise ValueError("At least one weight must be positive.")
    return {key: value / total for key, value in weights.items()}


def score_component(value: object) -> float:
    key = str(value).strip().lower()
    if key not in SCORE_MAP:
        raise ValueError(f"Invalid component value {value!r}; expected high, medium, or low.")
    return SCORE_MAP[key]


def compute_qrs(input_csv: Path, output_csv: Path, weights: Dict[str, float]) -> pd.DataFrame:
    df = pd.read_csv(input_csv)
    missing = [component for component in weights if component not in df.columns]
    if missing:
        raise ValueError(f"Input file is missing QRS component columns: {missing}")

    for component in weights:
        df[f"{component}_score"] = df[component].map(score_component)

    df["qrs"] = sum(df[f"{component}_score"] * weight for component, weight in weights.items())
    df["qrs"] = df["qrs"].round(3)

    df = df.sort_values(
        by=["qrs", "dataset_name"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))

    preferred = [
        "rank",
        "dataset_id",
        "dataset_name",
        "category",
        "task_type",
        "modality",
        "sequence_type",
        "label_type",
        "estimated_qubits_min",
        "estimated_qubits_max",
        "qrs",
        "nisq_feasibility",
        *weights.keys(),
        *[f"{component}_score" for component in weights],
        "preprocessing_need",
        "candidate_quantum_encoding",
        "access_status",
        "related_papers_count",
        "baseline_available",
        "scale_summary",
        "notes",
    ]
    ordered = [column for column in preferred if column in df.columns]
    remaining = [column for column in df.columns if column not in ordered]
    df = df[ordered + remaining]

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute IonSense-QKG Quantum Readiness Score rankings.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("metadata/datasets_qkg_enriched.csv"),
        help="Path to enriched metadata CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("metadata/datasets_qkg_ranked.csv"),
        help="Path for ranked QRS output CSV.",
    )
    parser.add_argument(
        "--weights",
        default=None,
        help=(
            "Optional comma-separated weights, e.g. "
            "feature_compactness=2,sequence_suitability=1,modality_compatibility=1," 
            "label_availability=2,preprocessing_burden=1,access_reproducibility=1"
        ),
    )
    args = parser.parse_args()

    weights = parse_weights(args.weights, DEFAULT_COMPONENTS)
    ranked = compute_qrs(args.input, args.output, weights)
    print(f"Wrote {len(ranked)} ranked datasets to {args.output}")
    print(ranked[["rank", "dataset_name", "qrs", "nisq_feasibility"]].to_string(index=False))


if __name__ == "__main__":
    main()

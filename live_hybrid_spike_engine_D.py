"""
live_hybrid_spike_engine.py

Live-implementation av Hybrid V3 för Streamlit-appen.

Användning i badge_engine.py:

    from live_hybrid_spike_engine import get_hybrid_round_spikes

och ersätt kroppen i get_round_spikes med:

    return get_hybrid_round_spikes(
        all_races=all_races,
        calculate_spike_score=calculate_spike_score,
        rank_horses=_rank_horses_by_total_score,
        apply_value_flags=apply_system_only_value_flags,
    )
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

from badge_rules import get_loppbadge, get_race_metrics
from environment_live_engine import classify_environment, load_environment_model


ROOT = Path(__file__).resolve().parent

ENVIRONMENT_REGISTRY_FILE = (
    ROOT
    / "output"
    / "environment_registry"
    / "environment_registry.csv"
)

SPIKE_PROFILE_FILE = (
    ROOT
    / "output"
    / "spike_profile_weighting"
    / "weighted_spike_profiles.csv"
)

RANK1_TREE_MODEL_FILE = (
    ROOT
    / "output"
    / "rank1_environment_tree"
    / "rank1_environment_tree_model.joblib"
)

GLOBAL_SPIKE_PERCENT = 103 / 249 * 100
TOP_N = 3

# ============================================================
# LOCKED HYBRID D
# Environment V2 + Spike V2 + Rescue V1
# Frozen after BUILD90 and validated once on FROZEN31.
# ============================================================

HYBRID_D_VERSION = "HYBRID_D_BUILD90_FROZEN_20260817_FINAL_ENV_LIVE"
ENVIRONMENT_V2_VERSION = "ENVIRONMENT_V2_BUILD81_FROZEN_20260814"

SPIKE_V2_MODEL_FILE = (
    ROOT / "config" / "SPIKE_V2_BUILD90_FROZEN_CANDIDATE.cbm"
)
SPIKE_V2_META = {'model_name': 'SPIKE_V2_BUILD90_FROZEN_CANDIDATE', 'status': 'FROZEN_CANDIDATE_NOT_YET_TESTED_ON_FROZEN31', 'environment_version': 'ENVIRONMENT_V2_BUILD81_FROZEN_20260814', 'build_rounds': 90, 'build_races': 702, 'build_first_date': 20250625, 'build_last_date': 20260502, 'frozen_rounds': 31, 'frozen_first_date': 20260506, 'frozen_last_date': 20260815, 'features': ['v2_environment', 'v2_rank1_pct', 'v2_observations', 'spike_score', 'spike_gap_1_2', 'spike_gap_1_3', 'spread_1_8', 'score_gap_1_2', 'score_gap_1_3', 'total_score', 'field_size', 'race_type', 'start_type', 'distance_bucket'], 'categorical_features': ['v2_environment', 'race_type', 'start_type', 'distance_bucket'], 'numeric_medians': {'v2_rank1_pct': 32.25, 'v2_observations': 92.0, 'spike_score': 304.18, 'spike_gap_1_2': 28.47, 'spike_gap_1_3': 47.47000000000001, 'spread_1_8': 59.0, 'score_gap_1_2': 12.5, 'score_gap_1_3': 23.0, 'total_score': 172.0, 'field_size': 12.0}, 'catboost_params': {'iterations': 200, 'depth': 3, 'learning_rate': 0.035, 'l2_leaf_reg': 8, 'random_strength': 1, 'random_seed': 20260817}, 'validation': {'group_oof_selections': 270, 'group_oof_winners': 121, 'group_oof_hit_rate_pct': 44.814815, 'forward45_selections': 135, 'forward45_winners': 70, 'forward45_hit_rate_pct': 51.851852, 'forward_blocks_winners': [25, 27, 18]}, 'frozen31_predictions_generated': False, 'frozen31_results_inspected': False}

RESCUE_V1_MODEL_FILE = (
    ROOT / "config" / "RESCUE_V1_BUILD90_FROZEN.cbm"
)
RESCUE_V1_META = {'model_name': 'RESCUE_V1_BUILD90_FROZEN', 'status': 'FROZEN_NOT_TESTED_ON_FROZEN31', 'build_rounds': 90, 'candidate_ranks': [1, 2, 3], 'features': ['model_rank', 'total_score', 'spike_score', 'percent', 'avg_odds', 'form_score', 'speed_score', 'latest_start_score', 'driver_score', 'post_score'], 'numeric_medians': {'model_rank': 2.0, 'total_score': 158.0, 'spike_score': 274.03, 'percent': 14.0, 'avg_odds': 8.395, 'form_score': 28.0, 'speed_score': 22.0, 'latest_start_score': 7.0, 'driver_score': 8.0, 'post_score': 11.0}, 'catboost_params': {'iterations': 150, 'depth': 3, 'learning_rate': 0.035, 'l2_leaf_reg': 8, 'random_strength': 1, 'random_seed': 20260817}, 'activation_rule': 'switch rank1 to highest rescue probability among ranks 2-3 if alt_p - rank1_p >= margin', 'margin': 0.05, 'oof_baseline_winners': 117, 'oof_rescued_winners': 122, 'oof_delta': 5, 'activations': 42, 'block_deltas': [1, 0, 4], 'frozen31_predictions_generated': False, 'frozen31_results_inspected': False}

EXPECTED_SPIKE_V2_FEATURES = [
    "v2_environment",
    "v2_rank1_pct",
    "v2_observations",
    "spike_score",
    "spike_gap_1_2",
    "spike_gap_1_3",
    "spread_1_8",
    "score_gap_1_2",
    "score_gap_1_3",
    "total_score",
    "field_size",
    "race_type",
    "start_type",
    "distance_bucket",
]

EXPECTED_RESCUE_V1_FEATURES = [
    "model_rank",
    "total_score",
    "spike_score",
    "percent",
    "avg_odds",
    "form_score",
    "speed_score",
    "latest_start_score",
    "driver_score",
    "post_score",
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def _to_bool(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)

    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value) != 0

    return str(value or "").strip().lower() in {
        "true",
        "1",
        "1.0",
        "ja",
        "yes",
        "y",
        "j",
    }


def _bucket_score_gap(value: Any) -> str:
    value = _safe_float(value, np.nan)

    if pd.isna(value):
        return "Unknown"
    if value < 5:
        return "0–5"
    if value < 10:
        return "5–10"
    if value < 15:
        return "10–15"
    if value < 20:
        return "15–20"
    return "20+"


def _bucket_spike_gap(value: Any) -> str:
    value = _safe_float(value, np.nan)

    if pd.isna(value):
        return "Unknown"
    if value < 10:
        return "0–10"
    if value < 20:
        return "10–20"
    if value < 30:
        return "20–30"
    if value < 40:
        return "30–40"
    return "40+"


def _bucket_spike_score(value: Any) -> str:
    value = _safe_float(value, np.nan)

    if pd.isna(value):
        return "Unknown"
    if value < 300:
        return "<300"
    if value < 325:
        return "300–325"
    if value < 350:
        return "325–350"
    if value < 375:
        return "350–375"
    if value < 400:
        return "375–400"
    return "400+"


def _bucket_spread(value: Any) -> str:
    value = _safe_float(value, np.nan)

    if pd.isna(value):
        return "Unknown"
    if value < 60:
        return "<60"
    if value < 70:
        return "60–70"
    if value < 80:
        return "70–80"
    return "80+"


def _bucket_value_count(value: Any) -> str:
    value = _safe_int(value, 0)

    if value >= 3:
        return "3+"

    return str(value)


def _profile_environment_bucket(value: Any) -> str:
    value = _safe_float(value, np.nan)

    if pd.isna(value):
        return "Unknown"
    if value < 40:
        return "<40"
    if value < 45:
        return "40–45"
    if value < 50:
        return "45–50"
    if value < 55:
        return "50–55"
    if value < 60:
        return "55–60"
    if value < 65:
        return "60–65"
    return "65+"


def _profile_observations_bucket(value: Any) -> str:
    value = _safe_int(value, 0)

    if value < 10:
        return "<10"
    if value < 20:
        return "10–19"
    if value < 30:
        return "20–29"
    if value < 40:
        return "30–39"
    if value < 60:
        return "40–59"
    if value < 100:
        return "60–99"
    return "100+"


def _normalise_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, (bool, np.bool_)):
        return bool(value)

    return str(value)


@lru_cache(maxsize=1)
def _load_environment_registry() -> pd.DataFrame:
    if not ENVIRONMENT_REGISTRY_FILE.exists():
        raise FileNotFoundError(
            f"Hittar inte miljöregistret: "
            f"{ENVIRONMENT_REGISTRY_FILE}"
        )

    registry = pd.read_csv(ENVIRONMENT_REGISTRY_FILE)

    required = {
        "environment_rank",
        "observations",
        "winners",
        "hit_rate_percent",
        "adjusted_hit_rate_percent",
        "ranking_score_percent",
        "depth",
        "environment",
        "conditions_json",
    }

    missing = sorted(required.difference(registry.columns))

    if missing:
        raise KeyError(
            "Miljöregistret saknar: "
            + ", ".join(missing)
        )

    registry = registry.copy()
    registry["_parsed_conditions"] = (
        registry["conditions_json"].apply(json.loads)
    )

    return registry.sort_values(
        [
            "ranking_score_percent",
            "adjusted_hit_rate_percent",
            "observations",
            "depth",
        ],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)


@lru_cache(maxsize=1)
def _load_spike_profiles() -> dict[str, dict[str, Any]]:
    if not SPIKE_PROFILE_FILE.exists():
        raise FileNotFoundError(
            f"Hittar inte Spike-profilerna: "
            f"{SPIKE_PROFILE_FILE}"
        )

    profiles = pd.read_csv(SPIKE_PROFILE_FILE)

    required = {
        "profile",
        "observations",
        "winners",
        "weighted_medium_percent",
    }

    missing = sorted(required.difference(profiles.columns))

    if missing:
        raise KeyError(
            "Spike-profilfilen saknar: "
            + ", ".join(missing)
        )

    result: dict[str, dict[str, Any]] = {}

    for _, row in profiles.iterrows():
        result[str(row["profile"])] = {
            "percent": _safe_float(
                row["weighted_medium_percent"],
                GLOBAL_SPIKE_PERCENT,
            ),
            "observations": _safe_int(
                row["observations"],
                0,
            ),
            "winners": _safe_int(
                row["winners"],
                0,
            ),
        }

    return result


@lru_cache(maxsize=1)
def _load_rank1_tree_bundle() -> dict[str, Any]:
    if not RANK1_TREE_MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Hittar inte Rank1-trädet: "
            f"{RANK1_TREE_MODEL_FILE}"
        )

    bundle = joblib.load(RANK1_TREE_MODEL_FILE)

    required = {
        "pipeline",
        "features",
        "leaves",
    }

    missing = sorted(required.difference(bundle.keys()))

    if missing:
        raise KeyError(
            "Rank1-trädets modellfil saknar: "
            + ", ".join(missing)
        )

    return bundle


def _matches_conditions(
    candidate: dict[str, Any],
    conditions: list[dict[str, Any]],
) -> bool:
    for condition in conditions:
        column = condition["column"]
        expected = condition.get("value")

        if column not in candidate:
            return False

        actual = candidate[column]

        if expected is None:
            if actual is not None and not pd.isna(actual):
                return False
            continue

        if isinstance(expected, bool):
            if _to_bool(actual) != expected:
                return False
            continue

        if _normalise_value(actual) != _normalise_value(expected):
            return False

    return True


def _match_old_environment(
    candidate: dict[str, Any],
) -> dict[str, Any]:
    registry = _load_environment_registry()

    for _, environment in registry.iterrows():
        if not _matches_conditions(
            candidate,
            environment["_parsed_conditions"],
        ):
            continue

        return {
            "rank": _safe_int(
                environment["environment_rank"],
                0,
            ),
            "depth": _safe_int(
                environment["depth"],
                0,
            ),
            "observations": _safe_int(
                environment["observations"],
                0,
            ),
            "winners": _safe_int(
                environment["winners"],
                0,
            ),
            "percent": _safe_float(
                environment["ranking_score_percent"],
                np.nan,
            ),
            "environment": str(
                environment["environment"]
            ),
        }

    return {
        "rank": 0,
        "depth": 0,
        "observations": 0,
        "winners": 0,
        "percent": np.nan,
        "environment": "INGEN MATCH",
    }


def _build_spike_profile(
    old_environment: dict[str, Any],
    race_features: dict[str, Any],
) -> str:
    return (
        "Miljö="
        + _profile_environment_bucket(
            old_environment["percent"]
        )
        + " | Tree="
        + str(old_environment["depth"])
        + " | Obs="
        + _profile_observations_bucket(
            old_environment["observations"]
        )
        + " | SpikeGap="
        + str(race_features["spike_gap_bucket"])
        + " | Spread="
        + str(race_features["spread_bucket"])
        + " | Lopptyp="
        + str(race_features["race_type"])
        + " | Röd="
        + (
            "Ja"
            if race_features["red_warning"]
            else "Nej"
        )
    )


def _predict_rank1_environment(
    race_features: dict[str, Any],
) -> dict[str, Any]:
    bundle = _load_rank1_tree_bundle()

    pipeline = bundle["pipeline"]
    features = list(bundle["features"])
    leaves = bundle["leaves"].copy()

    row = {
        feature: (
            "Unknown"
            if race_features.get(feature) is None
            or pd.isna(race_features.get(feature))
            else str(race_features.get(feature))
        )
        for feature in features
    }

    feature_frame = pd.DataFrame([row])

    transformed = pipeline[
        "preprocessor"
    ].transform(feature_frame)

    tree = pipeline["tree"]
    leaf_id = int(tree.apply(transformed)[0])

    leaf_match = leaves[
        pd.to_numeric(
            leaves["leaf_id"],
            errors="coerce",
        ).eq(leaf_id)
    ]

    if leaf_match.empty:
        raise ValueError(
            f"Rank1-trädet saknar löv {leaf_id}."
        )

    leaf = leaf_match.iloc[0]

    return {
        "leaf_id": leaf_id,
        "percent": _safe_float(
            leaf["adjusted_hit_rate_percent"],
            0.0,
        ),
        "observations": _safe_int(
            leaf["observations"],
            0,
        ),
        "winners": _safe_int(
            leaf["winners"],
            0,
        ),
        "rule": str(leaf["rule"]),
    }


def _build_race_features(
    race: dict[str, Any],
    horses: list[dict[str, Any]],
    ranked: list[dict[str, Any]],
) -> dict[str, Any]:
    metrics = get_race_metrics(ranked)
    loppbadge = get_loppbadge(metrics)

    rank1 = ranked[0]

    score_gap = (
        _safe_float(ranked[0].get("total_score"))
        - _safe_float(ranked[1].get("total_score"))
        if len(ranked) > 1
        else np.nan
    )

    spike_gap = (
        _safe_float(ranked[0].get("spike_score"))
        - _safe_float(ranked[1].get("spike_score"))
        if len(ranked) > 1
        else np.nan
    )

    spread = _safe_float(
        metrics.get("spread_1_8"),
        np.nan,
    )

    value_count = _safe_int(
        rank1.get("value_candidate_count"),
        0,
    )

    value_in_race = _to_bool(
        rank1.get("race_has_value_candidate")
    )

    red_warning = (
        value_in_race
        and not pd.isna(score_gap)
        and score_gap < 10
    )

    yellow_warning = value_in_race

    start_type = str(
        race.get(
            "start_type",
            race.get("start", "Unknown"),
        )
        or "Unknown"
    )

    race_type = str(
        loppbadge.get("label", "Öppet lopp")
    )

    features = {
        "race_type": race_type,
        "loppbadge_y": race_type,
        "spread_1_8": spread,
        "spread_bucket": _bucket_spread(spread),
        "score_gap_1_2": score_gap,
        "score_gap_bucket":
            _bucket_score_gap(score_gap),
        "spike_gap_1_2": spike_gap,
        "spike_gap_bucket":
            _bucket_spike_gap(spike_gap),
        "spike_score":
            _safe_float(rank1.get("spike_score")),
        "spike_score_bucket":
            _bucket_spike_score(
                rank1.get("spike_score")
            ),
        "spik_warning_red": red_warning,
        "spik_warning_yellow": yellow_warning,
        "red_warning": red_warning,
        "yellow_warning": yellow_warning,
        "race_has_value_candidate":
            value_in_race,
        "value_in_race": value_in_race,
        "value_candidate_count":
            value_count,
        "value_count_bucket":
            _bucket_value_count(value_count),
        "start_type": start_type,
        "distance": str(
            race.get("distance", "Unknown")
        ),
    }

    return features




def _distance_bucket_v2(value: Any) -> str:
    """
    Exact bucket definition used when the frozen Spike V2 model was trained.
    """
    distance = _safe_float(value, np.nan)

    if pd.isna(distance):
        return "Unknown"
    if distance < 1700:
        return "kort"
    if distance < 2300:
        return "medel"
    if distance < 2800:
        return "lang"
    return "extrem"


@lru_cache(maxsize=1)
def _load_spike_v2_bundle() -> dict[str, Any]:
    if not SPIKE_V2_MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Fryst Spike V2-modell saknas: {SPIKE_V2_MODEL_FILE}"
        )
    meta = dict(SPIKE_V2_META)

    if meta.get("features") != EXPECTED_SPIKE_V2_FEATURES:
        raise RuntimeError(
            "Spike V2 featurelista matchar inte den låsta D-specifikationen."
        )

    if meta.get("environment_version") != ENVIRONMENT_V2_VERSION:
        raise RuntimeError(
            "Spike V2 är kopplad till fel Environment V2-version."
        )

    model = CatBoostClassifier()
    model.load_model(str(SPIKE_V2_MODEL_FILE))

    return {
        "model": model,
        "features": list(meta["features"]),
        "categorical_features": set(meta["categorical_features"]),
        "numeric_medians": dict(meta["numeric_medians"]),
        "meta": meta,
    }


@lru_cache(maxsize=1)
def _load_rescue_v1_bundle() -> dict[str, Any]:
    if not RESCUE_V1_MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Fryst Rescue V1-modell saknas: {RESCUE_V1_MODEL_FILE}"
        )
    meta = dict(RESCUE_V1_META)

    if meta.get("features") != EXPECTED_RESCUE_V1_FEATURES:
        raise RuntimeError(
            "Rescue V1 featurelista matchar inte den låsta D-specifikationen."
        )

    if [int(x) for x in meta.get("candidate_ranks", [])] != [1, 2, 3]:
        raise RuntimeError(
            "Rescue V1 måste vara låst till rank 1-3."
        )

    if abs(_safe_float(meta.get("margin"), -1.0) - 0.05) > 1e-12:
        raise RuntimeError(
            "Rescue V1-marginalen är inte den låsta 0.05."
        )

    model = CatBoostClassifier()
    model.load_model(str(RESCUE_V1_MODEL_FILE))

    return {
        "model": model,
        "features": list(meta["features"]),
        "numeric_medians": dict(meta["numeric_medians"]),
        "margin": float(meta["margin"]),
        "meta": meta,
    }


def _gap_at(
    ranked: list[dict[str, Any]],
    column: str,
    index: int,
) -> float:
    if len(ranked) <= index:
        return np.nan

    return (
        _safe_float(ranked[0].get(column), np.nan)
        - _safe_float(ranked[index].get(column), np.nan)
    )


def _build_spike_v2_row(
    race: dict[str, Any],
    ranked: list[dict[str, Any]],
    environment_v2: dict[str, Any],
) -> dict[str, Any]:
    """
    Exact race feature construction used for the frozen BUILD90 Spike V2.
    """
    if not ranked:
        raise ValueError("Spike V2 kan inte byggas utan rankade hästar.")

    profile = environment_v2.get("profile") or {}

    if "rank1_pct" not in profile:
        raise RuntimeError(
            "Environment V2-profil saknar rank1_pct."
        )

    metrics = get_race_metrics(ranked)
    loppbadge = get_loppbadge(metrics)
    race_type = str(
        loppbadge.get(
            "label",
            race.get("race_type", "Öppet lopp"),
        )
    )

    top8 = ranked[:8]
    top8_scores = [
        _safe_float(horse.get("total_score"), np.nan)
        for horse in top8
    ]
    top8_scores = [
        value
        for value in top8_scores
        if not pd.isna(value)
    ]

    spread_1_8 = (
        max(top8_scores) - min(top8_scores)
        if len(top8_scores) > 1
        else 0.0
    )

    rank1 = ranked[0]

    return {
        "v2_environment":
            str(environment_v2.get("environment", "UT")),
        "v2_rank1_pct":
            _safe_float(profile.get("rank1_pct"), np.nan),
        "v2_observations":
            _safe_float(profile.get("observations"), 0.0),
        "spike_score":
            _safe_float(rank1.get("spike_score"), np.nan),
        "spike_gap_1_2":
            _gap_at(ranked, "spike_score", 1),
        "spike_gap_1_3":
            _gap_at(ranked, "spike_score", 2),
        "spread_1_8":
            float(spread_1_8),
        "score_gap_1_2":
            _gap_at(ranked, "total_score", 1),
        "score_gap_1_3":
            _gap_at(ranked, "total_score", 2),
        "total_score":
            _safe_float(rank1.get("total_score"), np.nan),
        "field_size":
            int(len(ranked)),
        "race_type":
            race_type,
        "start_type":
            str(
                race.get(
                    "start_type",
                    race.get("start", "Unknown"),
                )
                or "Unknown"
            ),
        "distance_bucket":
            _distance_bucket_v2(
                race.get("distance")
            ),
    }


def _predict_spike_v2_percent(
    feature_row: dict[str, Any],
) -> float:
    bundle = _load_spike_v2_bundle()

    row: dict[str, Any] = {}

    for feature in bundle["features"]:
        value = feature_row.get(feature)

        if feature in bundle["categorical_features"]:
            if value is None:
                value = "Unknown"
            else:
                try:
                    if pd.isna(value):
                        value = "Unknown"
                except Exception:
                    pass
            row[feature] = str(value)
        else:
            numeric = _safe_float(value, np.nan)
            if pd.isna(numeric):
                numeric = _safe_float(
                    bundle["numeric_medians"].get(feature),
                    0.0,
                )
            row[feature] = numeric

    frame = pd.DataFrame(
        [row],
        columns=bundle["features"],
    )

    probability = float(
        bundle["model"].predict_proba(frame)[0, 1]
    )

    # Hybrid V3 compares percentages on a 0-100 scale.
    return probability * 100.0


def _rescue_probabilities(
    ranked: list[dict[str, Any]],
) -> list[tuple[int, dict[str, Any], float]]:
    bundle = _load_rescue_v1_bundle()
    rows = []
    horses = []

    for position, horse in enumerate(
        ranked[:3],
        start=1,
    ):
        row = {}

        for feature in bundle["features"]:
            if feature == "model_rank":
                raw_value = position
            else:
                raw_value = horse.get(feature)

            numeric = _safe_float(raw_value, np.nan)

            if pd.isna(numeric):
                numeric = _safe_float(
                    bundle["numeric_medians"].get(feature),
                    0.0,
                )

            row[feature] = numeric

        rows.append(row)
        horses.append((position, horse))

    if not rows:
        return []

    frame = pd.DataFrame(
        rows,
        columns=bundle["features"],
    )

    probabilities = bundle["model"].predict_proba(frame)[:, 1]

    return [
        (
            position,
            horse,
            float(probability),
        )
        for (position, horse), probability
        in zip(horses, probabilities)
    ]


def _apply_rescue_v1(
    ranked: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    scored = _rescue_probabilities(ranked)

    if not scored:
        raise ValueError("Rescue V1 saknar kandidater.")

    rank1_position, rank1_horse, rank1_probability = scored[0]

    alternatives = [
        item
        for item in scored
        if item[0] in {2, 3}
    ]

    selected_position = rank1_position
    selected_horse = rank1_horse
    selected_probability = rank1_probability
    applied = False

    if alternatives:
        best = max(
            alternatives,
            key=lambda item: item[2],
        )

        margin = _load_rescue_v1_bundle()["margin"]

        if best[2] - rank1_probability >= margin:
            selected_position = best[0]
            selected_horse = best[1]
            selected_probability = best[2]
            applied = True

    audit = {
        "applied": applied,
        "from_rank": 1,
        "to_rank": selected_position,
        "rank1_probability": rank1_probability,
        "selected_probability": selected_probability,
        "probability_delta":
            selected_probability - rank1_probability,
        "margin":
            _load_rescue_v1_bundle()["margin"],
    }

    return selected_horse, audit


def get_hybrid_round_spikes(
    all_races: list[dict[str, Any]],
    calculate_spike_score: Callable[
        [dict[str, Any], dict[str, Any]],
        float,
    ],
    rank_horses: Callable[
        [list[dict[str, Any]]],
        list[dict[str, Any]],
    ],
    apply_value_flags: Callable[
        [list[dict[str, Any]], dict[str, Any]],
        list[dict[str, Any]],
    ],
) -> list[dict[str, Any]]:
    """
    LOCKED D:
    1) Current ranking/SpikeScore is left untouched.
    2) Environment V2 classifies every race.
    3) Frozen Spike V2 scores every race.
    4) Hybrid selects three unique races by the existing V3 ordering.
    5) Frozen Rescue V1 may switch rank1 to rank2/3 inside those races.
    """
    environment_bundle = load_environment_model()

    if environment_bundle.get("version") != ENVIRONMENT_V2_VERSION:
        raise RuntimeError(
            "Fel Environment V2-version för Hybrid D. "
            f"Förväntad={ENVIRONMENT_V2_VERSION}, "
            f"hittad={environment_bundle.get('version')}"
        )

    # Force-load and validate locked models before touching the round.
    _load_spike_v2_bundle()
    _load_rescue_v1_bundle()

    candidates: list[dict[str, Any]] = []
    race_contexts: dict[str, dict[str, Any]] = {}

    for race_data in all_races:
        race = race_data["race"]
        horses = race_data["horses"]

        if not horses:
            continue

        race_for_badges = dict(race)
        race_for_badges["horses"] = horses

        for horse in horses:
            horse["badges"] = [
                badge
                for badge in horse.get("badges", [])
                if badge not in {
                    "🟩 Toppspik",
                    "🟦 Spik",
                }
            ]

            horse["spike_score"] = (
                calculate_spike_score(
                    horse,
                    race_for_badges,
                )
            )

        ranked = rank_horses(horses)

        apply_value_flags(
            horses,
            race_for_badges,
        )

        if not ranked:
            continue

        rank1 = ranked[0]

        # IMPORTANT LIVE ORDER:
        # Spike V2/D must use the Environment V2 that exists AFTER
        # V8X final-ranking corrections. The frozen base rank/score features
        # remain on their original TotalScore/model-rank definition.
        final_order = sorted(
            horses,
            key=lambda h: _safe_int(
                h.get("_final_rank", h.get("final_rank", 999)),
                999,
            ),
        )

        final_environment_name = race.get("final_environment_v2")
        final_environment_profile = race.get("final_environment_profile_v2")
        final_environment_leaf = race.get("final_environment_leaf_v2")

        if (
            final_environment_name
            and final_environment_name != "UT"
            and isinstance(final_environment_profile, dict)
        ):
            environment_v2 = {
                "environment": final_environment_name,
                "leaf_id": final_environment_leaf,
                "profile": final_environment_profile,
                "version": environment_bundle.get("version", ""),
            }
        else:
            environment_v2 = classify_environment(
                {
                    "race": race,
                    "horses": horses,
                },
                final_order,
                stage="final",
            )

        environment_profile = (
            environment_v2.get("profile")
            or {}
        )

        if "rank1_pct" not in environment_profile:
            raise RuntimeError(
                "Environment V2-profil saknar rank1_pct "
                f"för {race.get('track', '')} "
                f"avd {race.get('race_no', '')}."
            )

        spike_v2_features = _build_spike_v2_row(
            race=race,
            ranked=ranked,
            environment_v2=environment_v2,
        )

        spike_v2_percent = _predict_spike_v2_percent(
            spike_v2_features
        )

        environment_percent = _safe_float(
            environment_profile.get("rank1_pct"),
            0.0,
        )

        environment_observations = _safe_int(
            environment_profile.get("observations"),
            0,
        )

        race_no = _safe_int(
            race.get("race_no"),
            999,
        )

        race_key = (
            str(race.get("track", ""))
            + "|"
            + str(race_no)
        )

        # Audit fields remain on rank1 even if Rescue later changes horse.
        rank1["hybrid_d_version"] = HYBRID_D_VERSION
        rank1["hybrid_spike_profile"] = (
            "SPIKE_V2_BUILD90_FROZEN_CANDIDATE"
        )
        rank1["hybrid_spike_percent"] = spike_v2_percent
        rank1[
            "hybrid_spike_profile_observations"
        ] = environment_observations
        rank1[
            "hybrid_environment_percent"
        ] = environment_percent
        rank1[
            "hybrid_environment_observations"
        ] = environment_observations
        rank1[
            "hybrid_environment_leaf_id"
        ] = environment_v2.get("leaf_id")
        rank1[
            "hybrid_environment_rule"
        ] = (
            "Environment V2 | "
            + str(environment_v2.get("environment", "UT"))
        )
        rank1["hybrid_environment_v2"] = (
            environment_v2.get("environment")
        )
        rank1["hybrid_environment_version_v2"] = (
            environment_v2.get("version")
        )

        race_contexts[race_key] = {
            "race": race,
            "ranked": ranked,
            "rank1": rank1,
            "environment_v2": environment_v2,
            "spike_v2_features": spike_v2_features,
            "spike_v2_percent": spike_v2_percent,
            "environment_percent": environment_percent,
            "environment_observations": environment_observations,
        }

        common = {
            "horse": rank1,
            "race_key": race_key,
            "race_no": race_no,
            "observations": environment_observations,
            "spike_score":
                _safe_float(rank1.get("spike_score")),
            "total_score":
                _safe_float(rank1.get("total_score")),
        }

        candidates.append(
            {
                **common,
                "engine": "SPIKE",
                "percent": spike_v2_percent,
            }
        )

        candidates.append(
            {
                **common,
                "engine": "ENVIRONMENT",
                "percent": environment_percent,
            }
        )

    debug_dir = ROOT / "output" / "live_hybrid_debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    candidate_rows = []

    for candidate in candidates:
        context = race_contexts[candidate["race_key"]]
        horse = candidate["horse"]

        candidate_rows.append(
            {
                "Avd": candidate["race_no"],
                "Häst": horse.get(
                    "horse",
                    horse.get("name", ""),
                ),
                "Motor": candidate["engine"],
                "Kandidat %": candidate["percent"],
                "Observationer": candidate["observations"],
                "Spike V2 %": context["spike_v2_percent"],
                "Environment V2 %":
                    context["environment_percent"],
                "Environment V2":
                    context["environment_v2"].get("environment"),
                "Environment leaf":
                    context["environment_v2"].get("leaf_id"),
                "Totalrank": horse.get(
                    "_model_rank_live",
                    horse.get("model_rank"),
                ),
                "Score": horse.get("total_score"),
                "SpikeScore": horse.get("spike_score"),
                "Spel %": horse.get("percent"),
                "Hybrid D version": HYBRID_D_VERSION,
            }
        )

    pd.DataFrame(candidate_rows).to_csv(
        debug_dir / "latest_round_all_candidates.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # Exact Hybrid V3 ordering, now with Spike V2 / Environment V2 percentages.
    ordered = sorted(
        candidates,
        key=lambda candidate: (
            -candidate["percent"],
            -candidate["observations"],
            -candidate["spike_score"],
            -candidate["total_score"],
            candidate["race_no"],
            candidate["engine"],
        ),
    )

    selected_candidates: list[dict[str, Any]] = []
    used_races: set[str] = set()

    for candidate in ordered:
        if candidate["race_key"] in used_races:
            continue

        used_races.add(candidate["race_key"])
        selected_candidates.append(candidate)

        if len(selected_candidates) == TOP_N:
            break

    if len(selected_candidates) != TOP_N:
        raise RuntimeError(
            f"Hybrid D gav endast {len(selected_candidates)} unika lopp."
        )

    selected: list[dict[str, Any]] = []
    selected_debug_rows = []

    for position, candidate in enumerate(
        selected_candidates,
        start=1,
    ):
        context = race_contexts[candidate["race_key"]]

        final_horse, rescue = _apply_rescue_v1(
            context["ranked"]
        )

        # Copy race-level Hybrid fields to the rescued horse.
        final_horse["hybrid_d_version"] = HYBRID_D_VERSION
        final_horse["hybrid_selected_engine"] = (
            candidate["engine"]
        )
        final_horse["hybrid_selected_percent"] = (
            candidate["percent"]
        )
        final_horse[
            "hybrid_selected_observations"
        ] = candidate["observations"]
        final_horse["hybrid_spike_position"] = position

        final_horse["hybrid_spike_profile"] = (
            "SPIKE_V2_BUILD90_FROZEN_CANDIDATE"
        )
        final_horse["hybrid_spike_percent"] = (
            context["spike_v2_percent"]
        )
        final_horse[
            "hybrid_spike_profile_observations"
        ] = context["environment_observations"]
        final_horse[
            "hybrid_environment_percent"
        ] = context["environment_percent"]
        final_horse[
            "hybrid_environment_observations"
        ] = context["environment_observations"]
        final_horse[
            "hybrid_environment_leaf_id"
        ] = context["environment_v2"].get("leaf_id")
        final_horse[
            "hybrid_environment_rule"
        ] = (
            "Environment V2 | "
            + str(
                context["environment_v2"].get(
                    "environment",
                    "UT",
                )
            )
        )
        final_horse["hybrid_environment_v2"] = (
            context["environment_v2"].get("environment")
        )
        final_horse[
            "hybrid_environment_version_v2"
        ] = context["environment_v2"].get("version")

        final_horse["hybrid_rescue_applied"] = (
            bool(rescue["applied"])
        )
        final_horse["hybrid_rescue_from_rank"] = (
            int(rescue["from_rank"])
        )
        final_horse["hybrid_rescue_to_rank"] = (
            int(rescue["to_rank"])
        )
        final_horse[
            "hybrid_rescue_rank1_probability"
        ] = float(rescue["rank1_probability"])
        final_horse[
            "hybrid_rescue_selected_probability"
        ] = float(rescue["selected_probability"])
        final_horse[
            "hybrid_rescue_probability_delta"
        ] = float(rescue["probability_delta"])
        final_horse["hybrid_rescue_margin"] = (
            float(rescue["margin"])
        )
        final_horse["hybrid_rescue_model"] = (
            "RESCUE_V1_BUILD90_FROZEN"
        )

        if position <= 2:
            final_horse.setdefault(
                "badges",
                [],
            ).append("🟩 Toppspik")
            final_horse["spike_badge_type"] = "Toppspik"
        else:
            final_horse.setdefault(
                "badges",
                [],
            ).append("🟦 Spik")
            final_horse["spike_badge_type"] = "Spik"

        selected.append(final_horse)

        selected_debug_rows.append(
            {
                "Avd": candidate["race_no"],
                "Häst": final_horse.get(
                    "horse",
                    final_horse.get("name", ""),
                ),
                "Motor": candidate["engine"],
                "Hybrid %": candidate["percent"],
                "Spike V2 %": context["spike_v2_percent"],
                "Environment V2 %":
                    context["environment_percent"],
                "Environment V2":
                    context["environment_v2"].get("environment"),
                "Rescue": bool(rescue["applied"]),
                "Rescue från rank": rescue["from_rank"],
                "Rescue till rank": rescue["to_rank"],
                "Rescue rank1 p": rescue["rank1_probability"],
                "Rescue vald p": rescue["selected_probability"],
                "Rescue delta": rescue["probability_delta"],
                "Score": final_horse.get("total_score"),
                "SpikeScore": final_horse.get("spike_score"),
                "Spel %": final_horse.get("percent"),
                "Hybrid D version": HYBRID_D_VERSION,
            }
        )

    pd.DataFrame(selected_debug_rows).to_csv(
        debug_dir / "latest_round_selected.csv",
        index=False,
        encoding="utf-8-sig",
    )

    return selected
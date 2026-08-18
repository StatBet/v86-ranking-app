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

from badge_rules import get_loppbadge, get_race_metrics


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
    candidates: list[dict[str, Any]] = []
    spike_profiles = _load_spike_profiles()

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

        # Hybrid V3 är låst till Total Sum-rank 1.
        rank1 = ranked[0]

        race_features = _build_race_features(
            race=race,
            horses=horses,
            ranked=ranked,
        )

        old_environment = _match_old_environment(
            race_features
        )

        spike_profile = _build_spike_profile(
            old_environment=old_environment,
            race_features=race_features,
        )

        spike_profile_data = spike_profiles.get(
            spike_profile,
            {
                "percent": GLOBAL_SPIKE_PERCENT,
                "observations": 0,
                "winners": 0,
            },
        )

        rank1_environment = (
            _predict_rank1_environment(
                race_features
            )
        )

        rank1["hybrid_spike_profile"] = (
            spike_profile
        )
        rank1["hybrid_spike_percent"] = (
            spike_profile_data["percent"]
        )
        rank1[
            "hybrid_spike_profile_observations"
        ] = spike_profile_data["observations"]

        rank1[
            "hybrid_environment_percent"
        ] = rank1_environment["percent"]
        rank1[
            "hybrid_environment_observations"
        ] = rank1_environment["observations"]
        rank1[
            "hybrid_environment_leaf_id"
        ] = rank1_environment["leaf_id"]
        rank1[
            "hybrid_environment_rule"
        ] = rank1_environment["rule"]

        race_no = _safe_int(
            race.get("race_no"),
            999,
        )

        candidates.append(
            {
                "horse": rank1,
                "race_key": (
                    str(race.get("track", ""))
                    + "|"
                    + str(race_no)
                ),
                "race_no": race_no,
                "engine": "SPIKE",
                "percent":
                    spike_profile_data["percent"],
                "observations":
                    spike_profile_data["observations"],
                "spike_score":
                    _safe_float(
                        rank1.get("spike_score")
                    ),
                "total_score":
                    _safe_float(
                        rank1.get("total_score")
                    ),
            }
        )

        candidates.append(
            {
                "horse": rank1,
                "race_key": (
                    str(race.get("track", ""))
                    + "|"
                    + str(race_no)
                ),
                "race_no": race_no,
                "engine": "ENVIRONMENT",
                "percent":
                    rank1_environment["percent"],
                "observations":
                    rank1_environment[
                        "observations"
                    ],
                "spike_score":
                    _safe_float(
                        rank1.get("spike_score")
                    ),
                "total_score":
                    _safe_float(
                        rank1.get("total_score")
                    ),
            }
        )

    # -------------------------------------------------
    # DEBUG: ALLA KANDIDATER FÖRE TOPP 3
    # -------------------------------------------------

    debug_dir = ROOT / "output" / "live_hybrid_debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    candidate_rows = []

    for candidate in candidates:
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
                "Spike %": horse.get("hybrid_spike_percent"),
                "Miljö %": horse.get(
                    "hybrid_environment_percent"
                ),
                "Totalrank": horse.get(
                    "_model_rank_live",
                    horse.get("model_rank"),
                ),
                "Score": horse.get("total_score"),
                "SpikeScore": horse.get("spike_score"),
                "Spel %": horse.get("percent"),
                "Leaf": horse.get(
                    "hybrid_environment_leaf_id"
                ),
                "Spikeprofil": horse.get(
                    "hybrid_spike_profile"
                ),
            }
        )

    candidate_debug = pd.DataFrame(candidate_rows)

    #candidate_debug = candidate_debug.sort_values(
        #[
           # "Kandidat %",
           # "Observationer",
            #"SpikeScore",
           # "Score",
            #"Avd",
            #"Motor",
        #],
        #ascending=[
            #False,
           # False,
            #False,
           # False,
            #True,
            #True,
       # ],
   # )

    candidate_debug.to_csv(
        debug_dir / "latest_round_all_candidates.csv",
        index=False,
        encoding="utf-8-sig",
    )

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

    selected: list[dict[str, Any]] = []
    used_races: set[str] = set()

    for candidate in ordered:
        if candidate["race_key"] in used_races:
            continue

        used_races.add(candidate["race_key"])

        horse = candidate["horse"]
        horse["hybrid_selected_engine"] = (
            candidate["engine"]
        )
        horse["hybrid_selected_percent"] = (
            candidate["percent"]
        )
        horse[
            "hybrid_selected_observations"
        ] = candidate["observations"]
        horse["hybrid_spike_position"] = (
            len(selected) + 1
        )

        selected.append(horse)

        if len(selected) == TOP_N:
            break

    for index, horse in enumerate(
        selected,
        start=1,
    ):
        if index <= 2:
            horse.setdefault(
                "badges",
                [],
            ).append("🟩 Toppspik")
            horse["spike_badge_type"] = (
                "Toppspik"
            )
        else:
            horse.setdefault(
                "badges",
                [],
            ).append("🟦 Spik")
            horse["spike_badge_type"] = "Spik"

    # -------------------------------------------------
    # DEBUG EXPORT
    # -------------------------------------------------

    debug_dir = ROOT / "output" / "live_hybrid_debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    debug_rows = []

    for horse in selected:
        debug_rows.append(
            {
                "Avd": horse.get("race_no"),
                "Häst": horse.get("horse", horse.get("name")),
                "Motor": horse.get("hybrid_selected_engine"),
                "Hybrid %": horse.get("hybrid_selected_percent"),
                "Spike %": horse.get("hybrid_spike_percent"),
                "Miljö %": horse.get("hybrid_environment_percent"),
                "Rank": horse.get("_model_rank_live", horse.get("model_rank")),
                "Score": horse.get("total_score"),
                "SpikeScore": horse.get("spike_score"),
                "Spel %": horse.get("percent"),
            }
        )

    pd.DataFrame(debug_rows).to_csv(
        debug_dir / "latest_round_selected.csv",
        index=False,
        encoding="utf-8-sig",
    )

    return selected
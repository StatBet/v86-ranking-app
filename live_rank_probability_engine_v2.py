# live_rank_probability_engine_v2.py
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent

PROFILE_FILE = (
    ROOT / "output" / "weighted_leaf_rank_profiles" / "weighted_leaf_rank_profiles.csv"
)

CLASSIFIED_LEAFS = {4, 5, 8, 10, 19, 20}
HYBRID_THRESHOLD = 42.25
HYBRID_BASELINE = 27.16


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or pd.isna(value):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


@lru_cache(maxsize=1)
def load_rank_probability_profiles() -> dict[str, dict[str, Any]]:
    frame = pd.read_csv(PROFILE_FILE)
    return {
        str(row["profile_key"]): row.to_dict()
        for _, row in frame.iterrows()
    }


def profile_key_for_leaf(leaf_id: Any) -> str:
    leaf = _safe_int(leaf_id, -1)
    return f"LEAF_{leaf}" if leaf in CLASSIFIED_LEAFS else "GLOBAL"


def assign_rank_probabilities(
    horses: list[dict[str, Any]],
    leaf_id: Any,
    hybrid_rank1_percent: Any,
) -> dict[str, Any]:

    if not horses:
        return {
            "horses": horses,
            "profile_key": profile_key_for_leaf(leaf_id),
            "total_probability": 0.0,
        }

    profiles = load_rank_probability_profiles()
    profile_key = profile_key_for_leaf(leaf_id)
    profile = profiles[profile_key]

    ranked = sorted(
        horses,
        key=lambda h: (
            _safe_int(
                h.get("_model_rank_live", h.get("model_rank", h.get("display_rank"))),
                999,
            ),
            -_safe_float(h.get("total_score")),
        ),
    )

    raw_rank1 = _safe_float(hybrid_rank1_percent)
    rank1_percent = (
        HYBRID_BASELINE
        if raw_rank1 < HYBRID_THRESHOLD
        else raw_rank1
    )

    remaining = 100.0 - rank1_percent

    field_size = len(ranked)

    rank2_plus_total = 0.0

    if field_size >= 2:
        rank2_plus_total += _safe_float(
            profile["rank_2_final_percent"]
        )

    if field_size >= 3:
        rank2_plus_total += _safe_float(
            profile["rank_3_final_percent"]
        )

    if field_size >= 4:
        rank2_plus_total += _safe_float(
            profile["rank_4_final_percent"]
        )

    if field_size >= 5:
        rank2_plus_total += _safe_float(
            profile["rank_5_final_percent"]
        )

    if field_size >= 7:
        rank2_plus_total += _safe_float(
            profile["rank_6_7_pool_percent"]
        )
    elif field_size == 6:
        rank2_plus_total += _safe_float(
            profile["rank_6_7_each_percent"]
        )

    if field_size >= 9:
        rank2_plus_total += _safe_float(
            profile["rank_8_9_pool_percent"]
        )
    elif field_size == 8:
        rank2_plus_total += _safe_float(
            profile["rank_8_9_each_percent"]
        )

    if field_size >= 10:
        rank2_plus_total += _safe_float(
            profile["rank_10_plus_pool_percent"]
        )

    scale = remaining / rank2_plus_total if rank2_plus_total else 1.0

    rank10_count = sum(
        1
        for h in ranked
        if _safe_int(
            h.get("_model_rank_live", h.get("model_rank", h.get("display_rank"))),
            999,
        ) >= 10
    )

    rank10_each = (
        _safe_float(profile["rank_10_plus_pool_percent"]) * scale / rank10_count
        if rank10_count else 0.0
    )

    mapping = {
        2: "rank_2_final_percent",
        3: "rank_3_final_percent",
        4: "rank_4_final_percent",
        5: "rank_5_final_percent",
    }

    for fallback_rank, horse in enumerate(ranked, start=1):
        rank = _safe_int(
            horse.get("_model_rank_live", horse.get("model_rank", horse.get("display_rank"))),
            fallback_rank,
        )

        if rank == 1:
            prob = rank1_percent
            src = "HYBRID"
        elif rank in mapping:
            prob = _safe_float(profile[mapping[rank]]) * scale
            src = profile_key
        elif rank in (6, 7):
            prob = _safe_float(profile["rank_6_7_each_percent"]) * scale
            src = profile_key
        elif rank in (8, 9):
            prob = _safe_float(profile["rank_8_9_each_percent"]) * scale
            src = profile_key
        else:
            prob = rank10_each
            src = profile_key

        horse["rank_probability_percent"] = round(prob, 4)
        horse["rank_probability_source"] = src
        horse["rank_probability_profile"] = profile_key

    total = sum(_safe_float(h["rank_probability_percent"]) for h in ranked)

    return {
        "horses": ranked,
        "profile_key": profile_key,
        "leaf_id": _safe_int(leaf_id, -1),
        "hybrid_rank1_percent": rank1_percent,
        "total_probability": round(total, 4),
    }
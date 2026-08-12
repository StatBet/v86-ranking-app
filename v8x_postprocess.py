from __future__ import annotations

"""
V8X final post-processing layer.

Important design rule:
- The base score model, Spike model, Hybrid engine and frozen Skräll engine run first.
- This module NEVER changes total_score or spike_score.
- It creates the final ranking order from the frozen Start Points / EPS rules.
- It then reduces the frozen Skräll candidate pool to one Main pick per round,
  adds the locked broad Rescue 2 candidates from the old candidate pool,
  and finally keeps the existing tightly controlled external Rescue.

Frozen rule precedence:
1. Start points top-3 corrections (most cautious / least data)
2. EPS top-3 corrections (EPS has precedence over start points)
3. Rank 4-5 double signal (Spike top3 + EPS top2) -> Rank 3
4. Leaf 4/5/10 Rank 6+ rescues:
   - same horse EPS + Spike -> Rank 3
   - otherwise EPS rescue has precedence for Rank 5
   - Spike rescue is used only if no EPS rescue exists
5. Skräll final selection uses BASE model rank, not corrected final rank.
6. Locked Rescue 2 only ADDS removed old Skräll candidates:
   max_parameters >= 3, dna_score >= 500, dna_matches >= 15, percent <= 8.
   It never replaces Main, never downgrades Premium, and has no max-1 cap.
"""

from typing import Iterable

ACTIVE_RESCUE_LEAVES = {4, 5, 10}
ACTIVE_SKRALL_LEAVES = {4, 5, 8, 10, 19, 20}

SKRALL_BADGES = {
    "⭐ SKRÄLL PREMIUM",
    "💥 SKRÄLLKANDIDAT",
    "💥 SKRÄLL",
    "🛟 SKRÄLL RESCUE",
}


def _float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _percent(horse):
    return _float(horse.get("percent", 0), 0.0)


def _name(horse):
    return str(horse.get("horse", horse.get("name", ""))).strip()


def _rank_ordinal(horses: list[dict], key, reverse=True) -> dict[int, int]:
    """Deterministic ordinal rank, matching the project's positional ranks."""
    decorated = list(enumerate(horses))
    decorated.sort(
        key=lambda item: (
            _float(key(item[1]), 0.0),
            -item[0] if reverse else item[0],
        ),
        reverse=reverse,
    )
    return {idx: rank for rank, (idx, _) in enumerate(decorated, start=1)}


def _move_to(order: list[dict], horse: dict, position: int) -> None:
    """Move horse to 1-indexed position, preserving relative order of others."""
    if horse not in order:
        return
    order.remove(horse)
    pos = max(0, min(position - 1, len(order)))
    order.insert(pos, horse)


def _race_leaf_id(race_data: dict, base_order: list[dict]) -> int | None:
    race = race_data.get("race", {})
    for source in (
        race,
        base_order[0] if base_order else {},
    ):
        for key in (
            "hybrid_environment_leaf_id",
            "rank1_environment_leaf_id",
            "leaf_id",
        ):
            value = source.get(key)
            if value not in (None, ""):
                try:
                    return int(float(value))
                except (TypeError, ValueError):
                    pass
    # Historical / audit data can carry leaf_id on every horse.
    for horse in base_order:
        value = horse.get("leaf_id")
        if value not in (None, ""):
            try:
                return int(float(value))
            except (TypeError, ValueError):
                pass
    return None


def _annotate_race_features(race_data: dict) -> tuple[list[dict], int | None]:
    horses = race_data.get("horses", [])
    base_order = sorted(
        horses,
        key=lambda h: _float(h.get("total_score", 0)),
        reverse=True,
    )

    # Stable base rank.
    for rank, horse in enumerate(base_order, start=1):
        horse["base_model_rank"] = rank
        horse["_base_model_rank"] = rank
        horse["_base_total_score"] = _float(horse.get("total_score", 0))

        starts = _float(horse.get("starts", 0))
        prize = _float(horse.get("prize_money", 0))
        horse["eps_value"] = (prize / starts) if starts > 0 else 0.0

        horse.setdefault("_final_rank_reasons", [])
        if not isinstance(horse["_final_rank_reasons"], list):
            horse["_final_rank_reasons"] = []
        else:
            horse["_final_rank_reasons"].clear()

    # Ordinal feature ranks within the race.
    index_of = {id(h): i for i, h in enumerate(base_order)}

    def annotate_rank(field, source, reverse=True):
        # deterministic sort from base order
        ordered = sorted(
            base_order,
            key=lambda h: (
                _float(h.get(source, 0)),
                -index_of[id(h)] if reverse else index_of[id(h)],
            ),
            reverse=reverse,
        )
        for rank, horse in enumerate(ordered, start=1):
            horse[field] = rank

    annotate_rank("start_points_rank", "start_points", True)
    annotate_rank("eps_rank", "eps_value", True)
    annotate_rank("spike_rank", "spike_score", True)

    leaf_id = _race_leaf_id(race_data, base_order)
    for horse in base_order:
        horse["_v8x_race_leaf_id"] = leaf_id

    return base_order, leaf_id


def _apply_ranking_rules_to_race(race_data: dict) -> None:
    base_order, leaf_id = _annotate_race_features(race_data)
    if not base_order:
        return

    order = list(base_order)
    base_top3 = base_order[:3]

    score1 = _float(base_order[0].get("total_score", 0))
    score3 = _float(base_order[2].get("total_score", 0)) if len(base_order) >= 3 else score1
    gap_1_3 = score1 - score3

    # Start points were added later to the parser/historical material.
    # Zero is also the missing-value fallback, so never fire the module when
    # the full base top3 does not carry positive parsed start points.
    has_start_points_top3 = (
        len(base_top3) >= 3
        and all(_float(h.get("start_points", 0)) > 0 for h in base_top3)
    )

    # ---------------------------------------------------------
    # START POINTS – cautious, then EPS may override.
    # ---------------------------------------------------------
    if has_start_points_top3 and gap_1_3 <= 20:
        rank1 = order[0]
        if (
            _int(rank1.get("start_points_rank", 999), 999) >= 3
            and _percent(rank1) < 25
        ):
            best = min(base_top3, key=lambda h: _int(h.get("start_points_rank", 999), 999))
            if best is not rank1:
                _move_to(order, best, 1)
                best["_final_rank_reasons"].append("Startpoäng Rank1")

    if has_start_points_top3 and len(order) >= 3 and gap_1_3 <= 35:
        # Keep the decided Rank1; only sort current Rank2/3 by start points.
        pair = order[1:3]
        pair.sort(key=lambda h: _int(h.get("start_points_rank", 999), 999))
        order[1:3] = pair
        for h in pair:
            h["_final_rank_reasons"].append("Startpoäng Rank2/3")

    # ---------------------------------------------------------
    # EPS – has precedence over start points.
    # ---------------------------------------------------------
    if len(order) >= 3 and gap_1_3 <= 35:
        rank1 = order[0]
        top3_now = order[:3]
        best_eps = min(top3_now, key=lambda h: _int(h.get("eps_rank", 999), 999))
        if _percent(rank1) < 20 and best_eps is not rank1:
            _move_to(order, best_eps, 1)
            best_eps["_final_rank_reasons"].append("EPS Rank1")

    if len(order) >= 3 and gap_1_3 <= 20:
        pair = order[1:3]
        pair.sort(key=lambda h: _int(h.get("eps_rank", 999), 999))
        order[1:3] = pair
        for h in pair:
            h["_final_rank_reasons"].append("EPS Rank2/3")

    # ---------------------------------------------------------
    # Rank 4-5 -> Rank 3: double requirement only.
    # Frozen rule = Spike top3 AND EPS top2.
    # ---------------------------------------------------------
    rank45 = [
        h for h in base_order
        if _int(h.get("base_model_rank", 999), 999) in (4, 5)
        and _int(h.get("spike_rank", 999), 999) <= 3
        and _int(h.get("eps_rank", 999), 999) <= 2
    ]
    if rank45:
        chosen = min(
            rank45,
            key=lambda h: (
                _int(h.get("eps_rank", 999), 999),
                _int(h.get("spike_rank", 999), 999),
                -_float(h.get("total_score", 0)),
            ),
        )
        _move_to(order, chosen, 3)
        chosen["_final_rank_reasons"].append("Rank4/5 dubbel Spike+EPS → Rank3")

    # ---------------------------------------------------------
    # Rank 6+ rescue in Leaf 4/5/10, >=11%.
    # ---------------------------------------------------------
    if leaf_id in ACTIVE_RESCUE_LEAVES:
        eligible = [
            h for h in base_order
            if _int(h.get("base_model_rank", 999), 999) >= 6
            and _percent(h) >= 11
        ]

        eps_eligible = [h for h in eligible if _int(h.get("eps_rank", 999), 999) <= 4]
        spike_eligible = [h for h in eligible if _int(h.get("spike_rank", 999), 999) <= 3]

        eps_candidate = (
            min(
                eps_eligible,
                key=lambda h: (
                    _int(h.get("eps_rank", 999), 999),
                    -_float(h.get("eps_value", 0)),
                    -_float(h.get("total_score", 0)),
                ),
            )
            if eps_eligible else None
        )
        spike_candidate = (
            min(
                spike_eligible,
                key=lambda h: (
                    _int(h.get("spike_rank", 999), 999),
                    -_float(h.get("spike_score", 0)),
                    -_float(h.get("total_score", 0)),
                ),
            )
            if spike_eligible else None
        )

        if eps_candidate is not None and eps_candidate is spike_candidate:
            # Strongest measured rescue (10/39 = 25.6%) gets Rank3 priority.
            _move_to(order, eps_candidate, 3)
            eps_candidate["_final_rank_reasons"].append("Dubbel Rescue EPS+Spike → Rank3")
            eps_candidate["double_rescue"] = True
            eps_candidate["eps_rescue"] = True
            eps_candidate["spike_rescue"] = True
        elif eps_candidate is not None:
            # EPS has precedence when separate rescue candidates conflict.
            _move_to(order, eps_candidate, 5)
            eps_candidate["_final_rank_reasons"].append("EPS Rescue → Rank5")
            eps_candidate["eps_rescue"] = True
        elif spike_candidate is not None:
            _move_to(order, spike_candidate, 5)
            spike_candidate["_final_rank_reasons"].append("Spike Rescue → Rank5")
            spike_candidate["spike_rescue"] = True

    # Final physical order and rank fields.
    race_data["horses"] = order
    for rank, horse in enumerate(order, start=1):
        horse["_final_rank"] = rank
        horse["final_rank"] = rank
        # IMPORTANT: keep model_rank/_model_rank_live on the original score rank.
        # Hybrid/probability/legacy badges were trained on that rank and must not be
        # silently redefined by this presentation/output post-process layer.
        horse["final_rank_reason"] = " | ".join(horse.get("_final_rank_reasons", []))


def _clean_skrall_badges(horse: dict) -> list:
    badges = horse.get("badges", [])
    if badges is None:
        badges = []
    elif isinstance(badges, str):
        badges = [badges] if badges.strip() else []
    else:
        badges = list(badges)
    badges = [b for b in badges if b not in SKRALL_BADGES]
    horse["badges"] = badges
    return badges


def _apply_final_skrall_selection(processed_races: list[dict]) -> None:
    """
    Frozen final Skräll architecture:
    - original frozen engine remains the candidate generator
    - choose exactly one Main candidate per round when candidates exist
    - Premium always has first priority for Main
    - locked Rescue 2 adds every removed old candidate satisfying:
      max_parameters >= 3, dna_score >= 500, dna_matches >= 15, percent <= 8
    - there is intentionally no max-1-per-round cap
    - Premium status/badge is never downgraded
    - existing external Rescue remains unchanged and can coexist with Rescue 2
    """
    all_horses: list[dict] = []
    original_candidates: list[dict] = []

    for race_data in processed_races:
        for horse in race_data.get("horses", []):
            _clean_skrall_badges(horse)
            horse["skrall_selected"] = False
            horse["skrall_main"] = False
            horse["skrall_rescue"] = False
            horse["skrall_rescue2"] = False
            all_horses.append(horse)
            if bool(horse.get("skrall_candidate", False)):
                original_candidates.append(horse)

    if not original_candidates:
        return

    # Premium > form > BASE model rank > spike > total.
    main = sorted(
        original_candidates,
        key=lambda h: (
            -int(bool(h.get("skrall_premium", False))),
            -_float(h.get("form_score", 0)),
            _int(h.get("base_model_rank", 999), 999),
            -_float(h.get("spike_score", 0)),
            -_float(h.get("total_score", 0)),
        ),
    )[0]

    main["skrall_selected"] = True
    main["skrall_main"] = True
    main_badges = main["badges"]
    if bool(main.get("skrall_premium", False)):
        main_badges.append("⭐ SKRÄLL PREMIUM")
    else:
        main_badges.append("💥 SKRÄLL")

    # Locked broad Rescue 2. Purely additive; Main is never replaced.
    rescue2_pool = [
        h for h in original_candidates
        if h is not main
        and _int(h.get("skrall_max_parameters", 0), 0) >= 3
        and _float(h.get("skrall_dna_score", 0), 0.0) >= 500
        and _int(h.get("skrall_dna_matches", 0), 0) >= 15
        and 0 <= _percent(h) <= 8
    ]

    for rescue2 in rescue2_pool:
        rescue2["skrall_selected"] = True
        rescue2["skrall_rescue2"] = True

        if bool(rescue2.get("skrall_premium", False)):
            rescue2["badges"].append("⭐ SKRÄLL PREMIUM")
        else:
            rescue2["badges"].append("💥 SKRÄLL")

    # Existing external Rescue remains exactly as before.
    if not (
        _int(main.get("base_model_rank", 999), 999) <= 3
        and _float(main.get("form_score", 0)) <= 20
    ):
        return

    original_ids = {id(h) for h in original_candidates}
    rescue_pool = [
        h for h in all_horses
        if id(h) not in original_ids
        and 0 <= _percent(h) <= 9
        and _int(h.get("_v8x_race_leaf_id", -1), -1) in ACTIVE_SKRALL_LEAVES
    ]

    if not rescue_pool:
        return

    # Important: first choose the best remaining horse exactly as in the
    # validation. latest_start_score is a GUARD on that chosen horse; if it
    # fails, we do not fall through to a weaker alternative.
    rescue = sorted(
        rescue_pool,
        key=lambda h: (
            _int(h.get("base_model_rank", 999), 999),
            -_float(h.get("total_score", 0)),
            -_float(h.get("spike_score", 0)),
        ),
    )[0]

    if _float(rescue.get("latest_start_score", 0)) < 6:
        return

    rescue["skrall_selected"] = True
    rescue["skrall_rescue"] = True
    rescue["badges"].append("🛟 SKRÄLL RESCUE")


def apply_v8x_postprocess(processed_races: list[dict]) -> list[dict]:
    """Apply all frozen final-ranking corrections + final Skräll selection."""
    for race_data in processed_races:
        _apply_ranking_rules_to_race(race_data)

    _apply_final_skrall_selection(processed_races)
    return processed_races
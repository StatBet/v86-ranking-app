from __future__ import annotations

"""
V8X final post-processing layer.

Important design rule:
- The base score model, Spike model, Hybrid engine and frozen SkrÃ¤ll engine run first.
- This module NEVER changes total_score or spike_score.
- It creates the final ranking order from the frozen Start Points / EPS rules.
- It then applies the officially frozen 06/79 candidate bank.
- If 06/79 are empty after NO PICK, BRED-ENV A / DIRECT-B run after Final Environment V2.
- Legacy Premium/Track final-selection flags are cleared; final variants are 06/79/BRED-ENV A/DIRECT-B.

Frozen rule precedence:
1. Start points top-3 corrections (most cautious / least data)
2. EPS top-3 corrections (EPS has precedence over start points)
3. Rank 4-5 double signal (Spike top3 + EPS top2) -> Rank 3
4. Leaf 4/5/10 Rank 6+ rescues:
   - same horse EPS + Spike -> Rank 3
   - otherwise EPS rescue has precedence for Rank 5
   - Spike rescue is used only if no EPS rescue exists
5. SkrÃ¤ll final selection uses BASE model rank, not corrected final rank.
6. Final SkrÃ¤ll order: 06 -> 79 -> Final Environment V2 -> BRED-ENV A / DIRECT-B.
"""

from typing import Iterable

ACTIVE_RESCUE_LEAVES = {4, 5, 10}
ACTIVE_SKRALL_LEAVES = {4, 5, 8, 10, 19, 20}

SKRALL_BADGES = {
    "â­ SKRÃ„LL PREMIUM",
    "ðŸ’¥ SKRÃ„LLKANDIDAT",
    "ðŸ’¥ SKRÃ„LL",
    "ðŸ›Ÿ SKRÃ„LL RESCUE",
    "ðŸ’¥ SKRÃ„LL 06",
    "ðŸ’¥ SKRÃ„LL 79",
    "ðŸ›Ÿ SKRÃ„LL K1",
    "ðŸ›Ÿ SKRÃ„LL K2",
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
    # START POINTS â€“ cautious, then EPS may override.
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
                best["_final_rank_reasons"].append("StartpoÃ¤ng Rank1")

    if has_start_points_top3 and len(order) >= 3 and gap_1_3 <= 35:
        # Keep the decided Rank1; only sort current Rank2/3 by start points.
        pair = order[1:3]
        pair.sort(key=lambda h: _int(h.get("start_points_rank", 999), 999))
        order[1:3] = pair
        for h in pair:
            h["_final_rank_reasons"].append("StartpoÃ¤ng Rank2/3")

    # ---------------------------------------------------------
    # EPS â€“ has precedence over start points.
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
        chosen["_final_rank_reasons"].append("Rank4/5 dubbel Spike+EPS â†’ Rank3")

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
            eps_candidate["_final_rank_reasons"].append("Dubbel Rescue EPS+Spike â†’ Rank3")
            eps_candidate["double_rescue"] = True
            eps_candidate["eps_rescue"] = True
            eps_candidate["spike_rescue"] = True
        elif eps_candidate is not None:
            # EPS has precedence when separate rescue candidates conflict.
            _move_to(order, eps_candidate, 5)
            eps_candidate["_final_rank_reasons"].append("EPS Rescue â†’ Rank5")
            eps_candidate["eps_rescue"] = True
        elif spike_candidate is not None:
            _move_to(order, spike_candidate, 5)
            spike_candidate["_final_rank_reasons"].append("Spike Rescue â†’ Rank5")
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

    # Rensa alla gamla/nya skrällbadges från visningen.
    # Övriga badges lämnas orörda.
    cleaned = []

    for badge in badges:
        text = str(badge)
        upper = text.upper()

        if (
            "SKRÄLL" in upper
            or "SKRÃ„LL" in upper
            or "SKRALL" in upper
        ):
            continue

        cleaned.append(badge)

    horse["badges"] = cleaned
    return cleaned


def _feature_rank(horses: list[dict], score_key: str) -> dict[int, int]:
    """Within-race rank, descending score, exact pandas rank(method="min")."""
    values = [
        (id(horse), _float(horse.get(score_key, 0), 0.0))
        for horse in horses
    ]

    # Competition ranking / pandas method="min":
    # [10, 10, 9] -> [1, 1, 3], not [1, 1, 2].
    ordered_values = sorted((value for _, value in values), reverse=True)
    rank_by_value = {}
    for position, value in enumerate(ordered_values, start=1):
        rank_by_value.setdefault(value, position)

    return {horse_id: rank_by_value[value] for horse_id, value in values}


def _frozen_environment(horse: dict) -> str:
    """Return frozen coarse environment used by 79-A."""
    for key in (
        "environment",
        "final_environment",
        "hybrid_environment",
        "rank1_environment",
    ):
        value = str(horse.get(key, "")).strip()
        if value:
            return value

    # Frozen environment-tree mapping from BUILD81/H21.
    leaf = _int(
        horse.get(
            "_v8x_race_leaf_id",
            horse.get(
                "hybrid_environment_leaf_id",
                horse.get("rank1_environment_leaf_id", horse.get("leaf_id", -1)),
            ),
        ),
        -1,
    )
    leaf_to_environment = {
        5: "Neutral",
        6: "Ã–ppet",
        8: "Kaos",
        9: "Ã–ppet",
        12: "Kaos",
        13: "Neutral",
        15: "Solid",
        16: "Neutral",
        19: "Solid",
        21: "Ã–ppet",
        22: "Solid",
        24: "Solid",
        25: "Favoritrank",
        27: "Kaos",
        29: "Neutral",
        30: "Kaos",
    }
    return leaf_to_environment.get(leaf, "")


def _prepare_frozen_candidate_features(processed_races: list[dict]) -> list[dict]:
    """Annotate exact within-race ranks needed by frozen 06/79/K1/K2."""
    all_horses: list[dict] = []

    for race_index, race_data in enumerate(processed_races):
        race = race_data.get("race", {})
        horses = race_data.get("horses", [])
        if not horses:
            continue

        # Base model rank must be total-score order and is already frozen by
        # _annotate_race_features, but fill defensively if needed.
        base_order = sorted(
            horses,
            key=lambda h: _float(h.get("total_score", 0), 0.0),
            reverse=True,
        )
        for rank, horse in enumerate(base_order, start=1):
            horse.setdefault("base_model_rank", rank)

        rank_specs = {
            "frozen_spike_rank": "spike_score",
            "frozen_speed_rank": "speed_score",
            "frozen_latest_rank": "latest_start_score",
            "frozen_form_rank": "form_score",
            "frozen_driver_rank": "driver_score",
            "frozen_record_rank": "record_score",
            "frozen_win_rank": "win_score",
            "frozen_starts_rank": "starts_score",
            "frozen_post_rank": "post_score",
            "frozen_prize_money_rank": "prize_money_score",
        }
        rank_maps = {
            field: _feature_rank(horses, source)
            for field, source in rank_specs.items()
        }

        for horse in horses:
            for field, rank_map in rank_maps.items():
                horse[field] = rank_map[id(horse)]
            horse["_frozen_race_index"] = race_index
            horse["_frozen_race_no"] = _int(race.get("race_no", race_index + 1), race_index + 1)

            # 79 anvÃ¤nder den NYA Environment V2-modellen.
            # Initial V2 finns redan nÃ¤r V8X/79 kÃ¶rs.
            horse["_environment_v2_79"] = str(
                race.get("initial_environment_v2", "")
            ).strip()

            all_horses.append(horse)

    return all_horses


def _mark_frozen_pick(horse: dict, variant: str) -> None:
    horse["skrall_selected"] = True
    horse["skrall_variant"] = variant

    if variant in {"06", "79"}:
        horse["skrall_main"] = True
    elif variant == "BRED-ENV A":
        horse["skrall_rescue"] = True
    elif variant == "DIRECT-B":
        horse["skrall_rescue2"] = True
    elif variant == "BRED-ENV A + DIRECT-B":
        horse["skrall_rescue"] = True
        horse["skrall_rescue2"] = True

    # Alla slutliga V8X-varianter visas likadant.
    display_badge = "💥 SKRÄLLKANDIDAT"

    if display_badge not in horse["badges"]:
        horse["badges"].append(display_badge)


def _apply_final_skrall_selection(processed_races: list[dict]) -> None:
    """
    OFFICIALLY FROZEN 06 / 79 / K1 / K2 engine.

    Order:
      1) 06-A CLEAN, percent 5-6
         speed rank <=2 + starts rank <=6
         + driver rank <=7 + prize-money rank <=6
         No NO PICK rule.

      2) 79-A, percent 7-9, only Neutral/Solid
         starts rank <=4 AND (
             win rank <=3 + form rank <=5
             OR
             win rank <=2 + driver rank <=4
         )
         NO PICK: driver_score <=4 AND record_score <=13

      3) If no surviving 06/79 candidate exists in the WHOLE ROUND:
         K1, percent 5-9: lowest speed_rank + latest_rank, max one/round.
         NO PICK: record_rank >=11 OR recent_prize_score <=8.

      4) K2, percent 5-9, after excluding raw K1 horse:
         record_rank + starts_rank + post_rank <=6 AND base_model_rank <=7.
         Choose lowest sum, max one/round. No NO PICK rule.

    Important: K1/K2 are recomputed AFTER 06/79 NO PICK, so newly created
    zero-rounds automatically receive fallback candidates.
    """
    all_horses = _prepare_frozen_candidate_features(processed_races)

    # Clear every old final skrÃ¤ll state/badge. The earlier frozen engine may
    # still generate diagnostics, but this function owns the final selection.
    for horse in all_horses:
        _clean_skrall_badges(horse)
        horse["skrall_selected"] = False
        horse["skrall_main"] = False
        horse["skrall_rescue"] = False
        horse["skrall_rescue2"] = False
        # The frozen 06/79/K1/K2 bank is explicitly without legacy Premium/Track flags.
        horse["skrall_premium"] = False
        horse["skrall_candidate"] = False
        horse["skrall_track1"] = False
        horse["skrall_track2"] = False
        horse["skrall_variant"] = ""
        horse["skrall_no_pick"] = False
        horse["skrall_no_pick_reason"] = ""

    # ---------------------------------------------------------
    # 06-A CLEAN â€” OFFICIALLY FROZEN NEW 06
    #
    # Spelprocent:       5-6 %
    # Speed-rank:        <= 2
    # Starts-rank:       <= 6
    # Driver-rank:       <= 7
    # Prize-money-rank:  <= 6
    #
    # IMPORTANT:
    # - No old 06 conditions.
    # - No Spike-rank requirement.
    # - No Form-rank requirement.
    # - No Post NO PICK.
    # - RELATIV <=3 is a separate rule and is NOT part of 06.
    # ---------------------------------------------------------
    selected_06: list[dict] = []

    for h in all_horses:
        qualifies = (
            5 <= _percent(h) <= 6
            and _int(h.get("frozen_speed_rank", 999), 999) <= 2
            and _int(h.get("frozen_starts_rank", 999), 999) <= 6
            and _int(h.get("frozen_driver_rank", 999), 999) <= 7
            and _int(h.get("frozen_prize_money_rank", 999), 999) <= 6
        )

        if not qualifies:
            continue

        selected_06.append(h)
        _mark_frozen_pick(h, "06")

    # ---------------------------------------------------------
    # 79-A Neutral + Solid â€” NEW Environment V2
    # ---------------------------------------------------------
    selected_79: list[dict] = []
    for h in all_horses:
        pct = _percent(h)
        environment = str(
            h.get("_environment_v2_79", "")
        ).strip()

        branch_a = (
            _int(h.get("frozen_starts_rank", 999), 999) <= 4
            and _int(h.get("frozen_win_rank", 999), 999) <= 3
            and _int(h.get("frozen_form_rank", 999), 999) <= 5
        )
        branch_b = (
            _int(h.get("frozen_starts_rank", 999), 999) <= 4
            and _int(h.get("frozen_win_rank", 999), 999) <= 2
            and _int(h.get("frozen_driver_rank", 999), 999) <= 4
        )

        qualifies = (
            7 <= pct <= 9
            and environment in {"Neutral", "Solid"}
            and (branch_a or branch_b)
        )
        if not qualifies:
            continue

        if (
            _float(h.get("driver_score", 0), 0.0) <= 4
            and _float(h.get("record_score", 0), 0.0) <= 13
        ):
            h["skrall_no_pick"] = True
            h["skrall_no_pick_reason"] = "79: Driver score <=4 + Record score <=13"
            continue

        selected_79.append(h)
        _mark_frozen_pick(h, "79")

    # BRED-ENV A / DIRECT-B kÃ¶rs INTE hÃ¤r.
    # De krÃ¤ver Final Environment V2 och appliceras dÃ¤rfÃ¶r fÃ¶rst efter
    # classify_environment(..., stage="final") i app.py.
    return


def apply_final_skrall_fallback(processed_races: list[dict]) -> list[dict]:
    """
    OFFICIALLY FROZEN FINAL FALLBACK.

    KÃ¶rs ENDAST om hela omgÃ¥ngen saknar Ã¶verlevande 06/79.

    BRED-ENV A:
        percent 3-8
        frozen_post_rank <= 2
        Final Environment V2 in {"Kaos", "Extrem kaos"}
        Ingen max-1-regel.

    DIRECT-B:
        percent 6-9
        frozen_prize_money_rank <= 4
        vÃ¤lj hÃ¶gsta SpikeScore
        max 1 per omgÃ¥ng.

    BÃ¥da reglerna kÃ¶rs som union. Samma hÃ¤st rÃ¤knas bara en gÃ¥ng.
    """

    all_horses = _prepare_frozen_candidate_features(processed_races)

    # Fallback fÃ¥r endast kÃ¶ras pÃ¥ en HEL 06/79-nollomgÃ¥ng.
    if any(
        h.get("skrall_selected", False)
        and h.get("skrall_variant") in {"06", "79"}
        for h in all_horses
    ):
        return processed_races

    # ---------------------------------------------------------
    # BRED-ENV A
    # 3-8 % + Post-rank <=2 + Final V2 Kaos/Extrem kaos
    # ---------------------------------------------------------
    bred_selected: list[dict] = []

    for race_data in processed_races:
        race = race_data.get("race", {})
        environment = str(
            race.get("final_environment_v2", "")
        ).strip()

        if environment not in {"Kaos", "Extrem kaos"}:
            continue

        for h in race_data.get("horses", []):
            pct = _percent(h)

            if (
                3 <= pct <= 8
                and _int(
                    h.get("frozen_post_rank", 999),
                    999,
                ) <= 2
            ):
                bred_selected.append(h)

    for h in bred_selected:
        _mark_frozen_pick(h, "BRED-ENV A")

    # ---------------------------------------------------------
    # DIRECT-B
    # 6-9 % + Prize-money-rank <=4
    # hÃ¶gsta SpikeScore, max 1 per omgÃ¥ng
    # ---------------------------------------------------------
    direct_pool = [
        h
        for h in all_horses
        if (
            6 <= _percent(h) <= 9
            and _int(
                h.get("frozen_prize_money_rank", 999),
                999,
            ) <= 4
        )
    ]

    if direct_pool:
        direct_b = sorted(
            direct_pool,
            key=lambda h: (
                -_float(h.get("spike_score", 0), 0.0),
                _int(h.get("base_model_rank", 999), 999),
                -_float(h.get("total_score", 0), 0.0),
                _int(h.get("_frozen_race_no", 999), 999),
                _name(h),
            ),
        )[0]

        if direct_b in bred_selected:
            # Union: samma hÃ¤st ska endast vara en kandidat.
            direct_b["badges"] = [
                b
                for b in direct_b.get("badges", [])
                if "BRED-ENV A" not in str(b)
            ]
            direct_b["skrall_variant"] = ""
            _mark_frozen_pick(
                direct_b,
                "BRED-ENV A + DIRECT-B",
            )
        else:
            _mark_frozen_pick(direct_b, "DIRECT-B")

    return processed_races



def apply_v8x_postprocess(processed_races: list[dict]) -> list[dict]:
    """Apply all frozen final-ranking corrections + final SkrÃ¤ll selection."""
    for race_data in processed_races:
        _apply_ranking_rules_to_race(race_data)

    _apply_final_skrall_selection(processed_races)
    return processed_races

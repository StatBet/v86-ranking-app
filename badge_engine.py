def is_back_post_large_field(horse, race):
    start_type = str(race.get("start", "") or race.get("start_type", "")).lower()
    field_size = len(race.get("horses", [])) if race.get("horses") else race.get("field_size", 0)

    post = horse.get("post", 0)

    try:
        post = int(post)
    except Exception:
        post = 0

    if field_size < 12:
        return False

    if start_type == "auto" and 9 <= post <= 12:
        return True

    if start_type == "volt" and 8 <= post <= 15:
        return True

    return False


def calculate_spike_score(horse, race):
    score = 0

    score += horse.get("win_percent", 0) * 2
    score += horse.get("form_score", 0) * 1.5
    score += horse.get("place_percent", 0) * 1

    avg_time = horse.get("avg_time", 0)
    avg_odds = horse.get("avg_odds", 0)

    if avg_time:
        score += max(0, 30 - avg_time) * 6

    if avg_odds:
        score += max(0, 20 - avg_odds) * 4

    if is_back_post_large_field(horse, race):
        score -= 120

    if horse.get("win_percent", 0) >= 60:
        score -= 40

    if horse.get("place_percent", 0) >= 80:
        score -= 30

    if horse.get("avg_odds", 0) and horse.get("avg_odds", 0) < 3:
        score -= 30

    return round(score, 2)


def _safe_float(value, default=0):
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _rank_horses_by_total_score(horses):
    ranked = sorted(
        horses,
        key=lambda h: h.get("total_score", 0),
        reverse=True
    )

    for i, horse in enumerate(ranked, start=1):
        horse["_model_rank_live"] = i

    return ranked


def _get_score_gap_1_2(ranked):
    if len(ranked) < 2:
        return None

    return (
        _safe_float(ranked[0].get("total_score", 0))
        - _safe_float(ranked[1].get("total_score", 0))
    )


def _is_value_candidate_balanced(horse):
    rank = _safe_int(horse.get("_model_rank_live", horse.get("model_rank", 0)))
    total_score = _safe_float(horse.get("total_score", 0))
    spike_score = _safe_float(horse.get("spike_score", 0))

    return (
        4 <= rank <= 7
        and 125 <= total_score <= 134
        and spike_score >= 105
    )


def _is_value_candidate_offensive(horse):
    rank = _safe_int(horse.get("_model_rank_live", horse.get("model_rank", 0)))
    total_score = _safe_float(horse.get("total_score", 0))
    spike_score = _safe_float(horse.get("spike_score", 0))

    return (
        3 <= rank <= 5
        and 125 <= total_score <= 134
        and spike_score >= 105
    )


def _is_value_candidate_plus(horse):
    rank = _safe_int(horse.get("_model_rank_live", horse.get("model_rank", 0)))
    total_score = _safe_float(horse.get("total_score", 0))
    spike_score = _safe_float(horse.get("spike_score", 0))

    return (
        3 <= rank <= 5
        and 125 <= total_score <= 134
        and spike_score >= 150
    )


def apply_system_only_value_flags(horses, race):
    ranked = _rank_horses_by_total_score(horses)
    score_gap_1_2 = _get_score_gap_1_2(ranked)

    balanced_candidates = []
    offensive_candidates = []
    plus_candidates = []

    for horse in horses:
        horse["system_value_balanced"] = False
        horse["system_value_offensive"] = False
        horse["system_value_plus"] = False
        horse["system_only_value_candidate"] = False

        if _is_value_candidate_balanced(horse):
            horse["system_value_balanced"] = True
            horse["system_only_value_candidate"] = True
            balanced_candidates.append(horse)

        if _is_value_candidate_offensive(horse):
            horse["system_value_offensive"] = True
            horse["system_only_value_candidate"] = True
            offensive_candidates.append(horse)

        if _is_value_candidate_plus(horse):
            horse["system_value_plus"] = True
            horse["system_only_value_candidate"] = True
            plus_candidates.append(horse)

    race_has_value_candidate = len(balanced_candidates) > 0

    value_names = [
        str(h.get("horse", h.get("name", "")))
        for h in balanced_candidates
    ]

    for horse in horses:
        horse["race_has_value_candidate"] = race_has_value_candidate
        horse["value_candidate_count"] = len(balanced_candidates)
        horse["value_candidate_names"] = value_names
        horse["score_gap_1_2"] = score_gap_1_2

        # System-only warnings. These should be shown only near spikförslag/systembygge.
        horse["spik_warning_yellow"] = race_has_value_candidate
        horse["spik_warning_red"] = (
            race_has_value_candidate
            and score_gap_1_2 is not None
            and score_gap_1_2 < 10
        )

    return horses


def assign_badges(horses, race):
    ranked = sorted(
        horses,
        key=lambda h: h.get("total_score", 0),
        reverse=True
    )

    race_for_badges = dict(race)
    race_for_badges["horses"] = horses

    for horse in horses:
        horse["badges"] = []
        horse["spike_score"] = calculate_spike_score(horse, race_for_badges)

    ranked = _rank_horses_by_total_score(horses)

    ranked_horses = ranked[:5]

    for horse in ranked_horses:
        horse["badges"].append("🟧 Topp 5")

    model_top_3 = ranked[:3]

    for horse in model_top_3:
        if (
            horse.get("percent", 0) >= 30
            and is_back_post_large_field(horse, race_for_badges)
        ):
            horse["badges"].append("⚠️ Riskfavorit")

    # IMPORTANT:
    # Value Coverage is system-only. We do NOT add normal ranking badges here.
    apply_system_only_value_flags(horses, race_for_badges)

    return horses


def get_round_spikes(all_races):
    candidates = []

    for race_data in all_races:
        race = race_data["race"]
        horses = race_data["horses"]

        if not horses:
            continue

        race_for_badges = dict(race)
        race_for_badges["horses"] = horses

        for horse in horses:
            horse["badges"] = [
                badge for badge in horse.get("badges", [])
                if badge not in ["🟩 Toppspik", "🟦 Spik"]
            ]

            horse["spike_score"] = calculate_spike_score(
                horse,
                race_for_badges
            )

        ranked = _rank_horses_by_total_score(horses)

        apply_system_only_value_flags(horses, race_for_badges)

        best_horse = ranked[0]

        if len(ranked) > 1:
            rank1 = ranked[0]
            rank2 = ranked[1]

            score_gap = (
                rank1.get("total_score", 0)
                - rank2.get("total_score", 0)
            )

            if (
                rank1.get("post", 99) >= 6
                and rank2.get("post", 99) <= 8
                and score_gap < 10
            ):
                best_horse = rank2

        best_horse["spike_score"] = calculate_spike_score(
            best_horse,
            race_for_badges
        )

        # Preserve system-only warning fields on the selected spik candidate
        best_horse["spik_warning_yellow"] = bool(
            best_horse.get("race_has_value_candidate", False)
        )
        best_horse["spik_warning_red"] = bool(
            best_horse.get("race_has_value_candidate", False)
            and best_horse.get("score_gap_1_2") is not None
            and best_horse.get("score_gap_1_2") < 10
        )

        candidates.append(best_horse)

    selected = sorted(
        candidates,
        key=lambda h: h.get("spike_score", 0),
        reverse=True
    )[:4]

    for i, horse in enumerate(selected):
        if i < 2:
            horse.setdefault("badges", []).append("🟩 Toppspik")
            horse["spike_badge_type"] = "Toppspik"
        else:
            horse.setdefault("badges", []).append("🟦 Spik")
            horse["spike_badge_type"] = "Spik"

    return selected
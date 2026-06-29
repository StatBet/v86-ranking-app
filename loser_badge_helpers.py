def _num(value, default=0):
    try:
        return float(value)
    except Exception:
        return default


def has_rank68_badge(h):
    text = " ".join(map(str, h.get("badges", [])))
    return (
        "Rank 6-8" in text
        or "🔵" in text
        or "🔹" in text
    )


def is_global_loser(h):
    spike = _num(h.get("spike_score", 0))
    total = _num(h.get("total_score", 0))
    win = _num(h.get("win_score", 0))

    base_loser = (
        (spike < 140 and total < 80)
        or
        (spike < 160 and total < 90 and win < 14)
    )

    weak_count = (
        int(_num(h.get("place_score", 0)) < 8)
        + int(_num(h.get("form_score_all_rank", 0)) >= 6)
        + int(spike < 225)
        + int(_num(h.get("driver_score", 0)) < 8)
    )

    speed_post_loser = (
        _num(h.get("speed_score_all_rank", 0)) >= 10
        and 9 <= _num(h.get("post", 0)) <= 15
        and weak_count >= 2
    )

    return base_loser or speed_post_loser


def add_race_gap_fields(horses):
    if not horses:
        return horses

    total_sum = sum(_num(h.get("total_score", 0)) for h in horses)
    spike_sum = sum(_num(h.get("spike_score", 0)) for h in horses)

    total_leader = max(_num(h.get("total_score", 0)) for h in horses)
    spike_leader = max(_num(h.get("spike_score", 0)) for h in horses)

    sorted_total = sorted(
        horses,
        key=lambda h: _num(h.get("total_score", 0)),
        reverse=True
    )
    sorted_spike = sorted(
        horses,
        key=lambda h: _num(h.get("spike_score", 0)),
        reverse=True
    )

    total_rank_by_id = {id(h): i + 1 for i, h in enumerate(sorted_total)}
    spike_rank_by_id = {id(h): i + 1 for i, h in enumerate(sorted_spike)}

    for h in horses:
        h["race_total_sum"] = round(total_sum, 1)
        h["race_spike_sum"] = round(spike_sum, 1)
        h["horse_total_gap"] = round(total_leader - _num(h.get("total_score", 0)), 1)
        h["horse_spike_gap"] = round(spike_leader - _num(h.get("spike_score", 0)), 1)
        h["total_score_rank_in_race"] = total_rank_by_id[id(h)]
        h["spike_score_rank_in_race"] = spike_rank_by_id[id(h)]

    return horses


def is_extreme_total_gap_loser(h):
    return (
        360 <= _num(h.get("race_total_sum", 0)) <= 555
        and _num(h.get("horse_total_gap", 0)) >= 36
    )


def is_extreme_spike_gap_loser(h):
    total_rank = int(_num(h.get("total_score_rank_in_race", 99)))
    spike_rank = int(_num(h.get("spike_score_rank_in_race", 99)))

    protected_top5_signal = (
        total_rank <= 5
        and spike_rank <= 5
    )

    return (
        360 <= _num(h.get("race_spike_sum", 0)) <= 810
        and _num(h.get("horse_spike_gap", 0)) >= 101
        and not protected_top5_signal
    )


def is_loser_badge(h):
    model_rank = int(_num(h.get("model_rank", 99)))

    # Skydda alltid modellens rank 1-5
    if model_rank <= 5:
        return False

    # Skydda Rank 6-8-badges
    if has_rank68_badge(h):
        return False

    return (
        is_global_loser(h)
    )


def apply_loser_badges_to_race(horses):
    horses = add_race_gap_fields(horses)

    for h in horses:
        h.setdefault("badges", [])

        if is_loser_badge(h) and "🔴" not in h["badges"]:
            h["badges"].append("🔴")

    return horses
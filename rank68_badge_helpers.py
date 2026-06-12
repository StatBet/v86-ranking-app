def remove_old_top5_badges(badges):
    if not badges:
        return []

    blocked = ["Top5", "Topp 5", "Topp5", "TOP5"]

    return [
        b for b in badges
        if not any(x in str(b) for x in blocked)
    ]


def is_rank68_v1(h):
    rank = h.get("model_rank", 0)

    return (
        6 <= rank <= 8
        and h.get("spike_score", 0) >= 170
        and h.get("spread", 0) <= 51
        and 99 <= h.get("total_score", 0) <= 139
    )


def is_rank68_v2_strong_b(h):
    rank = h.get("model_rank", 0)

    return (
        6 <= rank <= 8
        and h.get("spike_score", 0) >= 120
        and h.get("spread", 0) <= 50
        and h.get("total_score", 0) >= 105
        and h.get("avg_odds", 999) <= 15
        and (
            h.get("post", 99) <= 5
            or h.get("latest_start_score", 0) >= 7
            or h.get("form_score", 0) >= 35
        )
    )


def passes_rank68_cleaner(h):
    return (
        h.get("win_score", 0) >= 25
        or h.get("post", 99) <= 5
        or h.get("latest_start_score", 0) >= 7
    )


def get_rank68_badge(h):
    is_candidate = is_rank68_v1(h) or is_rank68_v2_strong_b(h)

    if not is_candidate:
        return None

    if not passes_rank68_cleaner(h):
        return None

    if h.get("win_score", 0) >= 25:
        return "🔵 Rank 6-8+"

    return "🔹 Rank 6-8"


def apply_rank68_badges(h):
    badges = remove_old_top5_badges(h.get("badges", []))

    badge = get_rank68_badge(h)

    if badge:
        badges.append(badge)

    h["badges"] = badges

    return h
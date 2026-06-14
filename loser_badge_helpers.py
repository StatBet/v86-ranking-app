def is_loser_a(h):
    return (
        h.get("spike_score", 0) < 60
        and h.get("total_score", 0) < 90
    )


def is_loser_cplus(h):
    return (
        h.get("spike_score", 0) < 80
        and h.get("total_score", 0) < 100
        and h.get("win_score", 0) < 12
    )


def get_loser_badge(h):
    if is_loser_a(h) or is_loser_cplus(h):
        return "🔴"

    return None


def apply_loser_badges(h):
    badges = h.get("badges", [])

    badge = get_loser_badge(h)

    if badge and badge not in badges:
        badges.append(badge)

    h["badges"] = badges

    return h
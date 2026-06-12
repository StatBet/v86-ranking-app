from badge_rules import (
    get_race_metrics,
    get_loppbadge,
    format_loppbadge,
    get_horse_badges,
    get_loser_flags,
)


def build_race_badge_line(race):
    metrics = get_race_metrics(race)
    loppbadge = get_loppbadge(metrics)
    return loppbadge, format_loppbadge(loppbadge)


def build_horse_badge_text(horse, loppbadge):
    badges = get_horse_badges(horse)
    loser_flags = get_loser_flags(horse, loppbadge)

    extras = []

    if badges:
        extras.append(" / ".join(badges))

    if loser_flags:
        extras.append(" / ".join(loser_flags))

    if not extras:
        return ""

    return f"  [{'; '.join(extras)}]"
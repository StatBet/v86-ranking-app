DARK_GREEN = "🟩"


def _iter_rows(race_or_horses):
    if hasattr(race_or_horses, "iterrows"):
        for _, row in race_or_horses.iterrows():
            yield row.to_dict()
    else:
        for row in race_or_horses:
            yield row


def get_race_metrics(race_or_horses):
    scores = {}

    for i, r in enumerate(_iter_rows(race_or_horses), start=1):
        rank = int(r.get("model_rank", i))
        scores[rank] = r.get("total_score", 0)

    r1 = scores.get(1, 0)

    return {
        "total_sum": sum(scores.values()),
        "spread_1_8": r1 - scores.get(8, 0),
        "gap_1_2": r1 - scores.get(2, 0),
        "gap_1_3": r1 - scores.get(3, 0),
        "gap_1_4": r1 - scores.get(4, 0),
        "gap_1_5": r1 - scores.get(5, 0),
    }


def get_loppbadge(metrics):
    spread = metrics.get("spread_1_8", 0)
    total_sum = metrics.get("total_sum", 0)
    gap_1_2 = metrics.get("gap_1_2", 0)

    if spread >= 70 and total_sum <= 1450 and gap_1_2 >= 5:
        return {
            "label": "3-hästarslopp",
            "square": DARK_GREEN,
            "main_group": 3,
            "hit_rate": 81.0,
            "reason": "rank 1–3: 81% | rank 4–5: 12% | rank 6+: 7%",
            "loser_filter": "Loser B",
        }

    if spread >= 60 and total_sum <= 1450:
        return {
            "label": "Topp 5-profil",
            "square": DARK_GREEN,
            "main_group": 5,
            "hit_rate": 90.0,
            "reason": "rank 1–3: 69% | rank 4–5: 21% | rank 6+: 10%",
            "loser_filter": None,
        }

    return {
        "label": "Öppet lopp",
        "square": "",
        "main_group": None,
        "hit_rate": None,
        "reason": "ingen loppbadge",
        "loser_filter": None,
    }


def loser_b(horse):
    return (
        (
            horse.get("spike_score", 0) <= 120
            and horse.get("driver_score", 0) == 0
            and horse.get("latest_start_score", 0) <= 3
            and horse.get("form_score", 0) <= 20
            and horse.get("avg_odds", 0) > 15
        )
        or horse.get("spike_score", 0) <= 50
    )


def loser_d(horse):
    return loser_b(horse) and horse.get("speed_score", 0) <= 14


def get_loser_flags(horse, loppbadge=None):
    flags = []

    if loppbadge and loppbadge.get("label") == "3-hästarslopp":
        if loser_b(horse):
            flags.append("Loser B")

    elif loppbadge and loppbadge.get("label") == "Topp 5-profil":
        if loser_d(horse):
            flags.append("Loser D")

    return flags

def format_loppbadge(badge):

    if badge["label"] == "Öppet lopp":
        return "Öppet lopp"

    return (
        f"{'🟩' * badge['main_group']} "
        f"{badge['label']} "
        f"({badge['hit_rate']}%)"
    )
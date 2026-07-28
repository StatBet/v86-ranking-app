DARK_GREEN = "🟩"


# Historisk vinstfördelning per modellrank.
# 3-hästarslopp: 110 lopp.
THREE_HORSE_PROBABILITIES = {
    1: 52 / 110,
    2: 21 / 110,
    3: 12 / 110,
    4: 8 / 110,
    5: 6 / 110,
    6: 3 / 110,
    7: 2 / 110,
    8: 3 / 110,
    9: 1 / 110,
    10: 0 / 110,
    11: 1 / 110,
    12: 1 / 110,
}


# Historisk vinstfördelning per modellrank.
# Öppet lopp: 508 lopp.
OPEN_RACE_PROBABILITIES = {
    1: 147 / 508,
    2: 84 / 508,
    3: 57 / 508,
    4: 43 / 508,
    5: 25 / 508,
    6: 26 / 508,
    7: 43 / 508,
    8: 21 / 508,
    9: 16 / 508,
    10: 14 / 508,
    11: 18 / 508,
    12: 7 / 508,
    13: 2 / 508,
    14: 3 / 508,
    15: 2 / 508,
}


# Topp 5-profil: 40 % egen historik och 60 % 3-hästarslopp.
TOP5_RAW_PROBABILITIES = {
    1: 16 / 42,
    2: 12 / 42,
    3: 5 / 42,
    4: 2 / 42,
    5: 2 / 42,
    6: 2 / 42,
    7: 2 / 42,
    8: 1 / 42,
}


TOP5_PROFILE_PROBABILITIES = {
    rank: (
        0.40 * TOP5_RAW_PROBABILITIES.get(rank, 0.0)
        + 0.60 * THREE_HORSE_PROBABILITIES.get(rank, 0.0)
    )
    for rank in range(1, 16)
}


PROBABILITIES_BY_PROFILE = {
    "3-hästarslopp": THREE_HORSE_PROBABILITIES,
    "Topp 5-profil": TOP5_PROFILE_PROBABILITIES,
    "Öppet lopp": OPEN_RACE_PROBABILITIES,
}


def _iter_rows(race_or_horses):
    if hasattr(race_or_horses, "iterrows"):
        for _, row in race_or_horses.iterrows():
            yield row.to_dict()
    else:
        for row in race_or_horses:
            yield row


def get_race_metrics(race_or_horses):
    scores = {}

    for i, row in enumerate(_iter_rows(race_or_horses), start=1):
        rank = int(row.get("model_rank", i))
        scores[rank] = row.get("total_score", 0)

    rank_1 = scores.get(1, 0)

    return {
        "total_sum": sum(scores.values()),
        "spread_1_8": rank_1 - scores.get(8, 0),
        "gap_1_2": rank_1 - scores.get(2, 0),
        "gap_1_3": rank_1 - scores.get(3, 0),
        "gap_1_4": rank_1 - scores.get(4, 0),
        "gap_1_5": rank_1 - scores.get(5, 0),
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
            "hit_rate": 77.27,
            "reason": "rank 1–3: 77,27% | rank 4–5: 12,73% | rank 6+: 10,00%",
            "loser_filter": "Loser B",
        }

    if spread >= 60 and total_sum <= 1450:
        return {
            "label": "Topp 5-profil",
            "square": DARK_GREEN,
            "main_group": 5,
            "hit_rate": 77.79,
            "reason": "viktad modell: rank 1–3: 77,79% | rank 4–5: 11,44% | rank 6+: 10,77%",
            "loser_filter": None,
        }

    return {
        "label": "Öppet lopp",
        "square": "",
        "main_group": None,
        "hit_rate": 56.69,
        "reason": "rank 1–3: 56,69% | rank 4–5: 13,39% | rank 6+: 29,92%",
        "loser_filter": None,
    }


def get_rank_probability(profile_label, model_rank):
    """Returnera profilens grundsannolikhet för en modellrank som decimaltal."""
    try:
        rank = int(model_rank)
    except (TypeError, ValueError):
        return 0.0

    profile = PROBABILITIES_BY_PROFILE.get(
        profile_label,
        OPEN_RACE_PROBABILITIES,
    )
    return float(profile.get(rank, 0.0))


def apply_model_probabilities(horses, loppbadge):
    """
    Lägg till modellchans på varje häst.

    Endast ranker som faktiskt finns i loppet räknas med. De historiska
    grundsannolikheterna normaliseras därför till exakt 100 procent inom
    det aktuella startfältet.
    """
    if not horses:
        return horses

    profile_label = (
        loppbadge.get("label", "Öppet lopp")
        if isinstance(loppbadge, dict)
        else str(loppbadge or "Öppet lopp")
    )

    raw_probabilities = []

    for index, horse in enumerate(horses, start=1):
        rank = horse.get("model_rank", index)
        raw_probability = get_rank_probability(profile_label, rank)
        raw_probabilities.append(raw_probability)

    probability_sum = sum(raw_probabilities)

    if probability_sum <= 0:
        equal_probability = 100.0 / len(horses)

        for horse in horses:
            horse["model_probability"] = equal_probability

        return horses

    for horse, raw_probability in zip(horses, raw_probabilities):
        horse["model_probability"] = (
            raw_probability / probability_sum * 100.0
        )

    return horses


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
        return f"Öppet lopp ({badge['reason']})"

    return (
        f"{'🟩' * badge['main_group']} "
        f"{badge['label']} "
        f"({badge['hit_rate']:.2f}% topp 3)"
    )
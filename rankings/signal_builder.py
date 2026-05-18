from rankings.signals import HorseSignals


def _calc_form_trend(h):
    results = h.get("placements", [5, 5, 5, 5])

    if len(results) < 2:
        return 50.0

    # viktning av senaste lopp (nyast viktigast)
    weights = [0.4, 0.3, 0.2, 0.1]

    weighted = 0.0
    total_w = 0.0

    for i, w in enumerate(weights):
        if i < len(results):
            # 1 = bäst → högst score
            score = max(0, 100 - (results[i] * 10))
            weighted += score * w
            total_w += w

    base_form = weighted / total_w if total_w > 0 else 50.0

    # trend: förbättring eller försämring
    trend = 0.0
    if len(results) >= 2:
        trend = (results[-2] - results[-1]) * 5

    return base_form + trend


def _calc_consistency(h):
    placements = h.get("placements", [5, 5, 5])

    spread = max(placements) - min(placements)
    return max(0.0, 100 - spread * 10)


def build_signals(horse_data):
    """
    Omvandlar rådata → signaler som används i rankingmodellen
    """

    form_trend = _calc_form_trend(horse_data)

    speed_rating = horse_data.get("km_time", 0)

    distance_fit = horse_data.get("distance_score", 0)

    driver_synergy = horse_data.get("driver_winrate", 0)

    consistency = _calc_consistency(horse_data)

    return HorseSignals(
        form_trend=form_trend,
        speed_rating=speed_rating,
        distance_fit=distance_fit,
        driver_synergy=driver_synergy,
        consistency=consistency
    )
def _calc_speed_rating(h):
    km_time = h.get("km_time", 0)

    # basnivå (normalisering)
    base = km_time

    # justering beroende på nivå
    # lägre tid = bättre → vi inverterar lite
    score = max(0, 120 - base)

    # liten bonus om hästen är snabb + stabil
    placements = h.get("placements", [5, 5, 5])
    stability_bonus = max(0, 10 - (max(placements) - min(placements)))

    return score + stability_bonus
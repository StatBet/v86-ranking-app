def is_back_post_large_field(horse, race):
    start_type = str(race.get("start", "")).lower()
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
        score -= 80

    return round(score, 2)


def assign_badges(horses, race):
    ranked = sorted(
        horses,
        key=lambda h: h.get("total_score", 0),
        reverse=True
    )

    for horse in horses:
        horse["badges"] = []
        horse["spike_score"] = calculate_spike_score(horse, race)

    spike_ranked = sorted(
        horses,
        key=lambda h: h.get("spike_score", 0),
        reverse=True
    )

    

    ranked_horses = ranked[:5]

    for horse in ranked_horses:
        horse["badges"].append("🟧 Topp 5")

    for horse in horses:
        if (
            horse.get("percent", 0) >= 30
            and is_back_post_large_field(horse, race)
        ):
            horse["badges"].append("⚠ Riskfavorit")

    return horses

def get_round_spikes(all_races):
    return []
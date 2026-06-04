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

    ranked_horses = ranked[:5]

    for horse in ranked_horses:
        horse["badges"].append("🟧 Topp 5")

    model_top_3 = ranked[:3]

    for horse in model_top_3:
        if (
            horse.get("percent", 0) >= 30
            and is_back_post_large_field(horse, race)
        ):
            horse["badges"].append("⚠ Riskfavorit")

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

        ranked = sorted(
            horses,
            key=lambda h: h.get("total_score", 0),
            reverse=True
        )

        best_horse = ranked[0]
        best_horse["spike_score"] = calculate_spike_score(
            best_horse,
            race_for_badges
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
        else:
            horse.setdefault("badges", []).append("🟦 Spik")

    return selected
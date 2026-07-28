BADGE = "🟥"


def _rank_desc(values):
    unique = sorted(set(values), reverse=True)
    return {
        value: i + 1
        for i, value in enumerate(unique)
    }


def _rank_asc(values):
    unique = sorted(set(values))
    return {
        value: i + 1
        for i, value in enumerate(unique)
    }


def apply_chanslos_combo_badge(horses):

    if not horses:
        return horses

    prize_scores = [
        h.get("prize_money_score", 0)
        for h in horses
    ]

    form_scores = [
        h.get("form_score", 0)
        for h in horses
    ]

    driver_scores = [
        h.get("driver_score", 0)
        for h in horses
    ]

    win_scores = [
        h.get("win_score", 0)
        for h in horses
    ]

    latest_scores = [
        h.get("latest_start_score", 0)
        for h in horses
    ]

    prize_rank = _rank_desc(prize_scores)
    form_rank = _rank_desc(form_scores)
    driver_rank = _rank_desc(driver_scores)
    win_rank = _rank_desc(win_scores)
    latest_rank = _rank_desc(latest_scores)

    eligible = []

    for horse in horses:

        horse["_prize_rank"] = prize_rank[
            horse.get("prize_money_score", 0)
        ]

        horse["_form_rank"] = form_rank[
            horse.get("form_score", 0)
        ]

        horse["_driver_rank"] = driver_rank[
            horse.get("driver_score", 0)
        ]

        horse["_win_rank"] = win_rank[
            horse.get("win_score", 0)
        ]

        horse["_latest_rank"] = latest_rank[
            horse.get("latest_start_score", 0)
        ]

        if (
            horse["_prize_rank"] >= 6
            and horse["_form_rank"] >= 6
            and horse["_driver_rank"] >= 6
        ):

            horse["_combo"] = (
                horse.get("prize_money_score", 0)
                + horse.get("form_score", 0)
                + horse.get("driver_score", 0)
            )

            eligible.append(horse)

    if not eligible:
        return horses

    combo_rank = _rank_asc([
        h["_combo"]
        for h in eligible
    ])

    for horse in eligible:

        if combo_rank[horse["_combo"]] != 1:
            continue

        if (
            horse["_win_rank"] <= 4
            and horse["_latest_rank"] <= 4
        ):
            continue

        badges = horse.setdefault("badges", [])

        if BADGE not in badges:
            badges.append(BADGE)

    return horses
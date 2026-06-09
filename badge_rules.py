def get_loppbadge(metrics):
    spread = metrics.get("spread_1_8", 0)
    gap_13 = metrics.get("gap_1_3", 0)
    gap_14 = metrics.get("gap_1_4", 0)

    if spread >= 80:
        return {
            "label": "🔥 3-hästarslopp",
            "main_group": 3,
            "hit_rate": "81.0%",
            "reason": "spread_1_8 >= 80",
        }

    if spread >= 75:
        return {
            "label": "⭐ 4-hästarslopp",
            "main_group": 4,
            "hit_rate": "82.6%",
            "reason": "spread_1_8 >= 75",
        }

    if gap_14 >= 30:
        return {
            "label": "🎯 5-hästarslopp",
            "main_group": 5,
            "hit_rate": "80.4%",
            "reason": "gap_1_4 >= 30",
        }

    if gap_13 >= 30:
        return {
            "label": "🎯 5-hästarslopp",
            "main_group": 5,
            "hit_rate": "80.2%",
            "reason": "gap_1_3 >= 30",
        }

    return {
        "label": "⚠ Öppet lopp",
        "main_group": 5,
        "hit_rate": None,
        "reason": "ingen stark loppbadge",
    }


def get_horse_badges(horse):
    badges = []

    rank = horse.get("model_rank", 0)
    spike = horse.get("spike_score", 0)
    spread = horse.get("spread", 0)
    total = horse.get("total_score", 0)
    odds = horse.get("avg_odds", 0)
    post = horse.get("post", 0)
    latest = horse.get("latest_start_score", 0)
    form = horse.get("form_score", 0)
    driver = horse.get("driver_score", 0)
    win_pct = horse.get("win_percent", 0)
    percent = horse.get("percent", 0)
    speed = horse.get("speed_score", 0)

    if (
        6 <= rank <= 8
        and spike >= 170
        and spread <= 51
        and 99 <= total <= 139
    ):
        badges.append("Underskattad V1")

    if (
        6 <= rank <= 8
        and spike >= 120
        and spread <= 50
        and total >= 105
        and odds <= 15
        and (post <= 5 or latest >= 7 or form >= 35)
    ):
        badges.append("Underskattad V2")

    if (
        6 <= rank <= 8
        and 7 <= latest <= 10
        and 19 <= form <= 40
        and driver >= 8
        and odds <= 15
        and win_pct >= 10
    ):
        badges.append("Form/Kusk V3")

    if (
        percent <= 14
        and 7 <= latest <= 10
        and 19 <= form <= 40
    ):
        badges.append("Skrällvarning")

    return badges


def get_loser_flags(horse):
    flags = []

    rank = horse.get("model_rank", 0)
    spike = horse.get("spike_score", 0)
    driver = horse.get("driver_score", 0)
    latest = horse.get("latest_start_score", 0)
    form = horse.get("form_score", 0)
    odds = horse.get("avg_odds", 0)
    speed = horse.get("speed_score", 0)
    percent = horse.get("percent", 0)

    loser_b = (
        6 <= rank <= 8
        and (
            (
                spike <= 120
                and driver == 0
                and latest <= 3
                and form <= 20
                and odds > 15
            )
            or spike <= 50
        )
    )

    if loser_b and speed <= 14:
        flags.append("Röd loserflagga")

    elif loser_b:
        flags.append("Gul loserflagga")

    if 6 <= rank <= 8 and percent <= 4 and spike <= 100:
        flags.append("Loser C")

    return flags
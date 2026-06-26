import pandas as pd
import random
from math import prod

MAX_ROWS = 540
ITERATIONS_PER_ROUND = 5000
random.seed(20260625)

df = pd.read_csv("ml_dataset.csv").fillna(0)

payout = pd.read_csv("payout_vs_winner_percent_rounds.csv")
payout = payout[["date", "payout_8_value"]].drop_duplicates("date")
df = df.merge(payout, on="date", how="left")


def is_open_lopp(race):
    scores = {int(r["model_rank"]): r["total_score"] for _, r in race.iterrows()}
    r1 = scores.get(1, 0)

    return (
        r1 - scores.get(8, 0) < 70
        and r1 - scores.get(3, 0) < 30
        and r1 - scores.get(4, 0) < 30
    )


def get_race_flags(race):
    race = race.copy()
    sorted_pct = race.sort_values("percent", ascending=False)

    rank1_percent = sorted_pct.iloc[0]["percent"]
    top3_sum = sorted_pct.head(3)["percent"].sum()
    medium_count = len(race[race["percent"].between(15, 25)])

    open_lopp = is_open_lopp(race)

    value = race[
        race["model_rank"].between(4, 7)
        & race["total_score"].between(125, 134)
        & (race["spike_score"] >= 105)
    ]

    has_value = len(value) > 0
    level2 = open_lopp and has_value
    level3 = open_lopp and has_value and 65 <= top3_sum < 75

    top3_warning = race["total_score"].sum() >= 1538

    medium_lopp = (
        rank1_percent < 30
        and top3_sum < 75
        and medium_count >= 2
    )

    favorite_lopp = (
        rank1_percent >= 50
        and top3_sum >= 80
    )

    return {
        "rank1_percent": rank1_percent,
        "top3_sum": top3_sum,
        "medium_count": medium_count,
        "open": open_lopp,
        "top3_warning": top3_warning,
        "has_value": has_value,
        "level2": level2,
        "level3": level3,
        "medium_lopp": medium_lopp,
        "favorite_lopp": favorite_lopp,
    }


def race_type(flags):
    if flags["level3"]:
        return "level3"
    if flags["medium_lopp"]:
        return "medium"
    if flags["top3_warning"]:
        return "top3_warning"
    if flags["level2"]:
        return "level2"
    if flags["open"]:
        return "open"
    if flags["favorite_lopp"]:
        return "favorite"
    return "normal"


TEMPLATES = {
    "favorite": [
        [1],
        [1, 2],
    ],

    "normal": [
        [1],
        [1, 2],
        [1, 2, 3],
        [1, 2, 3, 4],
        [1, 2, 3, 4, 5],
        [2, 3, 4, 5],
        [3, 4, 5, 6],
    ],

    "open": [
        [1, 2, 3, 4],
        [1, 2, 3, 4, 5],
        [2, 3, 4, 5, 6],
        [3, 4, 5, 6, 7],
    ],

    "top3_warning": [
        [4, 5],
        [4, 5, 6],
        [4, 5, 6, 7],
        [4, 5, 6, 7, 8],
    ],

    "medium": [
        [2, 3, 4, 5, 6],
        [3, 4, 5, 6, 7],
        [3, 4, 5, 6, 7, 8],
        [4, 5, 6, 7, 8],
    ],

    "level2": [
        [2, 3, 4, 5, 6],
        [3, 4, 5, 6, 7],
        [3, 4, 5, 6, 7, 8],
    ],

    "level3": [
        [4, 5],
        [4, 5, 6],
        [4, 5, 6, 7],
        [4, 5, 6, 7, 8],
    ],
}


def pick_horses_by_template(race, ranks):
    sub = race[race["model_rank"].isin(ranks)].copy()

    if len(sub) == 0:
        sub = race.sort_values("model_rank").head(len(ranks)).copy()

    return sub.sort_values("model_rank")


def profile_score(system_rows):
    rank1_included = sum(1 for r in system_rows if r["has_rank1"])
    rank4plus_lopp = sum(1 for r in system_rows if r["has_rank4plus"])
    rank7plus_lopp = sum(1 for r in system_rows if r["has_rank7plus"])
    big_fav_count = sum(r["big_favorite_included"] for r in system_rows)

    scenario_percent_sum = sum(r["avg_selected_percent"] for r in system_rows)

    score = 0

    # Ny mer realistisk 100k-profil
    score -= abs(rank1_included - 4) * 18
    score -= abs(rank4plus_lopp - 5) * 14
    score -= abs(rank7plus_lopp - 2) * 16

    # Ny spel%-zon: 160–210, sweet spot runt 185
    if 160 <= scenario_percent_sum <= 210:
        score += 50
        score -= abs(scenario_percent_sum - 185) * 0.6
    else:
        score -= abs(scenario_percent_sum - 185) * 1.4

    # Max två stora favoriter okej, fler straffas
    if big_fav_count > 2:
        score -= (big_fav_count - 2) * 35

    if rank7plus_lopp >= 2:
        score += 20

    if rank4plus_lopp >= 5:
        score += 20

    if 3 <= rank1_included <= 5:
        score += 15

    return score


def simulate_round(round_df):
    race_data = []

    for race_id, race in round_df.groupby("race_id"):
        race = race.copy()
        flags = get_race_flags(race)
        rt = race_type(flags)

        race_data.append({
            "race_id": race_id,
            "race": race,
            "flags": flags,
            "race_type": rt,
            "templates": TEMPLATES[rt],
        })

    best = None

    for _ in range(ITERATIONS_PER_ROUND):
        system_rows = []
        rows_count = 1
        hit_count = 0

        for rd in race_data:
            template = random.choice(rd["templates"])
            selected = pick_horses_by_template(rd["race"], template)

            rows_count *= len(selected)

            if rows_count > MAX_ROWS:
                break

            winner = rd["race"][rd["race"]["won"] == 1].iloc[0]
            hit = int(winner["horse"] in selected["horse"].tolist())
            hit_count += hit

            system_rows.append({
                "race_id": rd["race_id"],
                "race_no": winner["race_no"],
                "race_type": rd["race_type"],
                "template": "-".join(map(str, template)),
                "selected_count": len(selected),
                "selected": " | ".join(selected["horse"].tolist()),
                "selected_ranks": ",".join(map(str, selected["model_rank"].astype(int).tolist())),
                "min_selected_percent": selected["percent"].min(),
                "max_selected_percent": selected["percent"].max(),
                "avg_selected_percent": selected["percent"].mean(),
                "has_rank1": int((selected["model_rank"] == 1).any()),
                "has_rank4plus": int((selected["model_rank"] >= 4).any()),
                "has_rank7plus": int((selected["model_rank"] >= 7).any()),
                "big_favorite_included": int((selected["percent"] >= 50).any()),
                "winner": winner["horse"],
                "winner_rank": int(winner["model_rank"]),
                "winner_percent": winner["percent"],
                "hit": hit,
            })

        if rows_count > MAX_ROWS or len(system_rows) != len(race_data):
            continue

        score = profile_score(system_rows)

        # Tiebreaker: fler träffar, men profilscore viktigast
        final_score = score + hit_count * 25

        if best is None or final_score > best["final_score"]:
            best = {
                "final_score": final_score,
                "profile_score": score,
                "hits": hit_count,
                "rows": rows_count,
                "system_rows": system_rows,
            }

    return best


round_results = []
detail_rows = []

for date, round_df in df.groupby("date"):
    best = simulate_round(round_df)

    if best is None:
        continue

    payout_value = round_df["payout_8_value"].iloc[0]
    is_100k = int(payout_value >= 100000)

    system_rows = best["system_rows"]

    rank1_included = sum(r["has_rank1"] for r in system_rows)
    rank4plus_lopp = sum(r["has_rank4plus"] for r in system_rows)
    rank7plus_lopp = sum(r["has_rank7plus"] for r in system_rows)
    big_fav_count = sum(r["big_favorite_included"] for r in system_rows)
    scenario_percent_sum = sum(r["avg_selected_percent"] for r in system_rows)

    round_results.append({
        "date": date,
        "payout_8_value": payout_value,
        "is_100k": is_100k,
        "rows": best["rows"],
        "hits": best["hits"],
        "eight_right": int(best["hits"] >= 8),
        "seven_right": int(best["hits"] == 7),
        "six_right": int(best["hits"] == 6),
        "profile_score": round(best["profile_score"], 2),
        "rank1_included_lopp": rank1_included,
        "rank4plus_lopp": rank4plus_lopp,
        "rank7plus_lopp": rank7plus_lopp,
        "big_favorite_count": big_fav_count,
        "scenario_percent_sum": round(scenario_percent_sum, 2),
    })

    for r in system_rows:
        r["date"] = date
        r["payout_8_value"] = payout_value
        r["is_100k"] = is_100k
        r["round_rows"] = best["rows"]
        r["round_hits"] = best["hits"]
        detail_rows.append(r)


rounds = pd.DataFrame(round_results)
details = pd.DataFrame(detail_rows)

summary = pd.DataFrame([{
    "rounds": len(rounds),
    "avg_rows": round(rounds["rows"].mean(), 1),
    "max_rows": int(rounds["rows"].max()),
    "eight_right": int(rounds["eight_right"].sum()),
    "seven_right": int(rounds["seven_right"].sum()),
    "six_right": int(rounds["six_right"].sum()),
    "avg_hits": round(rounds["hits"].mean(), 3),
    "best_hits": int(rounds["hits"].max()),
    "avg_rank1_included_lopp": round(rounds["rank1_included_lopp"].mean(), 2),
    "avg_rank4plus_lopp": round(rounds["rank4plus_lopp"].mean(), 2),
    "avg_rank7plus_lopp": round(rounds["rank7plus_lopp"].mean(), 2),
    "avg_scenario_percent_sum": round(rounds["scenario_percent_sum"].mean(), 2),
}])

print()
print("=" * 120)
print("100K PROFILE GENERATOR MAX 540")
print("=" * 120)
print(summary.to_string(index=False))

print()
print("=" * 120)
print("BÄSTA OMGÅNGAR")
print("=" * 120)
print(
    rounds.sort_values(
        ["hits", "payout_8_value"],
        ascending=[False, False]
    ).head(50).to_string(index=False)
)

rounds.to_csv("100k_profile_generator_rounds.csv", index=False, encoding="utf-8-sig")
details.to_csv("100k_profile_generator_details.csv", index=False, encoding="utf-8-sig")
summary.to_csv("100k_profile_generator_summary.csv", index=False, encoding="utf-8-sig")

print()
print("Sparat:")
print("100k_profile_generator_summary.csv")
print("100k_profile_generator_rounds.csv")
print("100k_profile_generator_details.csv")
import pandas as pd
import random
from math import prod

ITERATIONS = 300
MAX_ROWS = 540
random.seed(42)

df = pd.read_csv("ml_dataset.csv").fillna(0)
payout = pd.read_csv("payout_vs_winner_percent_rounds.csv")
payout = payout[["date", "payout_8_value"]].drop_duplicates("date")
df = df.merge(payout, on="date", how="left")


def open_lopp(race):
    scores = {int(r["model_rank"]): r["total_score"] for _, r in race.iterrows()}
    r1 = scores.get(1, 0)
    return r1 - scores.get(8, 0) < 70 and r1 - scores.get(3, 0) < 30 and r1 - scores.get(4, 0) < 30


def get_flags(race):
    w = race[race["won"] == 1].iloc[0]
    r1 = race[race["model_rank"] == 1]
    r2 = race[race["model_rank"] == 2]

    score_gap = 999
    spike_gap = 999
    rank1_spike = 0

    if len(r1):
        rank1_spike = r1.iloc[0]["spike_score"]
    if len(r1) and len(r2):
        score_gap = r1.iloc[0]["total_score"] - r2.iloc[0]["total_score"]
        spike_gap = r1.iloc[0]["spike_score"] - r2.iloc[0]["spike_score"]

    value = race[
        race["model_rank"].between(4, 7)
        & race["total_score"].between(125, 134)
        & (race["spike_score"] >= 105)
    ]

    has_value = len(value) > 0
    top3_sum = race.nlargest(3, "percent")["percent"].sum()
    total_sum = race["total_score"].sum()
    spike_sum = race["spike_score"].sum()
    is_open = open_lopp(race)

    return {
        "value_horses": set(value["horse"].tolist()),
        "level1": has_value and w["spread"] < 70,
        "level2": is_open and has_value,
        "level3": is_open and has_value and 65 <= top3_sum < 75,
        "top3": total_sum >= 1538,
        "open": is_open,
        "compact": total_sum <= 1165 or spike_sum <= 1097,
        "trap": has_value and (score_gap < 10 or spike_gap < 25 or rank1_spike < 175),
    }


def rt(f):
    if f["level3"]:
        return "level3"
    if f["level2"]:
        return "level2"
    if f["level1"]:
        return "level1"
    if f["top3"]:
        return "top3"
    if f["open"]:
        return "open"
    if f["compact"]:
        return "compact"
    return "normal"


def random_profile(i):
    return {
        "id": i,
        "counts": {
            "level3": random.randint(4, 8),
            "level2": random.randint(3, 7),
            "level1": random.randint(3, 6),
            "top3": random.randint(3, 7),
            "open": random.randint(2, 6),
            "compact": random.randint(1, 3),
            "normal": random.randint(1, 4),
        },
        "remove_rank1_trap": random.choice([0, 0, 0, 1]),
        "remove_rank1_level3": random.choice([0, 0, 1]),
        "long_bonus": random.randint(0, 120),
        "value_bonus": random.randint(40, 140),
        "trap_rank1_penalty": random.randint(0, 140),
    }


def score(row, f, p):
    rank = int(row["model_rank"])
    horse = row["horse"]
    pct = float(row["percent"])
    s = float(row["total_score"])
    spike = float(row["spike_score"])

    val = 200 - rank * 10

    if rank <= 5:
        val += 60 - rank * 5

    if horse in f["value_horses"]:
        val += p["value_bonus"]

    if f["level3"] and 6 <= rank <= 11:
        val += p["long_bonus"]

    if f["level2"] and 5 <= rank <= 9:
        val += p["long_bonus"] * 0.4

    if f["trap"] and rank == 1:
        val -= p["trap_rank1_penalty"]

    if f["trap"] and 2 <= rank <= 8:
        val += 35

    if f["top3"] and 5 <= rank <= 10:
        val += 25

    if pct <= 10:
        val += 15

    if spike >= 150:
        val += 10

    if s >= 120:
        val += 6

    return val


def trim(data):
    prio = {"normal": 1, "compact": 2, "open": 3, "level1": 4, "top3": 5, "level2": 6, "level3": 7}

    while prod([x["wanted"] for x in data]) > MAX_ROWS:
        cand = [x for x in data if x["wanted"] > 1]
        if not cand:
            break
        c = sorted(cand, key=lambda x: (prio[x["rt"]], -x["wanted"]))[0]
        c["wanted"] -= 1

    return data


def simulate_round(round_df, profile):
    data = []

    for race_id, race in round_df.groupby("race_id"):
        f = get_flags(race)
        race_type = rt(f)

        data.append({
            "race_id": race_id,
            "race": race.copy(),
            "flags": f,
            "rt": race_type,
            "wanted": profile["counts"][race_type],
        })

    data = trim(data)

    hits = 0
    rows = prod([x["wanted"] for x in data])

    for d in data:
        race = d["race"].copy()
        f = d["flags"]

        if profile["remove_rank1_trap"] and f["trap"]:
            race = race[race["model_rank"] != 1].copy()

        if profile["remove_rank1_level3"] and f["level3"]:
            race = race[race["model_rank"] != 1].copy()

        race["pick_score"] = race.apply(lambda r: score(r, f, profile), axis=1)

        selected = set(f["value_horses"]).intersection(set(race["horse"]))
        ordered = race.sort_values(["pick_score", "total_score"], ascending=False)

        for _, row in ordered.iterrows():
            if len(selected) >= d["wanted"]:
                break
            selected.add(row["horse"])

        if len(selected) > d["wanted"]:
            selected = set(
                ordered[ordered["horse"].isin(selected)]
                .head(d["wanted"])["horse"]
                .tolist()
            )

        winner = d["race"][d["race"]["won"] == 1].iloc[0]["horse"]

        if winner in selected:
            hits += 1

    return hits, rows


high_dates = payout[payout["payout_8_value"] >= 100000]["date"].drop_duplicates().tolist()

results = []

for i in range(ITERATIONS):
    if i % 25 == 0:
        print(f"{i}/{ITERATIONS}")

    profile = random_profile(i)

    round_hits = []
    round_rows = []

    for date in high_dates:
        round_df = df[df["date"] == date].copy()

        hits, rows = simulate_round(round_df, profile)

        round_hits.append(hits)
        round_rows.append(rows)

    results.append({
        "profile_id": i,
        "eight_right": sum(1 for h in round_hits if h >= 8),
        "seven_right": sum(1 for h in round_hits if h == 7),
        "six_right": sum(1 for h in round_hits if h == 6),
        "avg_hits": round(sum(round_hits) / len(round_hits), 3),
        "best_hits": max(round_hits),
        "avg_rows": round(sum(round_rows) / len(round_rows), 1),
        "max_rows": max(round_rows),
        **profile["counts"],
        "remove_rank1_trap": profile["remove_rank1_trap"],
        "remove_rank1_level3": profile["remove_rank1_level3"],
        "long_bonus": profile["long_bonus"],
        "value_bonus": profile["value_bonus"],
        "trap_rank1_penalty": profile["trap_rank1_penalty"],
    })

res = pd.DataFrame(results).sort_values(
    ["eight_right", "seven_right", "six_right", "avg_hits"],
    ascending=False
)

print()
print("=" * 100)
print("TOPP 30 RANDOMPROFILER")
print("=" * 100)
print(res.head(30).to_string(index=False))

res.to_csv("optimized_100k_random_profiles_540.csv", index=False, encoding="utf-8-sig")

print()
print("Sparat:")
print("optimized_100k_random_profiles_540.csv")
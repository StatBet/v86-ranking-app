import pandas as pd
from math import prod

MAX_TOTAL_ROWS = 540

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


def flags(race):
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

    top3_sum = race.nlargest(3, "percent")["percent"].sum()
    total_sum = race["total_score"].sum()
    spike_sum = race["spike_score"].sum()
    open_lopp = is_open_lopp(race)
    has_value = len(value) > 0

    return {
        "open": open_lopp,
        "has_value": has_value,
        "value_horses": set(value["horse"].tolist()),
        "level1": has_value and w["spread"] < 70,
        "level2": open_lopp and has_value,
        "level3": open_lopp and has_value and 65 <= top3_sum < 75,
        "top3_warning": total_sum >= 1538,
        "compact": total_sum <= 1165 or spike_sum <= 1097,
        "trap": has_value and (
            score_gap < 10
            or spike_gap < 25
            or rank1_spike < 175
        ),
    }


def race_type(f):
    if f["level3"]:
        return "level3"
    if f["level2"]:
        return "level2"
    if f["level1"]:
        return "level1"
    if f["top3_warning"]:
        return "top3"
    if f["open"]:
        return "open"
    if f["compact"]:
        return "compact"
    return "normal"


SYSTEMS = [
    {
        "name": "value_aggressive",
        "budget": 180,
        "style": "value",
        "counts": {"level3": 6, "level2": 5, "level1": 5, "top3": 4, "open": 3, "compact": 1, "normal": 2},
    },
    {
        "name": "level3_longs",
        "budget": 180,
        "style": "longs",
        "counts": {"level3": 7, "level2": 4, "level1": 3, "top3": 5, "open": 3, "compact": 1, "normal": 2},
    },
    {
        "name": "trap_no_rank1",
        "budget": 180,
        "style": "trap",
        "counts": {"level3": 6, "level2": 5, "level1": 4, "top3": 5, "open": 3, "compact": 1, "normal": 2},
    },
]


def horse_score(row, f, style):
    rank = int(row["model_rank"])
    horse = row["horse"]
    pct = float(row["percent"])
    score = float(row["total_score"])
    spike = float(row["spike_score"])

    p = 200 - rank * 10

    if style == "value":
        if rank <= 5:
            p += 70 - rank * 5
        if horse in f["value_horses"]:
            p += 120
        if f["level2"] and 5 <= rank <= 9:
            p += 35

    elif style == "longs":
        if f["level3"] and 6 <= rank <= 11:
            p += 150
        elif rank <= 4:
            p += 45 - rank * 3
        if horse in f["value_horses"]:
            p += 80
        if pct <= 10:
            p += 25

    elif style == "trap":
        if f["trap"] and rank == 1:
            p -= 160
        if f["trap"] and 2 <= rank <= 8:
            p += 80
        if rank <= 5:
            p += 45
        if horse in f["value_horses"]:
            p += 90

    if spike >= 150:
        p += 10
    if score >= 120:
        p += 6
    if pct <= 10:
        p += 10

    return p


def trim(data, budget):
    while prod([x["wanted"] for x in data]) > budget:
        cand = [x for x in data if x["wanted"] > 1]
        if not cand:
            break
        cand = sorted(cand, key=lambda x: (x["priority"], -x["wanted"]))
        cand[0]["wanted"] -= 1
    return data


def build_system(round_df, system):
    data = []

    priority = {
        "compact": 1,
        "normal": 2,
        "open": 3,
        "level1": 4,
        "top3": 5,
        "level2": 6,
        "level3": 7,
    }

    for race_id, race in round_df.groupby("race_id"):
        race = race.copy()
        f = flags(race)
        rt = race_type(f)

        data.append({
            "race_id": race_id,
            "race": race,
            "flags": f,
            "race_type": rt,
            "wanted": system["counts"][rt],
            "priority": priority[rt],
        })

    data = trim(data, system["budget"])

    selections = {}
    details = []

    for d in data:
        race = d["race"].copy()
        f = d["flags"]

        if system["style"] == "trap" and f["trap"]:
            race = race[race["model_rank"] != 1].copy()

        race["score_pick"] = race.apply(lambda r: horse_score(r, f, system["style"]), axis=1)
        ordered = race.sort_values(["score_pick", "total_score"], ascending=False)

        selected = set(f["value_horses"])
        selected = selected.intersection(set(ordered["horse"]))

        for _, row in ordered.iterrows():
            if len(selected) >= d["wanted"]:
                break
            selected.add(row["horse"])

        selected = list(selected)

        if len(selected) > d["wanted"]:
            selected = ordered[ordered["horse"].isin(selected)].head(d["wanted"])["horse"].tolist()

        selections[d["race_id"]] = set(selected)

        winner = d["race"][d["race"]["won"] == 1].iloc[0]

        details.append({
            "race_id": d["race_id"],
            "race_no": winner["race_no"],
            "system": system["name"],
            "race_type": d["race_type"],
            "wanted": len(selected),
            "winner": winner["horse"],
            "winner_rank": int(winner["model_rank"]),
            "winner_percent": winner["percent"],
            "hit": int(winner["horse"] in selected),
            "picked": " | ".join(selected),
        })

    rows = prod([len(v) for v in selections.values()])
    hits = sum(x["hit"] for x in details)

    return selections, rows, hits, details


high_dates = payout[payout["payout_8_value"] >= 100000]["date"].drop_duplicates().tolist()

round_rows = []
details_all = []

for date in high_dates:
    round_df = df[df["date"] == date].copy()
    payout_value = round_df["payout_8_value"].iloc[0]

    system_results = []

    for system in SYSTEMS:
        selections, rows, hits, details = build_system(round_df, system)
        system_results.append((system["name"], selections, rows, hits))

        for d in details:
            d["date"] = date
            d["payout_8_value"] = payout_value
            details_all.append(d)

    # Multisystem: rätt om något av delsystemen har vinnaren i varje avdelning
    combined_hits = 0

    for race_id, race in round_df.groupby("race_id"):
        winner = race[race["won"] == 1].iloc[0]["horse"]

        if any(winner in selections[race_id] for _, selections, _, _ in system_results):
            combined_hits += 1

    total_rows = sum(r for _, _, r, _ in system_results)

    round_rows.append({
        "date": date,
        "payout_8_value": payout_value,
        "total_rows": total_rows,
        "combined_hits": combined_hits,
        "eight_right": int(combined_hits >= 8),
        "seven_right": int(combined_hits == 7),
        "six_right": int(combined_hits == 6),
        "system_hits": " | ".join(f"{n}:{h}/{r}" for n, _, r, h in system_results),
    })

rounds = pd.DataFrame(round_rows)
details = pd.DataFrame(details_all)

summary = pd.DataFrame([{
    "rounds": len(rounds),
    "avg_rows": round(rounds["total_rows"].mean(), 1),
    "max_rows": int(rounds["total_rows"].max()),
    "eight_right": int(rounds["eight_right"].sum()),
    "seven_right": int(rounds["seven_right"].sum()),
    "six_right": int(rounds["six_right"].sum()),
    "avg_hits": round(rounds["combined_hits"].mean(), 3),
    "best_hits": int(rounds["combined_hits"].max()),
}])

print()
print("=" * 100)
print("MULTISYSTEM 540")
print("=" * 100)
print(summary.to_string(index=False))

print()
print(rounds.sort_values(["combined_hits", "payout_8_value"], ascending=[False, False]).to_string(index=False))

summary.to_csv("multisystem_540_summary.csv", index=False, encoding="utf-8-sig")
rounds.to_csv("multisystem_540_rounds.csv", index=False, encoding="utf-8-sig")
details.to_csv("multisystem_540_details.csv", index=False, encoding="utf-8-sig")

print()
print("Sparat:")
print("multisystem_540_summary.csv")
print("multisystem_540_rounds.csv")
print("multisystem_540_details.csv")
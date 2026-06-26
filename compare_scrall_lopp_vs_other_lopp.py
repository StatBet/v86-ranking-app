import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rows = []

for race_id, race in df.groupby("race_id"):
    winner = race[race["won"] == 1]
    if winner.empty:
        continue

    w = winner.iloc[0]

    scores = {int(r["model_rank"]): r["total_score"] for _, r in race.iterrows()}
    r1 = scores.get(1, 0)

    spread = r1 - scores.get(8, 0)
    gap_1_2 = r1 - scores.get(2, 0)
    gap_1_3 = r1 - scores.get(3, 0)
    gap_1_4 = r1 - scores.get(4, 0)
    gap_1_5 = r1 - scores.get(5, 0)

    total_sum = race["total_score"].sum()
    spike_sum = race["spike_score"].sum()

    value = race[
        race["model_rank"].between(4, 7)
        & race["total_score"].between(125, 134)
        & (race["spike_score"] >= 105)
    ]

    plus = race[
        race["model_rank"].between(3, 5)
        & race["total_score"].between(125, 134)
        & (race["spike_score"] >= 150)
    ]

    rows.append({
        "race_id": race_id,
        "date": w["date"],
        "race_no": w["race_no"],
        "winner": w["horse"],
        "winner_rank": int(w["model_rank"]),
        "winner_percent": w["percent"],

        "spread": spread,
        "gap_1_2": gap_1_2,
        "gap_1_3": gap_1_3,
        "gap_1_4": gap_1_4,
        "gap_1_5": gap_1_5,
        "total_sum": total_sum,
        "spike_sum": spike_sum,

        "value_count": len(value),
        "plus_count": len(plus),
        "has_value": int(len(value) > 0),
        "has_plus": int(len(plus) > 0),
        "value_won": int(value["won"].sum()),
        "plus_won": int(plus["won"].sum()),

        "field_size": int(w["field_size"]),
        "rank1_percent": race[race["model_rank"] == 1]["percent"].iloc[0] if len(race[race["model_rank"] == 1]) else 0,
        "rank1_score": race[race["model_rank"] == 1]["total_score"].iloc[0] if len(race[race["model_rank"] == 1]) else 0,
        "rank1_spike": race[race["model_rank"] == 1]["spike_score"].iloc[0] if len(race[race["model_rank"] == 1]) else 0,
    })

races = pd.DataFrame(rows)

levels = [5, 10, 15]
params = [
    "spread",
    "gap_1_2",
    "gap_1_3",
    "gap_1_4",
    "gap_1_5",
    "total_sum",
    "spike_sum",
    "value_count",
    "plus_count",
    "has_value",
    "has_plus",
    "field_size",
    "rank1_percent",
    "rank1_score",
    "rank1_spike",
]

summary_rows = []

for pct in levels:
    scrall = races[races["winner_percent"] <= pct]
    other = races[races["winner_percent"] > pct]

    for p in params:
        summary_rows.append({
            "winner_percent_level": f"<={pct}%",
            "parameter": p,
            "scrall_avg": round(scrall[p].mean(), 2) if len(scrall) else 0,
            "other_avg": round(other[p].mean(), 2) if len(other) else 0,
            "difference": round((scrall[p].mean() if len(scrall) else 0) - (other[p].mean() if len(other) else 0), 2),
        })

summary = pd.DataFrame(summary_rows)

print("\n" + "=" * 100)
print("SKRÄLLOPP VS ÖVRIGA LOPP")
print("=" * 100)
for lvl in summary["winner_percent_level"].unique():
    print("\n" + "-" * 100)
    print(lvl)
    print("-" * 100)
    print(
        summary[summary["winner_percent_level"] == lvl]
        .sort_values("difference")
        .to_string(index=False)
    )

summary.to_csv("scrall_lopp_vs_other_lopp_summary.csv", index=False, encoding="utf-8-sig")
races.to_csv("scrall_lopp_vs_other_lopp_details.csv", index=False, encoding="utf-8-sig")

print("\nSparat:")
print("scrall_lopp_vs_other_lopp_summary.csv")
print("scrall_lopp_vs_other_lopp_details.csv")
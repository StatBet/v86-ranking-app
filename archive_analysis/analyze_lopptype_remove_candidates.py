import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

def race_metrics(race):
    scores = {int(r["model_rank"]): r["total_score"] for _, r in race.iterrows()}
    r1 = scores.get(1, 0)
    return {
        "gap_1_3": r1 - scores.get(3, 0),
        "gap_1_4": r1 - scores.get(4, 0),
        "spread_1_8": r1 - scores.get(8, 0),
    }

rows = []

for race_id, race in df.groupby("race_id"):
    m = race_metrics(race)

    for _, horse in race.iterrows():
        if not 4 <= horse["model_rank"] <= 8:
            continue

        rows.append({
            **horse.to_dict(),
            **m,
            "type_gap13_30": m["gap_1_3"] >= 30,
            "type_gap14_40": m["gap_1_4"] >= 40,
            "type_spread70": m["spread_1_8"] >= 70,
        })

x = pd.DataFrame(rows)

tests = [
    ("spike <= 80", x["spike_score"] <= 80),
    ("spike <= 100", x["spike_score"] <= 100),
    ("spike <= 120", x["spike_score"] <= 120),
    ("driver = 0", x["driver_score"] == 0),
    ("latest <= 3", x["latest_start_score"] <= 3),
    ("form <= 15", x["form_score"] <= 15),
    ("form <= 20", x["form_score"] <= 20),
    ("win% <= 10", x["win_percent"] <= 10),
    ("win% <= 15", x["win_percent"] <= 15),
    ("place% <= 35", x["place_percent"] <= 35),
    ("avg_odds > 15", x["avg_odds"] > 15),
    ("avg_odds > 20", x["avg_odds"] > 20),
    ("percent <= 4", x["percent"] <= 4),
    ("percent <= 9", x["percent"] <= 9),
    ("post >= 8", x["post"] >= 8),
    ("post >= 10", x["post"] >= 10),
    (
        "loser B",
        (
            (x["spike_score"] <= 120)
            & (x["driver_score"] == 0)
            & (x["latest_start_score"] <= 3)
            & (x["form_score"] <= 20)
            & (x["avg_odds"] > 15)
        )
        | (x["spike_score"] <= 50)
    ),
    (
        "loser C",
        (x["percent"] <= 4) & (x["spike_score"] <= 100)
    ),
]

groups = [
    ("gap_1_3 >= 30", x["type_gap13_30"]),
    ("gap_1_4 >= 40", x["type_gap14_40"]),
    ("spread_1_8 >= 70", x["type_spread70"]),
]

print("=" * 80)
print("TA BORT-KANDIDATER INOM LOPPTYPER")
print("=" * 80)

for group_name, group_mask in groups:
    group = x[group_mask]

    print()
    print("=" * 80)
    print(group_name)
    print("=" * 80)

    print("Rank 4-8 kandidater:", len(group))
    print("Vinnare bland rank 4-8:", int(group["won"].sum()))

    results = []

    for test_name, test_mask in tests:
        subset = x[group_mask & test_mask]

        if len(subset) == 0:
            continue

        results.append({
            "filter": test_name,
            "removed": len(subset),
            "lost_winners": int(subset["won"].sum()),
            "winner_pct": round(subset["won"].mean() * 100, 2),
        })

    res = pd.DataFrame(results)

    print()
    print(
        res.sort_values(
            ["lost_winners", "removed"],
            ascending=[True, False]
        )
        .head(25)
        .to_string(index=False)
    )
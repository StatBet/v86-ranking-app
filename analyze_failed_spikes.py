import pandas as pd

DATASET = "ml_dataset.csv"

df = pd.read_csv(DATASET)

df = df[df["won"].isin([0, 1])]

results = []

for race_id, race in df.groupby("race_id"):

    race = race.sort_values(
        "total_score",
        ascending=False
    ).reset_index(drop=True)

    if len(race) < 2:
        continue

    top = race.iloc[0]
    second = race.iloc[1]

    score_gap = (
        top["total_score"]
        - second["total_score"]
    )

    results.append({
        "won": int(top["won"]),
        "score_gap": score_gap,
        "win_percent": top["win_percent"],
        "place_percent": top["place_percent"],
        "avg_odds": top["avg_odds"],
        "avg_time": top["avg_time"],
        "post": top["post"],
        "field_size": top["field_size"],
        "form_score": top["form_score"],
        "driver_score": top["driver_score"]
    })

analysis = pd.DataFrame(results)

correct = analysis[
    analysis["won"] == 1
]

failed = analysis[
    analysis["won"] == 0
]

print("=" * 80)
print("RÄTTA SPIKAR")
print("=" * 80)
print(correct.mean(numeric_only=True))

print()
print("=" * 80)
print("FELSPIKAR")
print("=" * 80)
print(failed.mean(numeric_only=True))

print()
print("=" * 80)
print("SCORE GAP ANALYS")
print("=" * 80)

for gap in [5, 10, 15, 20, 25, 30]:

    subset = analysis[
        analysis["score_gap"] >= gap
    ]

    if len(subset) == 0:
        continue

    hitrate = round(
        subset["won"].mean() * 100,
        1
    )

    print(
        f"Gap >= {gap:2}: "
        f"{hitrate}% "
        f"({len(subset)} lopp)"
    )
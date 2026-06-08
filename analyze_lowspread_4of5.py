import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

race_spread = {}

for race_id, race in df.groupby("race_id"):

    ranked = race.sort_values("model_rank")

    if len(ranked) < 8:
        continue

    rank1 = ranked[ranked["model_rank"] == 1]
    rank8 = ranked[ranked["model_rank"] == 8]

    if len(rank1) == 0 or len(rank8) == 0:
        continue

    spread = (
        rank1.iloc[0]["total_score"]
        - rank8.iloc[0]["total_score"]
    )

    race_spread[race_id] = spread

df["spread"] = df["race_id"].map(race_spread)

df["criteria"] = 0

df["criteria"] += (df["win_percent"] >= 20).astype(int)
df["criteria"] += (df["place_percent"] >= 45).astype(int)
df["criteria"] += (df["form_score"] >= 20).astype(int)
df["criteria"] += (df["latest_start_score"] >= 5).astype(int)
df["criteria"] += (df["avg_odds"] <= 15).astype(int)

subset = df[
    (df["model_rank"].between(6,8))
    &
    (df["spread"] <= 51)
]

print("=" * 80)
print("4 AV 5 I LÅG SPREAD")
print("=" * 80)

for needed in [3,4,5]:

    test = subset[
        subset["criteria"] >= needed
    ]

    winners = int(test["won"].sum())

    pct = (
        winners / len(test) * 100
        if len(test)
        else 0
    )

    print()
    print(f"{needed} av 5")
    print("-" * 40)
    print("Kandidater:", len(test))
    print("Vinnare:", winners)
    print("Träff%:", round(pct,1))
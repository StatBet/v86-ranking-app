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
    (df["model_rank"].between(6, 8))
    &
    (df["spread"] <= 51)
    &
    (df["criteria"] >= 4)
]

print("=" * 80)
print("4 AV 5 + LÅG SPREAD")
print("=" * 80)

print()
print("Kandidater:", len(subset))
print("Vinnare:", int(subset["won"].sum()))

if len(subset):
    print(
        "Träff%:",
        round(
            subset["won"].mean() * 100,
            1
        )
    )
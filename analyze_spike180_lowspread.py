import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)
df["spike_score"] = (
    df["win_percent"] * 2
    + df["place_percent"]
    + df["form_score"] * 1.5
)

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

subset = df[
    (df["model_rank"].between(6, 8))
    &
    (df["spread"] <= 51)
    &
    (df["spike_score"] >= 170)
]

print("=" * 80)
print("SPIKE >=170 + LÅG SPREAD")
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
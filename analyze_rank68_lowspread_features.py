import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

race_info = {}

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

    race_info[race_id] = spread

df["spread"] = df["race_id"].map(race_info)

subset = df[
    (df["model_rank"].between(6, 8))
    &
    (df["spread"] <= 51)
]

winners = subset[subset["won"] == 1]
losers = subset[subset["won"] == 0]

cols = [
    "win_percent",
    "place_percent",
    "form_score",
    "latest_start_score",
    "avg_odds"
]

print("=" * 80)
print("LÅG SPREAD - RANK 6-8")
print("=" * 80)

print()
print("VINNARE")
print("-" * 40)
print(winners[cols].mean().round(2).to_string())

print()
print("FÖRLORARE")
print("-" * 40)
print(losers[cols].mean().round(2).to_string())

print()
print("DIFFERENS")
print("-" * 40)
print(
    (
        winners[cols].mean()
        - losers[cols].mean()
    ).round(2).to_string()
)
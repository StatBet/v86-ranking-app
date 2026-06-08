import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rows = []

for race_id, race in df.groupby("race_id"):

    ranked = race.sort_values("model_rank")

    if len(ranked) < 8:
        continue

    winner_rows = ranked[ranked["won"] == 1]

    if len(winner_rows) == 0:
        continue

    winner = winner_rows.iloc[0]

    rank1 = ranked[ranked["model_rank"] == 1]
    rank8 = ranked[ranked["model_rank"] == 8]

    if len(rank1) == 0 or len(rank8) == 0:
        continue

    rank1 = rank1.iloc[0]
    rank8 = rank8.iloc[0]

    spread = (
        rank1["total_score"]
        - rank8["total_score"]
    )

    rows.append({
        "winner_rank": winner["model_rank"],
        "spread": spread
    })

res = pd.DataFrame(rows)

top5 = res[
    res["winner_rank"] <= 5
]

rank68 = res[
    res["winner_rank"].between(6, 8)
]

print("=" * 80)
print("RACE SPREAD")
print("=" * 80)

print()
print("TOP5-VINNARE")
print("-" * 40)

print(
    top5["spread"]
    .describe()
    .round(2)
    .to_string()
)

print()
print("RANK 6-8-VINNARE")
print("-" * 40)

print(
    rank68["spread"]
    .describe()
    .round(2)
    .to_string()
)

print()
print("=" * 80)
print("SNITT")
print("=" * 80)

print(
    "Top5:",
    round(top5["spread"].mean(), 2)
)

print(
    "Rank6-8:",
    round(rank68["spread"].mean(), 2)
)

print(
    "Skillnad:",
    round(
        rank68["spread"].mean()
        -
        top5["spread"].mean(),
        2
    )
)
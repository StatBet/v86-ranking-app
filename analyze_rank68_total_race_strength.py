import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rows = []

for race_id, race in df.groupby("race_id"):

    ranked = (
        race
        .sort_values("model_rank")
        .head(8)
    )

    if len(ranked) < 8:
        continue

    winner_rows = ranked[
        ranked["won"] == 1
    ]

    if len(winner_rows) == 0:
        continue

    winner = winner_rows.iloc[0]

    total_strength = (
        ranked["total_score"]
        .sum()
    )

    avg_strength = (
        ranked["total_score"]
        .mean()
    )

    rows.append({
        "winner_rank": winner["model_rank"],
        "total_strength": total_strength,
        "avg_strength": avg_strength
    })

res = pd.DataFrame(rows)

top5 = res[
    res["winner_rank"] <= 5
]

rank68 = res[
    res["winner_rank"].between(6, 8)
]

print("=" * 80)
print("TOTAL STYRKA I LOPPET")
print("=" * 80)

print()
print("TOP5-VINNARE")
print("-" * 40)

print(
    top5[
        [
            "total_strength",
            "avg_strength"
        ]
    ]
    .mean()
    .round(2)
    .to_string()
)

print()
print("RANK 6-8-VINNARE")
print("-" * 40)

print(
    rank68[
        [
            "total_strength",
            "avg_strength"
        ]
    ]
    .mean()
    .round(2)
    .to_string()
)

print()
print("=" * 80)
print("DIFFERENS")
print("=" * 80)

diff = (
    rank68[
        [
            "total_strength",
            "avg_strength"
        ]
    ].mean()
    -
    top5[
        [
            "total_strength",
            "avg_strength"
        ]
    ].mean()
)

print(
    diff
    .round(2)
    .to_string()
)
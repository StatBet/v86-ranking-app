import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rows = []

for race_id, race in df.groupby("race_id"):

    ranked = race.sort_values(
        "model_rank"
    )

    if len(ranked) < 8:
        continue

    winner_rows = ranked[
        ranked["won"] == 1
    ]

    if len(winner_rows) == 0:
        continue

    winner = winner_rows.iloc[0]

    rank1 = ranked[
        ranked["model_rank"] == 1
    ].iloc[0]

    rank2 = ranked[
        ranked["model_rank"] == 2
    ].iloc[0]

    rank5 = ranked[
        ranked["model_rank"] == 5
    ].iloc[0]

    rank8 = ranked[
        ranked["model_rank"] == 8
    ].iloc[0]

    rows.append({
        "winner_rank": winner["model_rank"],

        "gap_1_8":
            rank1["total_score"]
            - rank8["total_score"],

        "gap_2_8":
            rank2["total_score"]
            - rank8["total_score"],

        "gap_1_winner":
            rank1["total_score"]
            - winner["total_score"],

        "gap_5_winner":
            rank5["total_score"]
            - winner["total_score"]
    })

res = pd.DataFrame(rows)

top5 = res[
    res["winner_rank"] <= 5
]

rank68 = res[
    res["winner_rank"].between(6, 8)
]

print("=" * 80)
print("VINNARE RANK 1-5")
print("=" * 80)

print(
    top5[
        [
            "gap_1_8",
            "gap_2_8",
            "gap_1_winner",
            "gap_5_winner"
        ]
    ]
    .mean()
    .round(2)
    .to_string()
)

print()
print("=" * 80)
print("VINNARE RANK 6-8")
print("=" * 80)

print(
    rank68[
        [
            "gap_1_8",
            "gap_2_8",
            "gap_1_winner",
            "gap_5_winner"
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
            "gap_1_8",
            "gap_2_8",
            "gap_1_winner",
            "gap_5_winner"
        ]
    ].mean()
    -
    top5[
        [
            "gap_1_8",
            "gap_2_8",
            "gap_1_winner",
            "gap_5_winner"
        ]
    ].mean()
)

print(
    diff.round(2).to_string()
)
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

    if winner["model_rank"] not in [6,7,8]:
        continue

    rank5 = ranked[
        ranked["model_rank"] == 5
    ]

    if len(rank5) == 0:
        continue

    rank5 = rank5.iloc[0]

    rows.append({
        "winner_rank": winner["model_rank"],
        "gap_to_rank5":
            rank5["total_score"]
            - winner["total_score"]
    })

res = pd.DataFrame(rows)

print("=" * 80)
print("GAP TILL RANK 5")
print("=" * 80)

print(
    res.groupby("winner_rank")
    ["gap_to_rank5"]
    .agg(["count","mean","median"])
    .round(2)
    .to_string()
)
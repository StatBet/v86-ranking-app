import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[
    df["model_rank"].between(6, 8)
].copy()

winners = rank68[
    rank68["won"] == 1
]

losers = rank68[
    rank68["won"] == 0
]

cols = [
    "win_percent",
    "place_percent",
    "form_score",
    "latest_start_score",
    "avg_odds",
    "post"
]

print("=" * 80)
print("RANK 6-8 VINNARE")
print("=" * 80)

print(
    winners[cols]
    .mean()
    .round(2)
    .to_string()
)

print()
print("=" * 80)
print("RANK 6-8 FÖRLORARE")
print("=" * 80)

print(
    losers[cols]
    .mean()
    .round(2)
    .to_string()
)

print()
print("=" * 80)
print("DIFFERENS")
print("=" * 80)

diff = (
    winners[cols].mean()
    -
    losers[cols].mean()
)

print(
    diff
    .round(2)
    .to_string()
)
import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

winners = df[df["won"] == 1].copy()

top5 = winners[
    winners["model_rank"] <= 5
]

rank68 = winners[
    winners["model_rank"].between(6, 8)
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
print("TOP5 VINNARE")
print("=" * 80)

print()
print("Antal:")
print(len(top5))

print()
print(
    top5[cols]
    .mean()
    .round(2)
    .to_string()
)

print()
print("=" * 80)
print("RANK 6-8 VINNARE")
print("=" * 80)

print()
print("Antal:")
print(len(rank68))

print()
print(
    rank68[cols]
    .mean()
    .round(2)
    .to_string()
)

print()
print("=" * 80)
print("DIFFERENS")
print("=" * 80)

diff = (
    rank68[cols].mean()
    -
    top5[cols].mean()
)

print(
    diff
    .round(2)
    .to_string()
)
import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

print("=" * 80)
print("VINNARE MED LÄGST AVG_ODDS")
print("=" * 80)

winners = (
    df[df["won"] == 1]
    .sort_values("avg_odds")
    .head(20)
)

cols = []

for c in [
    "horse",
    "avg_odds",
    "history"
]:
    if c in winners.columns:
        cols.append(c)

print(winners[cols].to_string(index=False))

print()
print("=" * 80)
print("KOLUMNER")
print("=" * 80)

for c in df.columns:
    print(c)
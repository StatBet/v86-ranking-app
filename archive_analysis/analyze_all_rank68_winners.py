import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

winners = df[
    (df["model_rank"].between(6, 8))
    &
    (df["won"] == 1)
].copy()

print("=" * 80)
print("ALLA RANK 6-8 VINNARE")
print("=" * 80)

print()
print("Antal:", len(winners))

print()
print("=" * 80)
print("SNITT")
print("=" * 80)

numeric_cols = [
    c for c in winners.columns
    if pd.api.types.is_numeric_dtype(winners[c])
]

summary = (
    winners[numeric_cols]
    .mean()
    .sort_index()
    .round(2)
)

print(summary.to_string())

print()
print("=" * 80)
print("ALLA VINNARE")
print("=" * 80)

cols = []

priority_cols = [
    "date",
    "race_no",
    "horse",
    "model_rank",
    "total_score",
    "avg_odds",
    "win_percent",
    "place_percent",
    "form_score",
    "latest_start_score",
    "post",
    "won"
]

for c in priority_cols:
    if c in winners.columns:
        cols.append(c)

for c in winners.columns:
    if c not in cols:
        cols.append(c)

print(
    winners[cols]
    .sort_values(["date", "race_no"])
    .to_string(index=False)
)

print()
print("=" * 80)
print("KOLUMNER")
print("=" * 80)

for c in winners.columns:
    print(c)





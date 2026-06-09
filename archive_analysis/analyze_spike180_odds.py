import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

df["spike_score"] = (
    df["win_percent"] * 2
    + df["form_score"] * 1.5
    + df["place_percent"]
)

subset = df[
    (df["model_rank"].between(6, 8))
    &
    (df["spike_score"] >= 180)
].copy()

subset["odds_bucket"] = pd.cut(
    subset["avg_odds"],
    bins=[0, 5, 10, 20, 999],
    labels=["<5", "5-10", "10-20", "20+"]
)

print("=" * 80)
print("SPIKE >=180 ODDS")
print("=" * 80)

print(
    subset["odds_bucket"]
    .value_counts()
    .sort_index()
    .to_string()
)

print()
print("Vinnare per bucket")
print()

print(
    subset[subset["won"] == 1]
    ["odds_bucket"]
    .value_counts()
    .sort_index()
    .to_string()
)
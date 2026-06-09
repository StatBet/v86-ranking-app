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

print("=" * 80)
print("SPIKE >= 180")
print("=" * 80)

print()
print("Kandidater:", len(subset))
print("Vinnare:", int(subset["won"].sum()))

if len(subset):
    print(
        "Träff%:",
        round(
            subset["won"].sum()
            / len(subset)
            * 100,
            1
        )
    )

print()
print("=" * 80)
print("VINNARE")
print("=" * 80)

print(
    subset[
        subset["won"] == 1
    ][[
        "date",
        "race_no",
        "horse",
        "model_rank",
        "spike_score",
        "win_percent",
        "place_percent",
        "form_score",
        "avg_odds"
    ]]
    .sort_values(
        "spike_score",
        ascending=False
    )
    .to_string(index=False)
)
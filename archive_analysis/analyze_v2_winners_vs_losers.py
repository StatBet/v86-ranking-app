import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

# --------------------------------------------------
# Spike score
# --------------------------------------------------

df["spike_score"] = (
    df["win_percent"] * 2
    + df["place_percent"]
    + df["form_score"] * 1.5
)

# --------------------------------------------------
# Spread
# --------------------------------------------------

spreads = {}

for race_id, race in df.groupby("race_id"):

    r1 = race[race["model_rank"] == 1]
    r8 = race[race["model_rank"] == 8]

    if r1.empty or r8.empty:
        continue

    spreads[race_id] = (
        r1.iloc[0]["total_score"]
        - r8.iloc[0]["total_score"]
    )

df["spread"] = df["race_id"].map(spreads)

# --------------------------------------------------
# V2
# --------------------------------------------------

rank68 = df[
    df["model_rank"].between(6, 8)
].copy()

v2 = rank68[
    (rank68["spike_score"] >= 120)
    &
    (rank68["spread"] <= 50)
    &
    (rank68["total_score"] >= 105)
    &
    (rank68["avg_odds"] <= 15)
]

winners = v2[v2["won"] == 1]
losers = v2[v2["won"] == 0]

cols = [
    "total_score",
    "spike_score",
    "spread",
    "win_percent",
    "place_percent",
    "form_score",
    "latest_start_score",
    "avg_odds",
    "post"
]

print("=" * 80)
print("V2 VINNARE")
print("=" * 80)

print(
    winners[cols]
    .mean()
    .round(2)
    .to_string()
)

print()

print("=" * 80)
print("V2 FÖRLORARE")
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

print(
    (
        winners[cols].mean()
        -
        losers[cols].mean()
    )
    .round(2)
    .to_string()
)

print()

print("=" * 80)
print("V2 VINNARE DETALJER")
print("=" * 80)

print(
    winners[
        [
            "date",
            "race_no",
            "horse",
            "model_rank",
            "total_score",
            "spike_score",
            "spread",
            "win_percent",
            "place_percent",
            "form_score",
            "latest_start_score",
            "avg_odds",
            "post"
        ]
    ]
    .sort_values("spike_score", ascending=False)
    .to_string(index=False)
)
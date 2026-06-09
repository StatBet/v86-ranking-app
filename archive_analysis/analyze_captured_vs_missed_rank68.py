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
# Rank 6-8 vinnare
# --------------------------------------------------

rank68 = df[
    (df["model_rank"].between(6, 8))
    &
    (df["won"] == 1)
].copy()

# --------------------------------------------------
# V1
# --------------------------------------------------

v1 = df[
    (df["model_rank"].between(6, 8))
    &
    (df["spike_score"] >= 170)
    &
    (df["spread"] <= 51)
    &
    (df["total_score"].between(99, 139))
    &
    (df["won"] == 1)
]

# --------------------------------------------------
# V2
# --------------------------------------------------

v2 = df[
    (df["model_rank"].between(6, 8))
    &
    (df["spike_score"] >= 120)
    &
    (df["spread"] <= 50)
    &
    (df["total_score"] >= 105)
    &
    (df["avg_odds"] <= 15)
    &
    (df["won"] == 1)
]

captured_keys = set(
    pd.concat([v1, v2])[
        ["date", "race_no", "horse"]
    ].apply(tuple, axis=1)
)

rank68["captured"] = rank68[
    ["date", "race_no", "horse"]
].apply(tuple, axis=1).isin(captured_keys)

captured = rank68[
    rank68["captured"]
]

missed = rank68[
    ~rank68["captured"]
]

# --------------------------------------------------
# Parametrar
# --------------------------------------------------

cols = [
    "model_rank",
    "total_score",
    "spike_score",
    "spread",
    "win_percent",
    "place_percent",
    "form_score",
    "latest_start_score",
    "avg_odds",
    "post",
    "starts",
    "wins"
]

print("=" * 80)
print("FÅNGADE VINNARE")
print("=" * 80)

print(captured[cols].mean().round(2).to_string())

print()
print("=" * 80)
print("MISSADE VINNARE")
print("=" * 80)

print(missed[cols].mean().round(2).to_string())

print()
print("=" * 80)
print("DIFFERENS")
print("=" * 80)

print(
    (
        captured[cols].mean()
        -
        missed[cols].mean()
    )
    .round(2)
    .to_string()
)

print()
print("=" * 80)
print("FÖRDELNING MODELRANK")
print("=" * 80)

print()

print("Fångade:")
print(
    captured["model_rank"]
    .value_counts()
    .sort_index()
)

print()

print("Missade:")
print(
    missed["model_rank"]
    .value_counts()
    .sort_index()
)

print()
print("=" * 80)
print("MISSADE VINNARE")
print("=" * 80)

print(
    missed[
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
    .sort_values(
        "spike_score",
        ascending=False
    )
    .to_string(index=False)
)
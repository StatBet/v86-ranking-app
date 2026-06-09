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

rank68 = df[
    df["model_rank"].between(6, 8)
].copy()

# --------------------------------------------------
# V1
# --------------------------------------------------

v1 = rank68[
    (rank68["spike_score"] >= 170)
    &
    (rank68["spread"] <= 51)
    &
    (rank68["total_score"].between(99, 139))
]

# --------------------------------------------------
# V2
# --------------------------------------------------

v2 = rank68[
    (rank68["spike_score"] >= 120)
    &
    (rank68["spread"] <= 50)
    &
    (rank68["total_score"] >= 105)
    &
    (rank68["avg_odds"] <= 15)
]

# --------------------------------------------------
# Endast vinnare
# --------------------------------------------------

v1_winners = set(
    v1[v1["won"] == 1][
        ["date", "race_no", "horse"]
    ].apply(tuple, axis=1)
)

v2_winners = set(
    v2[v2["won"] == 1][
        ["date", "race_no", "horse"]
    ].apply(tuple, axis=1)
)

common = v1_winners & v2_winners
only_v1 = v1_winners - v2_winners
only_v2 = v2_winners - v1_winners
union = v1_winners | v2_winners

print("=" * 80)
print("BADGE V1 VS V2")
print("=" * 80)

print()
print("V1 vinnare:", len(v1_winners))
print("V2 vinnare:", len(v2_winners))

print()
print("Gemensamma:", len(common))
print("Endast V1:", len(only_v1))
print("Endast V2:", len(only_v2))

print()
print("Totalt unika vinnare:", len(union))

print()
print("=" * 80)
print("NYA VINNARE SOM V2 HITTAR")
print("=" * 80)

if len(only_v2):

    only_v2_df = v2[
        (v2["won"] == 1)
    ].copy()

    only_v2_df = only_v2_df[
        only_v2_df[
            ["date", "race_no", "horse"]
        ].apply(tuple, axis=1).isin(only_v2)
    ]

    print(
        only_v2_df[
            [
                "date",
                "race_no",
                "horse",
                "model_rank",
                "total_score",
                "spike_score",
                "spread",
                "avg_odds"
            ]
        ]
        .sort_values("spike_score", ascending=False)
        .to_string(index=False)
    )
import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

# --------------------------------------------------
# Spike
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
# V1
# --------------------------------------------------

v1 = df[
    (df["model_rank"].between(6,8))
    &
    (df["spike_score"] >= 170)
    &
    (df["spread"] <= 51)
    &
    (df["total_score"].between(99,139))
]

# --------------------------------------------------
# V2 BAS
# --------------------------------------------------

v2_base = df[
    (df["model_rank"].between(6,8))
    &
    (df["spike_score"] >= 120)
    &
    (df["spread"] <= 50)
    &
    (df["total_score"] >= 105)
    &
    (df["avg_odds"] <= 15)
]

# --------------------------------------------------
# V2 STRONG
# --------------------------------------------------

v2_strong = v2_base[
    (v2_base["post"] <= 4)
    |
    (v2_base["latest_start_score"] >= 10)
    |
    (v2_base["form_score"] >= 35)
]

# --------------------------------------------------
# Kombinera
# --------------------------------------------------

v1_keys = set(
    v1[
        ["date","race_no","horse"]
    ].apply(tuple, axis=1)
)

base_keys = set(
    v2_base[
        ["date","race_no","horse"]
    ].apply(tuple, axis=1)
)

strong_keys = set(
    v2_strong[
        ["date","race_no","horse"]
    ].apply(tuple, axis=1)
)

combined_base = v1_keys | base_keys
combined_strong = v1_keys | strong_keys

df["key"] = df[
    ["date","race_no","horse"]
].apply(tuple, axis=1)

base_df = df[
    df["key"].isin(combined_base)
]

strong_df = df[
    df["key"].isin(combined_strong)
]

print("="*80)
print("V1 + V2 BAS")
print("="*80)

print("Kandidater:", len(base_df))
print("Vinnare:", int(base_df["won"].sum()))
print(
    "Träff%:",
    round(base_df["won"].mean()*100,1)
)

print()

print("="*80)
print("V1 + V2 STRONG")
print("="*80)

print("Kandidater:", len(strong_df))
print("Vinnare:", int(strong_df["won"].sum()))
print(
    "Träff%:",
    round(strong_df["won"].mean()*100,1)
)

print()

print("="*80)
print("FÖRBÄTTRING")
print("="*80)

print(
    "Borttagna kandidater:",
    len(base_df) - len(strong_df)
)

print(
    "Tappade vinnare:",
    int(base_df["won"].sum())
    -
    int(strong_df["won"].sum())
)

print()

print("="*80)
print("UNIKA RANK 6-8 VINNARE")
print("="*80)

rank68 = df[
    (df["model_rank"].between(6,8))
    &
    (df["won"] == 1)
]

print(
    "V1 + V2 BAS:",
    len(
        set(
            rank68[
                rank68["key"].isin(combined_base)
            ]["key"]
        )
    )
)

print(
    "V1 + V2 STRONG:",
    len(
        set(
            rank68[
                rank68["key"].isin(combined_strong)
            ]["key"]
        )
    )
)
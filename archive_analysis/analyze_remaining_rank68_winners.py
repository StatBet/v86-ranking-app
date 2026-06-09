import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

# =====================================================
# V1
# =====================================================

v1 = df[
    (df["model_rank"].between(6,8))
    & (df["spike_score"] >= 170)
    & (df["spread"] <= 51)
    & (df["total_score"].between(99,139))
]

# =====================================================
# V2 Strong B
# =====================================================

v2 = df[
    (df["model_rank"].between(6,8))
    & (df["spike_score"] >= 120)
    & (df["spread"] <= 50)
    & (df["total_score"] >= 105)
    & (df["avg_odds"] <= 15)
    & (
        (df["post"] <= 5)
        | (df["latest_start_score"] >= 7)
        | (df["form_score"] >= 35)
    )
]

# =====================================================
# V3
# =====================================================

v3 = df[
    (df["model_rank"].between(6,8))
    & (df["latest_start_score"].between(7,10))
    & (df["form_score"].between(19,40))
    & (df["driver_score"] >= 8)
    & (df["avg_odds"] <= 15)
    & (df["win_percent"] >= 10)
]

# =====================================================
# UNION
# =====================================================

caught = pd.concat([v1,v2,v3])

caught = caught.drop_duplicates(
    subset=["date","race_no","horse"]
)

caught_ids = set(
    caught["date"].astype(str)
    + "_"
    + caught["race_no"].astype(str)
)

# =====================================================
# ALLA RANK 6-8 VINNARE
# =====================================================

rank68_winners = df[
    (df["model_rank"].between(6,8))
    & (df["won"] == 1)
].copy()

rank68_winners["id"] = (
    rank68_winners["date"].astype(str)
    + "_"
    + rank68_winners["race_no"].astype(str)
)

remaining = rank68_winners[
    ~rank68_winners["id"].isin(caught_ids)
]

print("=" * 80)
print("MISSADE RANK 6-8 VINNARE")
print("=" * 80)

print()
print("Totala rank 6-8-vinnare:", len(rank68_winners))
print("Fångade:", len(rank68_winners)-len(remaining))
print("Missade:", len(remaining))

print()

print("=" * 80)
print("MISSADE VINNARE - MEDEL")
print("=" * 80)

cols = [
    "total_score",
    "spike_score",
    "spread",
    "speed_score",
    "driver_score",
    "form_score",
    "latest_start_score",
    "win_percent",
    "place_percent",
    "avg_odds",
    "percent",
    "post"
]

for c in cols:
    if c in remaining.columns:
        print(
            f"{c:<20}",
            round(remaining[c].mean(),2)
        )

print()

print("=" * 80)
print("MISSADE VINNARE")
print("=" * 80)

print(
    remaining[
        [
            "date",
            "race_no",
            "horse",
            "model_rank",
            "total_score",
            "spike_score",
            "spread",
            "speed_score",
            "driver_score",
            "form_score",
            "latest_start_score",
            "win_percent",
            "place_percent",
            "avg_odds",
            "percent",
            "post"
        ]
    ]
    .sort_values(["date","race_no"])
    .to_string(index=False)
)
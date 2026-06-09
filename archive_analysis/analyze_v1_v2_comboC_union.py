import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

# -------------------------
# V1
# -------------------------

v1 = df[
    (df["model_rank"].between(6,8))
    & (df["spike_score"] >= 170)
    & (df["spread"] <= 51)
    & (df["total_score"].between(99,139))
]

# -------------------------
# V2 STRONG B
# -------------------------

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

# -------------------------
# COMBO C
# -------------------------

c = df[
    (df["model_rank"].between(6,8))
    & (df["latest_start_score"].between(7,10))
    & (df["form_score"].between(19,40))
    & (df["driver_score"] >= 8)
    & (df["avg_odds"] <= 15)
    & (df["win_percent"] >= 10)
]

# -------------------------
# UNION
# -------------------------

union = pd.concat([v1, v2, c])

union = union.drop_duplicates(
    subset=["date","race_no","horse"]
)

print("="*80)
print("V1 + V2 STRONG B + COMBO C")
print("="*80)

print()
print("Kandidater:", len(union))
print("Vinnare:", int(union["won"].sum()))
print(
    "Träff%:",
    round(union["won"].mean()*100,1)
)

print()

rank68_winners = df[
    (df["model_rank"].between(6,8))
    & (df["won"] == 1)
]

caught = union[
    union["won"] == 1
]

print(
    "Rank 6-8-vinnare fångade:",
    len(caught),
    "/",
    len(rank68_winners)
)

print(
    "Andel:",
    round(
        len(caught)
        /
        len(rank68_winners)
        * 100,
        1
    ),
    "%"
)

print()
print("="*80)
print("VINNARE")
print("="*80)

print(
    caught[
        [
            "date",
            "race_no",
            "horse",
            "model_rank"
        ]
    ].sort_values(
        ["date","race_no"]
    ).to_string(index=False)
)
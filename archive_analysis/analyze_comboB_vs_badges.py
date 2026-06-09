import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

# COMBO B

comboB = df[
    (df["model_rank"].between(6,8))
    & (df["latest_start_score"].between(7,10))
    & (df["form_score"].between(19,40))
    & (df["driver_score"] >= 8)
    & (df["avg_odds"] <= 15)
    & (df["win_percent"] >= 15)
]

# BADGE V1

v1 = df[
    (df["model_rank"].between(6,8))
    & (df["spike_score"] >= 170)
    & (df["spread"] <= 50)
    & (df["total_score"].between(99,140))
]

# BADGE V2 Variant B

v2 = df[
    (df["model_rank"].between(6,8))
    & (df["spike_score"] >= 120)
    & (df["spread"] <= 50)
    & (df["avg_odds"] <= 15)
    & (
        (df["post"] <= 5)
        | (df["latest_start_score"] >= 7)
        | (df["form_score"] >= 35)
    )
]

combo_winners = comboB[comboB["won"] == 1]

combo_ids = set(
    combo_winners["date"].astype(str)
    + "_"
    + combo_winners["race_no"].astype(str)
)

v1_ids = set(
    (
        v1[v1["won"] == 1]["date"].astype(str)
        + "_"
        + v1[v1["won"] == 1]["race_no"].astype(str)
    )
)

v2_ids = set(
    (
        v2[v2["won"] == 1]["date"].astype(str)
        + "_"
        + v2[v2["won"] == 1]["race_no"].astype(str)
    )
)

new_ids = combo_ids - v1_ids - v2_ids

print("="*80)
print("COMBO B - NYA VINNARE?")
print("="*80)

new_winners = combo_winners[
    (
        combo_winners["date"].astype(str)
        + "_"
        + combo_winners["race_no"].astype(str)
    ).isin(new_ids)
]

print()
print("Nya vinnare:", len(new_winners))

if len(new_winners):
    print(
        new_winners[
            [
                "date",
                "race_no",
                "horse",
                "model_rank"
            ]
        ].to_string(index=False)
    )
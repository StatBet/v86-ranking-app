import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

# V1

v1 = df[
    (df["model_rank"].between(6,8))
    & (df["spike_score"] >= 170)
    & (df["spread"] <= 51)
    & (df["total_score"].between(99,139))
]

# V2

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

# V3

v3 = df[
    (df["model_rank"].between(6,8))
    & (df["latest_start_score"].between(7,10))
    & (df["form_score"].between(19,40))
    & (df["driver_score"] >= 8)
    & (df["avg_odds"] <= 15)
    & (df["win_percent"] >= 10)
]

union = pd.concat([v1,v2,v3]).drop_duplicates(
    subset=["date","race_no","horse"]
)

union_ids = set(
    union["date"].astype(str)
    + "_"
    + union["race_no"].astype(str)
)

speed = df[
    (df["model_rank"].between(6,8))
    & (df["speed_score"] >= 15)
    & (df["post"].between(1,6))
    & (df["won"] == 1)
].copy()

speed["id"] = (
    speed["date"].astype(str)
    + "_"
    + speed["race_no"].astype(str)
)

new_winners = speed[
    ~speed["id"].isin(union_ids)
]

print("="*80)
print("NYA VINNARE")
print("="*80)

print()
print("Antal:", len(new_winners))

if len(new_winners):

    print(
        new_winners[
            [
                "date",
                "race_no",
                "horse",
                "speed_score",
                "post",
                "avg_odds",
                "percent"
            ]
        ].to_string(index=False)
    )
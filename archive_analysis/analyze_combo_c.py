import pandas as pd

df = pd.read_csv("ml_dataset.csv")

combo = df[
    (df["model_rank"].between(6,15))
    & (df["latest_start_score"].between(7,10))
    & (df["form_score"].between(19,40))
    & (df["driver_score"] >= 8)
    & (df["win_percent"] >= 20)
    & (df["total_score"] >= 110)
]

print("="*80)
print("COMBO C")
print("="*80)

for low, high in [(6,8),(9,15)]:

    part = combo[
        combo["model_rank"].between(low,high)
    ]

    print()
    print(f"Rank {low}-{high}")
    print("-"*40)
    print("Kandidater:", len(part))
    print("Vinnare:", int(part["won"].sum()))

    if len(part):
        print(
            "Träff%",
            round(part["won"].mean()*100,1)
        )

print()
print("="*80)
print("VINNARE")
print("="*80)

print(
    combo[
        [
            "date",
            "race_no",
            "horse",
            "model_rank",
            "total_score",
            "speed_score",
            "driver_score",
            "win_percent",
            "form_score",
            "latest_start_score",
            "avg_odds"
        ]
    ]
    [combo["won"] == 1]
    .to_string(index=False)
)
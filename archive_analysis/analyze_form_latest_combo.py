import pandas as pd

df = pd.read_csv("ml_dataset.csv")

combo = df[
    (df["latest_start_score"] >= 7)
    & (df["latest_start_score"] <= 10)
    & (df["form_score"] >= 19)
    & (df["form_score"] <= 40)
]

winners = combo[combo["won"] == 1]

print("=" * 80)
print("FORM + LATEST")
print("=" * 80)

print()
print("Kandidater:", len(combo))
print("Vinnare:", len(winners))

if len(combo):
    print(
        "Träff%:",
        round(len(winners) / len(combo) * 100, 1)
    )

print()
print("=" * 80)
print("VINNARE")
print("=" * 80)

print(
    winners[
        [
            "date",
            "race_no",
            "horse",
            "model_rank",
            "percent",
            "win_percent",
            "place_percent",
            "form_score",
            "latest_start_score",
            "avg_odds",
            "post"
        ]
    ]
    .sort_values(
        ["model_rank", "percent"]
    )
    .to_string(index=False)
)
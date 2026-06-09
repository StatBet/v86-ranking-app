import pandas as pd

df = pd.read_csv("ml_dataset.csv")

skrall = df[
    (df["won"] == 1)
    & (df["percent"] <= 14)
]

combo = skrall[
    (skrall["latest_start_score"] >= 7)
    & (skrall["latest_start_score"] <= 10)
    & (skrall["form_score"] >= 19)
    & (skrall["form_score"] <= 40)
]

print("=" * 80)
print("SKRÄLLVINNARE SOM MATCHAR FORM/LATEST")
print("=" * 80)

print()
print("Totala skrällvinnare:", len(skrall))
print("Matchar kombon:", len(combo))

if len(skrall):
    print(
        "Andel:",
        round(
            len(combo) / len(skrall) * 100,
            1
        ),
        "%"
    )

print()
print(
    combo[
        [
            "date",
            "race_no",
            "horse",
            "percent",
            "model_rank",
            "form_score",
            "latest_start_score",
            "avg_odds",
            "post",
            "win_percent",
            "place_percent"
        ]
    ]
    .sort_values(
        ["percent", "model_rank"]
    )
    .to_string(index=False)
)
import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

winners = df[df["won"] == 1]

print("=" * 80)
print("20 HÖGSTA ODDSVINNARNA")
print("=" * 80)

print(
    winners.sort_values(
        "avg_odds",
        ascending=False
    )[
        [
            "date",
            "race_no",
            "horse",
            "model_rank",
            "avg_odds",
            "win_percent",
            "place_percent",
            "form_score"
        ]
    ]
    .head(20)
    .to_string(index=False)
)
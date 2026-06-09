import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[
    df["model_rank"].between(6,8)
]

filter2 = (
    (rank68["spike_score"] <= 120)
    & (rank68["driver_score"] == 0)
    & (rank68["latest_start_score"] <= 3)
    & (rank68["form_score"] <= 20)
)

loser_filter = rank68[
    filter2
    | (rank68["spike_score"] <= 50)
]

winners = loser_filter[
    loser_filter["won"] == 1
]

print("=" * 80)
print("LOSER FILTER A - VINNARE SOM FÖRSVINNER")
print("=" * 80)

print()
print("Kandidater:", len(loser_filter))
print("Vinnare:", len(winners))
print()

print(
    winners[
        [
            "date",
            "race_no",
            "horse",
            "model_rank",
            "total_score",
            "spike_score",
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
    .sort_values(["date", "race_no"])
    .to_string(index=False)
)
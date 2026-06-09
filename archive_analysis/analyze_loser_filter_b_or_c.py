import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[df["model_rank"].between(6, 8)]

loser_b = (
    (
        (rank68["spike_score"] <= 120)
        & (rank68["driver_score"] == 0)
        & (rank68["latest_start_score"] <= 3)
        & (rank68["form_score"] <= 20)
        & (rank68["avg_odds"] > 15)
    )
    | (rank68["spike_score"] <= 50)
)

loser_c = (
    (rank68["percent"] <= 4)
    & (rank68["spike_score"] <= 100)
)

combo = rank68[loser_b | loser_c]

print("=" * 80)
print("LOSER FILTER B OR C")
print("=" * 80)

print()
print("Kandidater:", len(combo))
print("Vinnare:", int(combo["won"].sum()))

if len(combo):
    print("Träff%:", round(combo["won"].mean() * 100, 1))

print()
print("=" * 80)
print("VINNARE SOM FÖRSVINNER")
print("=" * 80)

print(
    combo[combo["won"] == 1][
        [
            "date",
            "race_no",
            "horse",
            "model_rank",
            "percent",
            "total_score",
            "spike_score",
            "speed_score",
            "driver_score",
            "form_score",
            "latest_start_score",
            "win_percent",
            "place_percent",
            "avg_odds",
            "post",
        ]
    ]
    .sort_values(["date", "race_no"])
    .to_string(index=False)
)
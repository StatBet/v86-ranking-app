import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[df["model_rank"].between(6,8)]

filter_b = (
    (
        (rank68["spike_score"] <= 120)
        & (rank68["driver_score"] == 0)
        & (rank68["latest_start_score"] <= 3)
        & (rank68["form_score"] <= 20)
        & (rank68["avg_odds"] > 15)
    )
    |
    (rank68["spike_score"] <= 50)
)

result = rank68[filter_b]

print("=" * 80)
print("LOSER FILTER B")
print("=" * 80)

print()
print("Kandidater:", len(result))
print("Vinnare:", int(result["won"].sum()))

if len(result):
    print(
        "Träff%:",
        round(result["won"].mean() * 100, 1)
    )

print()
print("=" * 80)
print("VINNARE")
print("=" * 80)

print(
    result[result["won"] == 1][
        [
            "date",
            "race_no",
            "horse",
            "spike_score",
            "driver_score",
            "form_score",
            "latest_start_score",
            "avg_odds"
        ]
    ].to_string(index=False)
)
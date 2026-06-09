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

base = rank68[loser_b]

groups = [
    ("Speed <= 12", base["speed_score"] <= 12),
    ("Speed 13-14", base["speed_score"].between(13, 14)),
    ("Speed >= 15", base["speed_score"] >= 15),
    ("Speed >= 20", base["speed_score"] >= 20),
]

print("=" * 80)
print("LOSER B - SPEED SPLIT")
print("=" * 80)

print()
print("Loser B totalt")
print("-" * 40)
print("Kandidater:", len(base))
print("Vinnare:", int(base["won"].sum()))
print("Träff%:", round(base["won"].mean() * 100, 1) if len(base) else 0)

for name, mask in groups:
    subset = base[mask]

    print()
    print(name)
    print("-" * 40)
    print("Kandidater:", len(subset))
    print("Vinnare:", int(subset["won"].sum()))
    print("Träff%:", round(subset["won"].mean() * 100, 1) if len(subset) else 0)

print()
print("=" * 80)
print("VINNARE I LOSER B")
print("=" * 80)

print(
    base[base["won"] == 1][
        [
            "date",
            "race_no",
            "horse",
            "model_rank",
            "spike_score",
            "speed_score",
            "driver_score",
            "form_score",
            "latest_start_score",
            "avg_odds",
            "percent",
            "post",
        ]
    ]
    .sort_values("speed_score", ascending=False)
    .to_string(index=False)
)
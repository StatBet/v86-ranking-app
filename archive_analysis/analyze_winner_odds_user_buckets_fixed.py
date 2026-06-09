import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

winners = df[df["won"] == 1].copy()

groups = [
    ("0-30", 0, 30),
    ("31-49", 31, 49),
    ("50-69", 50, 69),
    ("70-99", 70, 99),
    ("100+", 100, 9999),
]

print("=" * 80)
print("ALLA VINNARE - AVG_ODDS FIXADE BUCKETS")
print("=" * 80)

total = len(winners)

print("Totalt vinnare:", total)

for name, low, high in groups:
    subset = winners[
        (winners["avg_odds"] >= low)
        &
        (winners["avg_odds"] <= high)
    ]

    print()
    print(name)
    print("-" * 40)
    print("Vinnare:", len(subset))
    print("Andel:", round(len(subset) / total * 100, 1), "%")

print()
print("=" * 80)
print("TOPP 30 HÖGSTA AVG_ODDS-VINNARE")
print("=" * 80)

print(
    winners.sort_values("avg_odds", ascending=False)[
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
    ].head(30).to_string(index=False)
)
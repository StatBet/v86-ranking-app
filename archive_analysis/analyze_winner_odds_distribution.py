import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

winners = df[df["won"] == 1].copy()

print("=" * 80)
print("VINNARE PER ODDSGRUPP")
print("=" * 80)

groups = [
    ("0-30", 0, 30),
    ("31-49", 31, 49),
    ("50-69", 50, 69),
    ("70-99", 70, 99),
    ("100+", 100, 9999)
]

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

print()
print("=" * 80)
print("SNITTODDS")
print("=" * 80)

print(round(winners["avg_odds"].mean(), 2))
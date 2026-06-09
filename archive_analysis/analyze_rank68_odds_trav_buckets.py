import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

winners = df[
    (df["won"] == 1)
    &
    (df["model_rank"].between(6,8))
].copy()

groups = [
    ("0-19", 0, 19.99),
    ("20-29", 20, 29.99),
    ("30-49", 30, 49.99),
    ("50-69", 50, 69.99),
    ("70-99", 70, 99.99),
    ("100+", 100, 9999)
]

print("=" * 80)
print("RANK 6-8 VINNARE PER ODDSGRUPP")
print("=" * 80)

total = len(winners)

for name, low, high in groups:

    subset = winners[
        (winners["avg_odds"] >= low)
        &
        (winners["avg_odds"] <= high)
    ]

    count = len(subset)

    pct = round(count / total * 100, 1)

    print()
    print(name)
    print("-" * 40)
    print("Vinnare:", count)
    print("Andel:", pct, "%")
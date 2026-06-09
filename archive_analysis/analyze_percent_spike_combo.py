import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[df["model_rank"].between(6,8)]

tests = [
    ("Spel<=4 + Spike<=100", 4, 100),
    ("Spel<=4 + Spike<=120", 4, 120),
    ("Spel<=5 + Spike<=120", 5, 120),
    ("Spel<=9 + Spike<=120", 9, 120),
]

print("="*80)
print("SPEL% + SPIKE")
print("="*80)

for name, pct, spike in tests:

    subset = rank68[
        (rank68["percent"] <= pct)
        &
        (rank68["spike_score"] <= spike)
    ]

    winners = int(subset["won"].sum())

    print()
    print(name)
    print("-"*40)
    print("Kandidater:", len(subset))
    print("Vinnare:", winners)

    if len(subset):
        print(
            "Träff%",
            round(
                winners / len(subset) * 100,
                1
            )
        )
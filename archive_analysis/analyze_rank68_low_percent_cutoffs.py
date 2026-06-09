import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[df["model_rank"].between(6,8)]

print("="*80)
print("RANK 6-8 - LÅG SPEL%")
print("="*80)

for cutoff in [2,4,5,7,9,10]:

    subset = rank68[
        rank68["percent"] <= cutoff
    ]

    winners = int(subset["won"].sum())

    print()
    print(f"Spel% <= {cutoff}")
    print("-"*40)
    print("Kandidater:", len(subset))
    print("Vinnare:", winners)

    if len(rank68[rank68["won"]==1]):
        print(
            "Andel vinnare som försvinner:",
            round(
                winners /
                len(rank68[rank68["won"]==1])
                * 100,
                1
            ),
            "%"
        )
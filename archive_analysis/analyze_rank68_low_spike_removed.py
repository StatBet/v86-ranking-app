import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[
    df["model_rank"].between(6,8)
]

total_winners = int(rank68["won"].sum())

print("=" * 80)
print("OM VI FILTRERAR BORT LÅGA SPIKE")
print("=" * 80)

for cutoff in [40,50,60,70,80,90,100,110,120,130,140]:

    removed = rank68[
        rank68["spike_score"] <= cutoff
    ]

    removed_winners = int(
        removed["won"].sum()
    )

    print()
    print(f"Ta bort spike <= {cutoff}")
    print("-"*40)

    print(
        "Borttagna kandidater:",
        len(removed)
    )

    print(
        "Borttagna vinnare:",
        removed_winners
    )

    print(
        "Andel vinnare som försvinner:",
        round(
            removed_winners
            /
            total_winners
            * 100,
            1
        ),
        "%"
    )
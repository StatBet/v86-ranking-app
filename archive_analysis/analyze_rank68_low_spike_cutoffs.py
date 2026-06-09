import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[
    df["model_rank"].between(6,8)
]

print("=" * 80)
print("RANK 6-8 - LÅGA SPIKEVÄRDEN")
print("=" * 80)

for cutoff in [40,50,60,70,80,90,100,110,120,130,140]:

    subset = rank68[
        rank68["spike_score"] <= cutoff
    ]

    winners = int(subset["won"].sum())

    print()
    print(f"Spike <= {cutoff}")
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
import pandas as pd

df = pd.read_csv("ml_dataset.csv")

rank1 = df[df["model_rank"] == 1].copy()

rank1 = rank1.sort_values(
    "total_score",
    ascending=False
)

for n in [25, 50, 100, 200]:

    sample = rank1.head(n)

    print("=" * 60)
    print(f"TOPP {n} TOTAL_SCORE")
    print("=" * 60)

    print("Hästar:", len(sample))
    print("Vinnare:", sample["won"].sum())
    print(
        "Träff%:",
        round(sample["won"].mean() * 100, 1)
    )
    print()
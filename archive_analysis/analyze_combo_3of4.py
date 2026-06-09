import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank = df[df["model_rank"].between(6,15)].copy()

rank["hits"] = (
    rank["latest_start_score"].between(7,10).astype(int)
    + rank["form_score"].between(19,40).astype(int)
    + (rank["driver_score"] >= 8).astype(int)
    + (rank["win_percent"] >= 20).astype(int)
)

combo = rank[rank["hits"] >= 3]

print("="*80)
print("3 AV 4")
print("="*80)

for low, high in [(6,8),(9,15)]:

    part = combo[
        combo["model_rank"].between(low,high)
    ]

    print()
    print(f"Rank {low}-{high}")
    print("-"*40)
    print("Kandidater:", len(part))
    print("Vinnare:", int(part["won"].sum()))

    if len(part):
        print(
            "Träff%",
            round(part["won"].mean()*100,1)
        )
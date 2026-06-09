import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

for limit in [10, 14]:

    combo = df[
        (df["model_rank"].between(6,8))
        & (df["speed_score"] >= 15)
        & (df["percent"] <= limit)
    ]

    print("="*80)
    print(f"SPEED >=15 + SPEL% <= {limit}")
    print("="*80)

    print()
    print("Kandidater:", len(combo))
    print("Vinnare:", int(combo["won"].sum()))

    if len(combo):
        print(
            "Träff%",
            round(combo["won"].mean()*100,1)
        )
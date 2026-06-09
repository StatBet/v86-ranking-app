import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

for wp in [10,20]:

    combo = df[
        (df["model_rank"].between(6,15))
        & (df["latest_start_score"].between(7,10))
        & (df["form_score"].between(19,40))
        & (df["driver_score"] >= 8)
        & (df["win_percent"] >= wp)
    ]

    print()
    print("="*80)
    print(f"WIN% >= {wp}")
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
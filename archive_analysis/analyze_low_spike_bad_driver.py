import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[
    df["model_rank"].between(6,8)
]

bad = rank68[
    (rank68["spike_score"] <= 120)
    &
    (rank68["driver_score"] == 0)
]

print("="*80)
print("SPIKE <=120 + DRIVER 0")
print("="*80)

print()
print("Kandidater:", len(bad))
print("Vinnare:", int(bad["won"].sum()))

if len(bad):
    print(
        "Träff%",
        round(
            bad["won"].mean()*100,
            1
        )
    )
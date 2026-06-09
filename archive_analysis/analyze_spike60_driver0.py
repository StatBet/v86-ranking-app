import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[df["model_rank"].between(6,8)]

combo = rank68[
    (rank68["spike_score"] <= 60)
    & (rank68["driver_score"] == 0)
]

print("="*80)
print("SPIKE<=60 + DRIVER=0")
print("="*80)

print()
print("Kandidater:", len(combo))
print("Vinnare:", int(combo["won"].sum()))
print("Träff%:", round(combo["won"].mean()*100,1))
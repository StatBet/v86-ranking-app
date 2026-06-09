import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[df["model_rank"].between(6,8)]

f2 = (
    (rank68["spike_score"] <= 120)
    & (rank68["driver_score"] == 0)
    & (rank68["latest_start_score"] <= 3)
    & (rank68["form_score"] <= 20)
)

combo = rank68[
    f2 | (rank68["spike_score"] <= 50)
]

print("="*80)
print("FILTER2 OR SPIKE<=50")
print("="*80)

print()
print("Kandidater:", len(combo))
print("Vinnare:", int(combo["won"].sum()))
print("Träff%:", round(combo["won"].mean()*100,1))
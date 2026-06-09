import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[
    df["model_rank"].between(6,8)
]

f = rank68[
    (rank68["spike_score"] <= 120)
    & (rank68["driver_score"] == 0)
    & (rank68["latest_start_score"] <= 3)
]

print("="*80)
print("FILTER 1")
print("Spike <=120 + Driver=0 + Latest<=3")
print("="*80)

print()
print("Kandidater:", len(f))
print("Vinnare:", int(f["won"].sum()))

if len(f):
    print(
        "Träff%",
        round(f["won"].mean()*100,1)
    )
import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[
    df["model_rank"].between(6,8)
]

f = rank68[
    (rank68["spike_score"] <= 120)
    & (rank68["driver_score"] == 0)
    & (rank68["latest_start_score"] <= 3)
    & (rank68["form_score"] <= 20)
    & (rank68["win_percent"] <= 15)
]

print("="*80)
print("FILTER 3")
print("Spike <=120 + Driver=0 + Latest<=3 + Form<=20 + Win%<=15")
print("="*80)

print()
print("Kandidater:", len(f))
print("Vinnare:", int(f["won"].sum()))

if len(f):
    print(
        "Träff%",
        round(f["won"].mean()*100,1)
    )

print()
print("="*80)
print("VINNARE SOM HAMNAR I FILTRET")
print("="*80)

print(
    f[f["won"] == 1][
        [
            "date",
            "race_no",
            "horse",
            "total_score",
            "spike_score",
            "form_score",
            "latest_start_score",
            "win_percent",
            "avg_odds",
            "percent"
        ]
    ].to_string(index=False)
)